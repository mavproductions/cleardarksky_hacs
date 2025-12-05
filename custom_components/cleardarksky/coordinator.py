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
            
            # Estimate row positions (percentages of image height)
            # These are approximate and may need adjustment based on chart version
            row_positions = {
                'cloud': int(height * 0.15),       # Cloud cover row
                'transparency': int(height * 0.23), # Transparency row
                'seeing': int(height * 0.31),       # Seeing row
                'darkness': int(height * 0.39),     # Darkness row
                'wind': int(height * 0.47),         # Wind row
            }
            
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
                    
                    forecast_data.append(hour_data)
            
            # Calculate current conditions (first hour in forecast)
            current = forecast_data[0] if forecast_data else {}
            
            # Calculate averages and totals
            clear_hours = sum(1 for f in forecast_data if f.get('cloud_value', 100) < 30)
            
            avg_cloud = sum(f.get('cloud_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0
            avg_transparency = sum(f.get('transparency_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0
            avg_seeing = sum(f.get('seeing_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0
            avg_wind = sum(f.get('wind_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0
            
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
        """Calculate condition value (0-100%) based on pixel color."""
        if row_name == 'cloud':
            # Dark blue = 0% (clear), White = 100% (overcast)
            # Calculate based on brightness and blue dominance
            brightness = (r + g + b) / 3
            blue_dominance = b - ((r + g) / 2)
            
            # More white = more clouds
            if brightness > 200:  # Very white
                return 100.0
            elif brightness > 150:
                return 70.0
            elif blue_dominance > 30:  # Dark blue
                return 10.0
            elif blue_dominance > 0:  # Medium blue
                return 30.0
            else:
                return 50.0
                
        elif row_name == 'transparency':
            # Dark blue = 100% (excellent), White = 0% (poor)
            brightness = (r + g + b) / 3
            blue_dominance = b - ((r + g) / 2)
            
            if blue_dominance > 50:  # Very dark blue
                return 100.0
            elif blue_dominance > 20:
                return 75.0
            elif brightness < 150:
                return 50.0
            else:  # White/light
                return 20.0
                
        elif row_name == 'seeing':
            # Dark blue = 100% (excellent), White = 0% (poor)
            brightness = (r + g + b) / 3
            blue_dominance = b - ((r + g) / 2)
            
            if blue_dominance > 50:
                return 100.0
            elif blue_dominance > 20:
                return 75.0
            elif brightness < 150:
                return 50.0
            else:
                return 20.0
                
        elif row_name == 'darkness':
            # Black = 100% (dark), White = 0% (daylight)
            brightness = (r + g + b) / 3
            
            if brightness < 50:  # Very dark/black
                return 100.0
            elif brightness < 100:  # Dark blue
                return 75.0
            elif brightness < 150:  # Medium
                return 50.0
            else:  # Light/white
                return 10.0
                
        elif row_name == 'wind':
            # Darker colors = calmer, lighter = windier
            # This is approximate as wind uses varied colors
            brightness = (r + g + b) / 3
            
            if brightness < 80:  # Dark (calm)
                return 90.0
            elif brightness < 120:
                return 70.0
            elif brightness < 160:
                return 50.0
            elif brightness < 200:
                return 30.0
            else:  # Very light (windy)
                return 10.0
        
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