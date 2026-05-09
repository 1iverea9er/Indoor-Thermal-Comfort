import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN, CONF_DIRECT_IRRADIANCE

_LOGGER = logging.getLogger(__name__)

_PLATFORMS_BASE  = ["sensor"]
_PLATFORMS_SOLAR = ["sensor", "number", "select"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Setting up entry: %s", entry.entry_id)

    config = {**entry.data, **entry.options}
    platforms = _PLATFORMS_SOLAR if config.get(CONF_DIRECT_IRRADIANCE) else _PLATFORMS_BASE

    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Always attempt to unload ALL possible platforms.
    # We can't rely on current config here — options may already reflect
    # the new (post-save) state, so solar platforms would be missed
    # if direct_irradiance was just removed.
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS_SOLAR)
