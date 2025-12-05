"""Support for Clear Dark Sky camera."""
from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ClearDarkSkyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Clear Dark Sky camera based on a config entry."""
    coordinator: ClearDarkSkyCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([ClearDarkSkyCamera(coordinator)])


class ClearDarkSkyCamera(CoordinatorEntity, Camera):
    """Representation of a Clear Dark Sky chart camera."""

    def __init__(self, coordinator: ClearDarkSkyCoordinator) -> None:
        """Initialize the camera."""
        super().__init__(coordinator)
        Camera.__init__(self)
        
        self._attr_unique_id = f"{coordinator.chart_key}_chart"
        self._attr_name = f"Clear Dark Sky {coordinator.chart_key} Chart"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.chart_key)},
            "name": f"Clear Dark Sky {coordinator.chart_key}",
            "manufacturer": "Clear Dark Sky",
            "model": "Astronomy Forecast",
            "configuration_url": f"https://www.cleardarksky.com/c/{coordinator.chart_key}key.html",
        }

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:chart-line"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the chart image."""
        return self.coordinator.image_data

    @property
    def frame_interval(self) -> float:
        """Return the interval between frames of the stream."""
        return 3600.0  # Update every hour
