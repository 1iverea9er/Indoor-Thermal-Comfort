from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    async def async_update_data():
        return {}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="comfort_tool",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok
