"""Support for Clear Dark Sky binary sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import ClearDarkSkyCoordinator


@dataclass
class ClearDarkSkyBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Clear Dark Sky binary sensor entity."""

    value_fn: Callable[[dict], bool] = None
    attr_fn: Callable[[dict], dict] = None


BINARY_SENSOR_TYPES: tuple[ClearDarkSkyBinarySensorEntityDescription, ...] = (
    ClearDarkSkyBinarySensorEntityDescription(
        key="clear_sky_tonight",
        name="Clear Sky Tonight",
        icon="mdi:weather-night",
        value_fn=lambda data: _is_clear_tonight(data),
        attr_fn=lambda data: {
            'clear_hours': data.get('clear_hours_total', 0),
            'darkness_hours': data.get('darkness_hours', 0),
            'percentage_clear': _calculate_clear_percentage(data),
        },
    ),
    ClearDarkSkyBinarySensorEntityDescription(
        key="good_observing",
        name="Good Observing Conditions",
        icon="mdi:telescope",
        value_fn=lambda data: _is_good_observing(data),
        attr_fn=lambda data: {
            'quality': _calculate_quality_score(data),
            'clear_hours': data.get('clear_hours_total', 0),
        },
    ),
    ClearDarkSkyBinarySensorEntityDescription(
        key="astronomical_darkness",
        name="Astronomical Darkness",
        icon="mdi:weather-night",
        value_fn=lambda data: _is_astronomical_darkness(data),
        attr_fn=lambda data: {
            'dusk': data.get('astronomical_dusk'),
            'dawn': data.get('astronomical_dawn'),
        },
    ),
)


def _is_clear_tonight(data: dict) -> bool:
    """Determine if sky will be mostly clear tonight."""
    clear_hours = data.get('clear_hours_total', 0)
    darkness_hours = data.get('darkness_hours', 0)
    
    if darkness_hours > 0:
        return clear_hours >= darkness_hours * 0.5  # At least 50% clear
    return clear_hours > 3  # Fallback: at least 3 clear hours


def _is_good_observing(data: dict) -> bool:
    """Determine if conditions are good for observing."""
    clear_hours = data.get('clear_hours_total', 0)
    darkness_hours = data.get('darkness_hours', 0)
    
    if darkness_hours > 0:
        return clear_hours >= darkness_hours * 0.7  # At least 70% clear
    return clear_hours > 5  # Fallback: at least 5 clear hours


def _is_astronomical_darkness(data: dict) -> bool:
    """Check if it's currently astronomical darkness."""
    now = dt_util.now()
    dusk = data.get('astronomical_dusk')
    dawn = data.get('astronomical_dawn')
    
    if dusk and dawn:
        return dusk <= now <= dawn
    return False


def _calculate_clear_percentage(data: dict) -> float:
    """Calculate percentage of darkness that will be clear."""
    clear_hours = data.get('clear_hours_total', 0)
    darkness_hours = data.get('darkness_hours', 0)
    
    if darkness_hours > 0:
        return round((clear_hours / darkness_hours) * 100, 1)
    return 0.0


def _calculate_quality_score(data: dict) -> int:
    """Calculate quality score 0-100."""
    clear_hours = data.get('clear_hours_total', 0)
    darkness_hours = data.get('darkness_hours', 0)
    
    if darkness_hours > 0:
        return min(100, int((clear_hours / darkness_hours) * 100))
    return int(min(100, clear_hours * 10))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Clear Dark Sky binary sensors based on a config entry."""
    coordinator: ClearDarkSkyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ClearDarkSkyBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_TYPES
    ]

    async_add_entities(entities)


class ClearDarkSkyBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Clear Dark Sky binary sensor."""

    entity_description: ClearDarkSkyBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: ClearDarkSkyCoordinator,
        description: ClearDarkSkyBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.chart_key}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.chart_key)},
            "name": f"Clear Dark Sky {coordinator.chart_key}",
            "manufacturer": "Clear Dark Sky",
            "model": "Astronomy Forecast",
            "configuration_url": f"https://www.cleardarksky.com/c/{coordinator.chart_key}key.html",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if self.coordinator.data and self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        if self.coordinator.data and self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.coordinator.data)
        return {}
