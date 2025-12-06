"""DataUpdateCoordinator for Clear Dark Sky."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from io import BytesIO

from PIL import Image
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.sun import get_astral_location
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CHART_KEY,
    DOMAIN,
    UPDATE_INTERVAL_MINUTES,
    CHART_URL_TEMPLATE,
    CLOUD_CLEAR_THRESHOLD,
)

_LOGGER = logging.getLogger(__name__)


class ClearDarkSkyCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Clear Dark Sky data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        self.chart_key = entry.data[CONF_CHART_KEY]
        self.latitude = entry.data.get(CONF_LATITUDE, hass.config.latitude)
        self.longitude = entry.data.get(CONF_LONGITUDE, hass.config.longitude)
        self.chart_url = CHART_URL_TEMPLATE.format(chart_key=self.chart_key)
        self._image_data: bytes | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.chart_key}",
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from Clear Dark Sky."""
        session = async_get_clientsession(self.hass)
        
        try:
            async with session.get(
                self.chart_url, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error fetching data: {response.status}")
                
                self._image_data = await response.read()
                
                # Parse the chart image
                data = await self.hass.async_add_executor_job(
                    self._parse_chart_image, self._image_data
                )
                
                # Calculate sun times
                sun_data = await self._get_sun_data()
                data.update(sun_data)
                
                return data
                
        except asyncio.TimeoutError as err:
            raise UpdateFailed(f"Timeout fetching data: {err}")
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")

    def _parse_chart_image(self, image_data: bytes) -> dict:
        """Parse the Clear Dark Sky chart image to extract forecast data."""
        try:
            img = Image.open(BytesIO(image_data))

            # Clear Dark Sky charts are GIF images with specific structure
            # Chart layout (rows from top to bottom):
            # Row 1: Cloud Cover (dark blue=clear, light blue=cloudy, white=overcast)
            # Row 2: Transparency (dark blue=excellent, white=poor)
            # Row 3: Seeing (dark blue=excellent, white=poor)
            # Row 4: Darkness (black=dark, blue=twilight, white=daylight)
            # Row 5: Wind (colors vary, darker=calmer)

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            width, height = img.size
            _LOGGER.debug("Chart image size: %dx%d", width, height)

            # Estimate row positions (percentages of image height)
            # These are approximate and may need adjustment based on chart version
            row_positions = {
                'cloud': int(height * 0.15),       # Cloud cover row
                'transparency': int(height * 0.23), # Transparency row
                'seeing': int(height * 0.31),       # Seeing row
                'darkness': int(height * 0.39),     # Darkness row
                'wind': int(height * 0.47),         # Wind row
            }
            _LOGGER.debug("Sampling row positions: %s", row_positions)

            # Sample every hour position across the chart
            hours_to_sample = min(48, width // 10)
            forecast_data = []

            for hour in range(hours_to_sample):
                x_pos = int((width * 0.1) + (width * 0.8 * hour / hours_to_sample))

                if x_pos < width:
                    hour_data = {'hour': hour}

                    # Sample each row
                    for row_name, row_y in row_positions.items():
                        if row_y < height:
                            pixel = img.getpixel((x_pos, row_y))
                            r, g, b = pixel[:3] if len(pixel) >= 3 else (pixel, pixel, pixel)

                            hour_data[f'{row_name}_rgb'] = (r, g, b)
                            hour_data[f'{row_name}_value'] = self._calculate_condition_value(
                                row_name, r, g, b
                            )

                            # Debug log first 3 hours for troubleshooting
                            if hour < 3:
                                _LOGGER.debug(
                                    "Hour %d, %s: RGB=(%d,%d,%d) -> Value=%.1f%%",
                                    hour, row_name, r, g, b, hour_data[f'{row_name}_value']
                                )

                    forecast_data.append(hour_data)
            
            # Calculate current conditions (first hour in forecast)
            current = forecast_data[0] if forecast_data else {}

            # Calculate averages and totals
            clear_hours = sum(1 for f in forecast_data if f.get('cloud_value', 100) < 30)

            avg_cloud = sum(f.get('cloud_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0
            avg_transparency = sum(f.get('transparency_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0
            avg_seeing = sum(f.get('seeing_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0
            avg_wind = sum(f.get('wind_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0

            # Log summary of current conditions
            _LOGGER.info(
                "Current conditions: Cloud=%.1f%%, Transparency=%.1f%%, Seeing=%.1f%%, Clear hours=%d/%d",
                current.get('cloud_value', 0),
                current.get('transparency_value', 0),
                current.get('seeing_value', 0),
                clear_hours,
                hours_to_sample
            )

            return {
                'forecast': forecast_data,
                'clear_hours_total': clear_hours,
                'current_cloud_cover': current.get('cloud_value', 0),
                'current_transparency': current.get('transparency_value', 0),
                'current_seeing': current.get('seeing_value', 0),
                'current_darkness': current.get('darkness_value', 0),
                'current_wind': current.get('wind_value', 0),
                'avg_cloud_cover': round(avg_cloud, 1),
                'avg_transparency': round(avg_transparency, 1),
                'avg_seeing': round(avg_seeing, 1),
                'avg_wind': round(avg_wind, 1),
                'last_updated': dt_util.utcnow(),
                'chart_url': self.chart_url,
            }
            
        except Exception as err:
            _LOGGER.error("Error parsing chart image: %s", err)
            return {
                'forecast': [],
                'clear_hours_total': 0,
                'current_cloud_cover': 0,
                'current_transparency': 0,
                'current_seeing': 0,
                'current_darkness': 0,
                'current_wind': 0,
                'avg_cloud_cover': 0,
                'avg_transparency': 0,
                'avg_seeing': 0,
                'avg_wind': 0,
                'last_updated': dt_util.utcnow(),
                'chart_url': self.chart_url,
            }
    
    def _calculate_condition_value(self, row_name: str, r: int, g: int, b: int) -> float:
        """Calculate condition value (0-100%) based on pixel color.

        Uses continuous/gradual mapping instead of discrete thresholds for more accurate readings.
        """
        brightness = (r + g + b) / 3

        if row_name == 'cloud':
            # Dark blue = 0% (clear), White = 100% (overcast)
            # Use a combination of brightness and blue saturation

            # Calculate how "blue" the color is vs how "white/gray" it is
            blue_saturation = b / max(1, (r + g + b))

            # Very white/bright = overcast
            if brightness > 220:
                return 95.0 + (brightness - 220) / 35 * 5  # 95-100%

            # High brightness with low blue = cloudy
            if brightness > 180:
                cloud_pct = 70 + (brightness - 180) / 40 * 25  # 70-95%
                return max(70.0, min(95.0, cloud_pct))

            # Medium brightness - check blue saturation
            if brightness > 140:
                # Less blue = more clouds
                if blue_saturation < 0.35:
                    return 50 + (180 - brightness) / 40 * 20  # 50-70%
                else:
                    return 30 + (180 - brightness) / 40 * 20  # 30-50%

            # Lower brightness - likely clear if blue-tinted
            if blue_saturation > 0.4:
                # Dark blue = clear sky
                return max(0.0, 20 - (140 - brightness) / 14)  # 0-20%
            else:
                # Dark but not blue = partially cloudy
                return 25 + (140 - brightness) / 14 * 15  # 25-40%

        elif row_name == 'transparency':
            # Dark blue = 100% (excellent), White = 0% (poor)
            # Transparency indicates atmospheric clarity

            # Calculate blue saturation
            blue_saturation = b / max(1, (r + g + b))

            # Very dark blue = excellent transparency
            if brightness < 100 and blue_saturation > 0.4:
                return 90 + (100 - brightness) / 100 * 10  # 90-100%

            # Dark blue = good transparency
            if brightness < 140 and blue_saturation > 0.38:
                return 70 + (140 - brightness) / 40 * 20  # 70-90%

            # Medium blue = fair transparency
            if brightness < 180:
                if blue_saturation > 0.35:
                    return 50 + (180 - brightness) / 40 * 20  # 50-70%
                else:
                    return 30 + (180 - brightness) / 40 * 20  # 30-50%

            # Light/white = poor transparency
            return max(0.0, 30 - (brightness - 180) / 75 * 30)  # 0-30%

        elif row_name == 'seeing':
            # Dark blue = 100% (excellent), White = 0% (poor)
            # Seeing indicates atmospheric steadiness
            # Use same logic as transparency

            blue_saturation = b / max(1, (r + g + b))

            if brightness < 100 and blue_saturation > 0.4:
                return 90 + (100 - brightness) / 100 * 10

            if brightness < 140 and blue_saturation > 0.38:
                return 70 + (140 - brightness) / 40 * 20

            if brightness < 180:
                if blue_saturation > 0.35:
                    return 50 + (180 - brightness) / 40 * 20
                else:
                    return 30 + (180 - brightness) / 40 * 20

            return max(0.0, 30 - (brightness - 180) / 75 * 30)

        elif row_name == 'darkness':
            # Black = 100% (dark), White = 0% (daylight)
            # Simple inverse brightness mapping

            if brightness < 30:
                return 100.0
            elif brightness < 100:
                return 100 - (brightness - 30) / 70 * 20  # 100-80%
            elif brightness < 180:
                return 80 - (brightness - 100) / 80 * 60  # 80-20%
            else:
                return max(0.0, 20 - (brightness - 180) / 75 * 20)  # 20-0%

        elif row_name == 'wind':
            # Darker colors = calmer, lighter = windier
            # Use continuous mapping based on brightness

            if brightness < 60:
                return 95.0 + (60 - brightness) / 60 * 5  # 95-100%
            elif brightness < 120:
                return 70 + (120 - brightness) / 60 * 25  # 70-95%
            elif brightness < 180:
                return 40 + (180 - brightness) / 60 * 30  # 40-70%
            elif brightness < 220:
                return 15 + (220 - brightness) / 40 * 25  # 15-40%
            else:
                return max(0.0, 15 - (brightness - 220) / 35 * 15)  # 0-15%

        return 50.0  # Default

    async def _get_sun_data(self) -> dict:
        """Calculate sun rise/set times and darkness periods."""
        try:
            location = get_astral_location(self.hass)
            now = dt_util.now()
            
            # Get today's sunset and next sunrise
            sunset = location.sunset(now, local=True)
            sunrise = location.sunrise(now + timedelta(days=1), local=True)
            
            # If sunset already passed, get tomorrow's
            if sunset < now:
                sunset = location.sunset(now + timedelta(days=1), local=True)
                sunrise = location.sunrise(now + timedelta(days=2), local=True)
            
            # Calculate astronomical twilight (sun 18° below horizon)
            # This is when true darkness begins for astronomy
            astronomical_dusk = sunset + timedelta(minutes=90)  # Approximate
            astronomical_dawn = sunrise - timedelta(minutes=90)  # Approximate
            
            darkness_hours = (astronomical_dawn - astronomical_dusk).total_seconds() / 3600
            
            return {
                'sunset': sunset,
                'sunrise': sunrise,
                'astronomical_dusk': astronomical_dusk,
                'astronomical_dawn': astronomical_dawn,
                'darkness_hours': darkness_hours,
            }
        except Exception as err:
            _LOGGER.error("Error calculating sun data: %s", err)
            return {
                'sunset': None,
                'sunrise': None,
                'astronomical_dusk': None,
                'astronomical_dawn': None,
                'darkness_hours': 0,
            }

    @property
    def image_data(self) -> bytes | None:
        """Return the raw chart image data."""
        return self._image_data