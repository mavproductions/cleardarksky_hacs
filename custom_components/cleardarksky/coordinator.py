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
from homeassistant.helpers import sun
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

# This will fire when the file is imported
_LOGGER.warning("=" * 80)
_LOGGER.warning("🔥 COORDINATOR.PY LOADED - VERSION 1.2.8 - LOGGING ACTIVE 🔥")
_LOGGER.warning("=" * 80)

# ClearDarkSky discrete color palettes (hex to RGB)
# Cloud Cover: 11 levels (0% to 100%)
CLOUD_COLORS = [
    ((0, 62, 126), 0),      # Clear
    ((19, 83, 147), 10),    # 10% covered
    ((38, 102, 166), 20),   # 20% covered
    ((78, 142, 206), 30),   # 30% covered
    ((98, 162, 226), 40),   # 40% covered
    ((118, 182, 246), 50),  # 50% covered
    ((153, 217, 217), 60),  # 60% covered
    ((173, 237, 237), 70),  # 70% covered
    ((193, 193, 193), 80),  # 80% covered
    ((233, 233, 233), 90),  # 90% covered
    ((250, 250, 250), 100), # Overcast
]

# Transparency: 6 levels (0% = too cloudy, 100% = transparent)
TRANSPARENCY_COLORS = [
    ((249, 249, 249), 0),   # Too cloudy to forecast
    ((199, 199, 199), 20),  # Poor
    ((149, 213, 213), 40),  # Below average
    ((99, 163, 227), 60),   # Average
    ((44, 108, 172), 80),   # Above average
    ((0, 63, 127), 100),    # Transparent (excellent)
]

# Seeing: 6 levels (0% = too cloudy, 100% = excellent)
SEEING_COLORS = [
    ((249, 249, 249), 0),   # Too cloudy to forecast
    ((199, 199, 199), 20),  # Bad 1/5
    ((149, 213, 213), 40),  # Poor 2/5
    ((99, 163, 227), 60),   # Average 3/5
    ((44, 108, 172), 80),   # Good 4/5
    ((0, 63, 127), 100),    # Excellent 5/5
]

# Darkness: 15 levels (magnitude scale -4 to 6.5)
# Mapped to 0-100% where 0% = daylight, 100% = darkest
DARKNESS_COLORS = [
    ((255, 255, 255), 0),    # -4 (daylight)
    ((255, 241, 216), 7),    # -3
    ((255, 227, 177), 14),   # -2
    ((255, 213, 138), 21),   # -1
    ((255, 198, 98), 29),    # 0
    ((255, 184, 59), 36),    # 1.0
    ((255, 170, 20), 43),    # 2.0 (sunset)
    ((0, 255, 255), 50),     # 3.0 (astronomical twilight)
    ((0, 203, 255), 57),     # 3.5
    ((0, 150, 255), 64),     # 4.0
    ((0, 100, 228), 71),     # 4.5
    ((0, 50, 202), 79),      # 5.0
    ((0, 0, 175), 86),       # 5.5
    ((0, 0, 66), 93),        # 6.0
    ((0, 0, 75), 100),       # 6.5 (darkest)
]


def _find_nearest_color(r: int, g: int, b: int, color_palette: list) -> float:
    """Find the nearest color in a discrete palette and return its value.

    Uses Euclidean distance in RGB space.
    """
    min_distance = float('inf')
    nearest_value = 50.0

    for (ref_r, ref_g, ref_b), value in color_palette:
        # Calculate Euclidean distance in RGB space
        distance = ((r - ref_r) ** 2 + (g - ref_g) ** 2 + (b - ref_b) ** 2) ** 0.5

        if distance < min_distance:
            min_distance = distance
            nearest_value = value

    return float(nearest_value)


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
        _LOGGER.warning("🔄 UPDATE STARTED - Fetching chart from: %s", self.chart_url)
        session = async_get_clientsession(self.hass)

        try:
            async with session.get(
                self.chart_url, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                _LOGGER.warning("📥 Response status: %s", response.status)
                if response.status != 200:
                    raise UpdateFailed(f"Error fetching data: {response.status}")

                self._image_data = await response.read()
                _LOGGER.warning("📊 Chart downloaded, size: %d bytes", len(self._image_data))

                # Parse the chart image
                _LOGGER.warning("🔍 Starting chart parsing...")
                data = await self.hass.async_add_executor_job(
                    self._parse_chart_image, self._image_data
                )
                _LOGGER.warning("✅ Chart parsing completed!")
                
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
        _LOGGER.warning("🎨 PARSE_CHART_IMAGE CALLED - Processing %d bytes", len(image_data))
        try:
            img = Image.open(BytesIO(image_data))
            _LOGGER.warning("🖼️  Image opened successfully")

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
            _LOGGER.warning("📐 Chart image size: %dx%d", width, height)

            # Row positions based on actual chart analysis
            # For 1270x276 chart: Cloud=83, Transparency=100, Seeing=116, Darkness=133
            row_positions = {
                'cloud': int(height * 0.30),       # Cloud cover row (~83px on 276px chart)
                'transparency': int(height * 0.36), # Transparency row (~100px)
                'seeing': int(height * 0.42),       # Seeing row (~116px)
                'darkness': int(height * 0.48),     # Darkness row (~133px)
                'wind': int(height * 0.54),         # Wind row (estimated)
            }
            _LOGGER.warning("📍 Sampling row positions (Y coordinates): %s", row_positions)
            _LOGGER.warning("⚠️  These percentages may need adjustment for your chart version")

            # Sample every hour position across the chart
            hours_to_sample = min(48, width // 10)
            forecast_data = []

            # ClearDarkSky charts: First data column at X=140 for 1270px chart (~11%)
            # Forecast data starts around 11% from left
            chart_start = width * 0.11  # Start at 11% where first column begins
            chart_width = width * 0.84   # Use 84% of width for forecast data

            for hour in range(hours_to_sample):
                x_pos = int(chart_start + (chart_width * hour / hours_to_sample))

                if x_pos < width:
                    hour_data = {'hour': hour}

                    # Sample each row
                    for row_name, row_y in row_positions.items():
                        if row_y < height:
                            pixel = img.getpixel((x_pos, row_y))
                            r, g, b = pixel[:3] if len(pixel) >= 3 else (pixel, pixel, pixel)

                            hour_data[f'{row_name}_rgb'] = (r, g, b)
                            value = self._calculate_condition_value(row_name, r, g, b)
                            hour_data[f'{row_name}_value'] = value

                            # Debug log first 3 hours for troubleshooting
                            if hour < 3:
                                brightness = (r + g + b) / 3
                                _LOGGER.warning(
                                    "🔢 Hour %d, %s at Y=%d, X=%d: RGB=(%d,%d,%d) brightness=%.1f -> Value=%.1f%%",
                                    hour, row_name, row_y, x_pos, r, g, b, brightness, value
                                )

                            # Warn if value is out of expected range
                            if value > 100 or value < 0:
                                _LOGGER.warning(
                                    "⚠️ Hour %d, %s: Value %.1f%% is out of range! RGB=(%d,%d,%d) at position Y=%d",
                                    hour, row_name, value, r, g, b, row_y
                                )

                    forecast_data.append(hour_data)
            
            # Calculate current conditions (first hour in forecast)
            current = forecast_data[0] if forecast_data else {}

            # Calculate averages and totals
            clear_hours = sum(1 for f in forecast_data if f.get('cloud_value', 100) < 30)

            avg_cloud = sum(f.get('cloud_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0
            avg_transparency = sum(f.get('transparency_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0
            avg_seeing = sum(f.get('seeing_value', 0) for f in forecast_data) / len(forecast_data) if forecast_data else 0

            # Log summary of current conditions
            _LOGGER.warning(
                "📊 Current conditions: Cloud=%.1f%%, Transparency=%.1f%%, Seeing=%.1f%%, Clear hours=%d/%d",
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
                'avg_cloud_cover': round(avg_cloud, 1),
                'avg_transparency': round(avg_transparency, 1),
                'avg_seeing': round(avg_seeing, 1),
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
                'avg_cloud_cover': 0,
                'avg_transparency': 0,
                'avg_seeing': 0,
                'last_updated': dt_util.utcnow(),
                'chart_url': self.chart_url,
            }
    
    def _calculate_condition_value(self, row_name: str, r: int, g: int, b: int) -> float:
        """Calculate condition value (0-100%) based on pixel color.

        Uses discrete color matching against ClearDarkSky's exact color palettes.
        """
        if row_name == 'cloud':
            return _find_nearest_color(r, g, b, CLOUD_COLORS)
        elif row_name == 'transparency':
            return _find_nearest_color(r, g, b, TRANSPARENCY_COLORS)
        elif row_name == 'seeing':
            return _find_nearest_color(r, g, b, SEEING_COLORS)
        elif row_name == 'darkness':
            return _find_nearest_color(r, g, b, DARKNESS_COLORS)
        elif row_name == 'wind':
            # Wind removed per user request - return neutral value
            return 50.0
        else:
            return 50.0  # Default for unknown rows

    async def _get_sun_data(self) -> dict:
        """Calculate sun rise/set times and darkness periods."""
        try:
            now = dt_util.now()

            # Get next sunset and sunrise using Home Assistant sun helpers
            next_sunset = sun.get_astral_event_next(
                self.hass, "sunset", dt_util.utcnow()
            )
            next_sunrise = sun.get_astral_event_next(
                self.hass, "sunrise", dt_util.utcnow()
            )

            # If we're before sunset today, use today's sunset
            # Otherwise use tomorrow's
            if next_sunset and next_sunrise:
                # Approximate astronomical twilight (sun 18° below horizon)
                # Civil twilight is ~30 min, nautical ~60 min, astronomical ~90 min after sunset
                astronomical_dusk = next_sunset + timedelta(minutes=90)
                astronomical_dawn = next_sunrise - timedelta(minutes=90)

                # Calculate darkness hours
                if astronomical_dawn > astronomical_dusk:
                    darkness_hours = (astronomical_dawn - astronomical_dusk).total_seconds() / 3600
                else:
                    # Handle case where it's already past dusk
                    darkness_hours = 8.0  # Default reasonable value

                return {
                    'sunset': next_sunset,
                    'sunrise': next_sunrise,
                    'astronomical_dusk': astronomical_dusk,
                    'astronomical_dawn': astronomical_dawn,
                    'darkness_hours': max(0, darkness_hours),
                }
            else:
                raise ValueError("Could not calculate sun times")

        except Exception as err:
            _LOGGER.error("Error calculating sun data: %s", err)
            _LOGGER.debug("Latitude: %s, Longitude: %s", self.latitude, self.longitude)
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