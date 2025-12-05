"""Support for Clear Dark Sky sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ClearDarkSkyCoordinator


@dataclass
class ClearDarkSkySensorEntityDescription(SensorEntityDescription):
    """Describes Clear Dark Sky sensor entity."""

    value_fn: Callable[[dict], StateType] = None
    attr_fn: Callable[[dict], dict] = None


SENSOR_TYPES: tuple[ClearDarkSkySensorEntityDescription, ...] = (
    ClearDarkSkySensorEntityDescription(
        key="clear_hours_tonight",
        name="Clear Hours Tonight",
        icon="mdi:weather-night",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get('clear_hours_total', 0),
    ),
    ClearDarkSkySensorEntityDescription(
        key="darkness_hours",
        name="Darkness Hours",
        icon="mdi:weather-night",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.get('darkness_hours', 0), 1),
    ),
    ClearDarkSkySensorEntityDescription(
        key="astronomical_dusk",
        name="Astronomical Dusk",
        icon="mdi:weather-sunset-down",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.get('astronomical_dusk'),
    ),
    ClearDarkSkySensorEntityDescription(
        key="astronomical_dawn",
        name="Astronomical Dawn",
        icon="mdi:weather-sunset-up",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.get('astronomical_dawn'),
    ),
    ClearDarkSkySensorEntityDescription(
        key="observing_quality",
        name="Observing Quality",
        icon="mdi:telescope",
        value_fn=lambda data: _calculate_quality(data),
        attr_fn=lambda data: {
            'clear_hours': data.get('clear_hours_total', 0),
            'darkness_hours': data.get('darkness_hours', 0),
            'forecast_count': len(data.get('forecast', [])),
        },
    ),
)


def _calculate_quality(data: dict) -> str:
    """Calculate overall observing quality."""
    clear_hours = data.get('clear_hours_total', 0)
    darkness_hours = data.get('darkness_hours', 0)
    
    if clear_hours == 0:
        return "Poor"
    elif clear_hours >= darkness_hours * 0.8:
        return "Excellent"
    elif clear_hours >= darkness_hours * 0.5:
        return "Good"
    elif clear_hours >= darkness_hours * 0.3:
        return "Fair"
    else:
        return "Poor"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Clear Dark Sky sensors based on a config entry."""
    coordinator: ClearDarkSkyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ClearDarkSkySensor(coordinator, description)
        for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class ClearDarkSkySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Clear Dark Sky sensor."""

    entity_description: ClearDarkSkySensorEntityDescription

    def __init__(
        self,
        coordinator: ClearDarkSkyCoordinator,
        description: ClearDarkSkySensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data and self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        if self.coordinator.data and self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.coordinator.data)
        return {}
