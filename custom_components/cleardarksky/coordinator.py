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
            # The chart has colored blocks representing different conditions
            # We'll analyze the pixels to determine conditions
            
            # Chart layout (approximate pixel positions):
            # - Cloud cover row
            # - Transparency row  
            # - Seeing row
            # - Darkness row
            # - Wind row
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            width, height = img.size
            
            # Estimate hourly forecast positions
            # Clear Dark Sky typically shows ~48 hours across the width
            forecast_data = []
            
            # Sample the cloud cover row (typically around row 60-80)
            cloud_row_y = int(height * 0.15)  # Approximate position
            
            # Sample every ~hour position across the chart
            hours_to_sample = min(48, width // 10)  # Adjust based on chart width
            
            for hour in range(hours_to_sample):
                x_pos = int((width * 0.1) + (width * 0.8 * hour / hours_to_sample))
                
                if x_pos < width:
                    pixel = img.getpixel((x_pos, cloud_row_y))
                    
                    # Analyze pixel color to determine cloud cover
                    # Dark blue = clear, light blue = some clouds, white = overcast
                    r, g, b = pixel[:3] if len(pixel) >= 3 else (pixel, pixel, pixel)
                    
                    # Calculate "blueness" - dark blue indicates clear skies
                    is_clear = b > (r + 30) and b > (g + 30) and b > 100
                    
                    forecast_data.append({
                        'hour': hour,
                        'is_clear': is_clear,
                        'rgb': (r, g, b),
                    })
            
            # Calculate clear hours after sundown
            clear_hours = sum(1 for f in forecast_data if f['is_clear'])
            
            return {
                'forecast': forecast_data,
                'clear_hours_total': clear_hours,
                'last_updated': dt_util.utcnow(),
                'chart_url': self.chart_url,
            }
            
        except Exception as err:
            _LOGGER.error("Error parsing chart image: %s", err)
            return {
                'forecast': [],
                'clear_hours_total': 0,
                'last_updated': dt_util.utcnow(),
                'chart_url': self.chart_url,
            }

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
