"""Solar posture select entity for comfort_tool."""
from __future__ import annotations
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import EntityCategory

from .const import (
    DOMAIN,
    CONF_DIRECT_IRRADIANCE,
    CONF_POSTURE,
    POSTURES,
    DEFAULT_POSTURE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up posture select entity — only if direct_irradiance is configured."""
    config = {**entry.data, **entry.options}
    if not config.get(CONF_DIRECT_IRRADIANCE):
        return

    prefix = config.get("name", "Comfort")
    async_add_entities([PostureSelectEntity(hass, entry, prefix)], True)


class PostureSelectEntity(SelectEntity, RestoreEntity):
    """Select entity for occupant posture."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass, entry, prefix):
        self._hass  = hass
        self._entry = entry

        self._attr_name        = f"{prefix} Occupant Posture"
        self._attr_unique_id   = f"{DOMAIN}_{entry.entry_id}_{CONF_POSTURE}"
        self._attr_icon        = "mdi:human"
        self._attr_options     = POSTURES
        self._attr_current_option = DEFAULT_POSTURE

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=prefix,
            manufacturer="Indoor Thermal Comfort",
            model="Comfort Tool",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        """Restore last selected option on restart."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in POSTURES:
            self._attr_current_option = last.state

    @property
    def current_option(self) -> str:
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()