from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "comfort_tool"

async def async_setup(hass: HomeAssistant, config: dict):
    return True


async def async_setup_entry(hass, config_entry):
    await hass.config_entries.async_forward_entry_setups(config_entry, ["sensor"])
    return True

async def async_unload_entry(hass, config_entry):
    return await hass.config_entries.async_unload_platforms(config_entry, ["sensor"])

