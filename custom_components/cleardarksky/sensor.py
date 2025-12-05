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
    # New detailed sensors for raw chart data
    ClearDarkSkySensorEntityDescription(
        key="cloud_cover_current",
        name="Cloud Cover (Current)",
        icon="mdi:cloud-percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.get('current_cloud_cover', 0), 1),
        attr_fn=lambda data: {
            'average_forecast': data.get('avg_cloud_cover', 0),
            'rating': _get_cloud_rating(data.get('current_cloud_cover', 0)),
        },
    ),
    ClearDarkSkySensorEntityDescription(
        key="cloud_cover_average",
        name="Cloud Cover (Average Forecast)",
        icon="mdi:cloud-percent-outline",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.get('avg_cloud_cover', 0), 1),
        attr_fn=lambda data: {
            'current': data.get('current_cloud_cover', 0),
            'rating': _get_cloud_rating(data.get('avg_cloud_cover', 0)),
        },
    ),
    ClearDarkSkySensorEntityDescription(
        key="transparency_current",
        name="Transparency (Current)",
        icon="mdi:eye",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.get('current_transparency', 0), 1),
        attr_fn=lambda data: {
            'average_forecast': data.get('avg_transparency', 0),
            'rating': _get_transparency_rating(data.get('current_transparency', 0)),
        },
    ),
    ClearDarkSkySensorEntityDescription(
        key="transparency_average",
        name="Transparency (Average Forecast)",
        icon="mdi:eye-outline",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.get('avg_transparency', 0), 1),
        attr_fn=lambda data: {
            'current': data.get('current_transparency', 0),
            'rating': _get_transparency_rating(data.get('avg_transparency', 0)),
        },
    ),
    ClearDarkSkySensorEntityDescription(
        key="seeing_current",
        name="Seeing (Current)",
        icon="mdi:magnify",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.get('current_seeing', 0), 1),
        attr_fn=lambda data: {
            'average_forecast': data.get('avg_seeing', 0),
            'rating': _get_seeing_rating(data.get('current_seeing', 0)),
        },
    ),
    ClearDarkSkySensorEntityDescription(
        key="seeing_average",
        name="Seeing (Average Forecast)",
        icon="mdi:magnify-scan",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.get('avg_seeing', 0), 1),
        attr_fn=lambda data: {
            'current': data.get('current_seeing', 0),
            'rating': _get_seeing_rating(data.get('avg_seeing', 0)),
        },
    ),
    ClearDarkSkySensorEntityDescription(
        key="darkness_current",
        name="Darkness (Current)",
        icon="mdi:brightness-2",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.get('current_darkness', 0), 1),
        attr_fn=lambda data: {
            'rating': _get_darkness_rating(data.get('current_darkness', 0)),
        },
    ),
    ClearDarkSkySensorEntityDescription(
        key="wind_current",
        name="Wind (Current)",
        icon="mdi:weather-windy",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.get('current_wind', 0), 1),
        attr_fn=lambda data: {
            'average_forecast': data.get('avg_wind', 0),
            'rating': _get_wind_rating(data.get('current_wind', 0)),
        },
    ),
    ClearDarkSkySensorEntityDescription(
        key="wind_average",
        name="Wind (Average Forecast)",
        icon="mdi:weather-windy-variant",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: round(data.get('avg_wind', 0), 1),
        attr_fn=lambda data: {
            'current': data.get('current_wind', 0),
            'rating': _get_wind_rating(data.get('avg_wind', 0)),
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


def _get_cloud_rating(value: float) -> str:
    """Get descriptive rating for cloud cover percentage."""
    if value < 20:
        return "Clear"
    elif value < 40:
        return "Mostly Clear"
    elif value < 60:
        return "Partly Cloudy"
    elif value < 80:
        return "Mostly Cloudy"
    else:
        return "Overcast"


def _get_transparency_rating(value: float) -> str:
    """Get descriptive rating for transparency percentage."""
    if value >= 80:
        return "Excellent"
    elif value >= 60:
        return "Good"
    elif value >= 40:
        return "Fair"
    elif value >= 20:
        return "Poor"
    else:
        return "Very Poor"


def _get_seeing_rating(value: float) -> str:
    """Get descriptive rating for seeing percentage."""
    if value >= 80:
        return "Excellent"
    elif value >= 60:
        return "Good"
    elif value >= 40:
        return "Fair"
    elif value >= 20:
        return "Poor"
    else:
        return "Very Poor"


def _get_darkness_rating(value: float) -> str:
    """Get descriptive rating for darkness percentage."""
    if value >= 80:
        return "Dark"
    elif value >= 60:
        return "Twilight"
    elif value >= 40:
        return "Dusk/Dawn"
    else:
        return "Daylight"


def _get_wind_rating(value: float) -> str:
    """Get descriptive rating for wind percentage (higher = calmer)."""
    if value >= 80:
        return "Calm"
    elif value >= 60:
        return "Light"
    elif value >= 40:
        return "Moderate"
    elif value >= 20:
        return "Breezy"
    else:
        return "Windy"


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