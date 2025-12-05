"""Config flow for Clear Dark Sky integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_CHART_KEY, DOMAIN, CHART_URL_TEMPLATE

_LOGGER = logging.getLogger(__name__)


async def validate_chart_key(hass: HomeAssistant, chart_key: str) -> bool:
    """Validate the chart key by attempting to fetch the chart image."""
    session = async_get_clientsession(hass)
    url = CHART_URL_TEMPLATE.format(chart_key=chart_key)
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                content_type = response.headers.get('content-type', '')
                return 'image' in content_type
    except Exception as err:
        _LOGGER.error("Error validating chart key: %s", err)
    
    return False


class ClearDarkSkyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Clear Dark Sky."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            chart_key = user_input[CONF_CHART_KEY]
            
            # Validate chart key
            if await validate_chart_key(self.hass, chart_key):
                # Create unique ID
                await self.async_set_unique_id(chart_key)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, f"Clear Dark Sky {chart_key}"),
                    data=user_input,
                )
            else:
                errors["base"] = "invalid_chart_key"

        # Get default lat/lon from Home Assistant configuration
        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Clear Dark Sky"): str,
                vol.Required(CONF_CHART_KEY): str,
                vol.Optional(CONF_LATITUDE, default=default_lat): vol.Coerce(float),
                vol.Optional(CONF_LONGITUDE, default=default_lon): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "chart_help": "Find your chart key at https://www.cleardarksky.com/csk/. "
                             "For example, if your chart URL is 'https://www.cleardarksky.com/c/OttawaONcsk.gif', "
                             "your chart key is 'OttawaON'."
            },
        )
