"""Solar parameter number entities for comfort_tool."""
from __future__ import annotations
import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity import EntityCategory

from .const import (
    DOMAIN,
    CONF_DIRECT_IRRADIANCE,
    CONF_SOLAR_AZIMUTH, CONF_T_SOL, CONF_F_SVV, CONF_F_BES, CONF_ASA,
    DEFAULT_T_SOL, DEFAULT_F_SVV, DEFAULT_F_BES, DEFAULT_ASA,
)

_LOGGER = logging.getLogger(__name__)

# (conf_key, name, min, max, step, default, icon, unit)
_SOLAR_NUMBER_DEFS = [
    (CONF_SOLAR_AZIMUTH, "SHARP",                0.0, 180.0, 1.0,  0.0,        "mdi:sun-angle",    "°"),
    (CONF_T_SOL,         "Solar Transmittance",  0.0, 1.0,   0.01, DEFAULT_T_SOL, "mdi:circle-opacity", None),
    (CONF_F_SVV,         "Sky View Factor",      0.0, 1.0,   0.01, DEFAULT_F_SVV, "mdi:white-balance-sunny", None),
    (CONF_F_BES,         "Body Sun Exposure",    0.0, 1.0,   0.01, DEFAULT_F_BES, "mdi:box-shadow",   None),
    (CONF_ASA,           "Solar Absorption",     0.2, 0.9,   0.01, DEFAULT_ASA,   "mdi:human",        None),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up solar number entities — only if direct_irradiance is configured."""
    config = {**entry.data, **entry.options}
    if not config.get(CONF_DIRECT_IRRADIANCE):
        return

    prefix = config.get("name", "Comfort")
    entities = [
        SolarNumberEntity(hass, entry, prefix, conf_key, name, min_v, max_v, step, default, icon, unit)
        for conf_key, name, min_v, max_v, step, default, icon, unit in _SOLAR_NUMBER_DEFS
    ]
    async_add_entities(entities, True)


class SolarNumberEntity(NumberEntity, RestoreEntity):
    """Editable number entity for a solar correction parameter."""

    _attr_mode = NumberMode.BOX
    _attr_entity_category  = EntityCategory.CONFIG

    def __init__(
        self, hass, entry, prefix,
        conf_key, name, min_v, max_v, step, default, icon, unit,
    ):
        self._hass     = hass
        self._entry    = entry
        self._conf_key = conf_key

        self._attr_name                       = f"{prefix} {name}"
        self._attr_unique_id                  = f"{DOMAIN}_{entry.entry_id}_{conf_key}"
        self._attr_icon                       = icon
        self._attr_native_min_value           = min_v
        self._attr_native_max_value           = max_v
        self._attr_native_step                = step
        self._attr_native_unit_of_measurement = unit
        self._attr_native_value               = default

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=prefix,
            manufacturer="Indoor Thermal Comfort",
            model="Comfort Tool",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        """Restore last value on restart."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            try:
                self._attr_native_value = float(last.state)
            except (ValueError, TypeError):
                pass

    @property
    def native_value(self) -> float:
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()