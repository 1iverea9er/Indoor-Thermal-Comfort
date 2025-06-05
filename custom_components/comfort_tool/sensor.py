
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.event import async_track_state_change_event

from .comfort import calculate_thermal_comfort
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "pmv": {"name": "Thermal Comfort PMV", "unit": ""},
    "ppd": {"name": "Thermal Comfort PPD", "unit": "%"},
    "set": {"name": "Thermal Comfort SET", "unit": TEMP_CELSIUS},
    "ce": {"name": "Thermal Comfort Cooling Effect", "unit": TEMP_CELSIUS},
    "sensation": {"name": "Thermal Comfort Sensation", "unit": ""},
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.debug("Setting up entry with options: %s", config_entry.options)
    
    _LOGGER.info("Setting up Indoor Thermal Comfort sensors")
    config = hass.data[DOMAIN][config_entry.entry_id]
    options = config_entry.options

    required = ("ta", "tr", "va", "rh", "clo", "met")
    if not all(k in options for k in required):
        _LOGGER.error("Missing one or more required options: %s", required)
        return

    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(ThermalComfortSensor(hass, options, sensor_type))
    async_add_entities(entities)
    _LOGGER.info("Thermal comfort sensors added: %s", [e.name for e in entities])


class ThermalComfortSensor(SensorEntity):
    def __init__(self, hass, options, sensor_type):
        self._hass = hass
        self._options = options
        self._sensor_type = sensor_type
        self._attr_name = SENSOR_TYPES[sensor_type]["name"]
        self._attr_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        self._attr_unique_id = f"thermal_comfort_{sensor_type}"
        self._state = None

        self._ta = options["ta"]
        self._tr = options["tr"]
        self._va = options["va"]
        self._rh = options["rh"]
        self._clo = options["clo"]
        self._met = options["met"]

    
async def async_added_to_hass(self):
        _LOGGER.debug("Sensor '%s' added to hass", self.name)
    
        for entity_id in (self._ta, self._tr, self._va, self._rh, self._clo, self._met):
            async_track_state_change_event(self._hass, entity_id, self._state_changed)
        await self._state_changed(None)

    @property
    def native_value(self):
        return self._state

    async def _state_changed(self, event):
        try:
            states = self._hass.states
            ta = float(states.get(self._ta).state)
            tr = float(states.get(self._tr).state)
            va = float(states.get(self._va).state)
            rh = float(states.get(self._rh).state)
            clo = float(states.get(self._clo).state)
            met = float(states.get(self._met).state)

            results = calculate_thermal_comfort(ta, tr, va, rh, clo, met)
            value = results.get(self._sensor_type)
            self._state = round(value, 2) if isinstance(value, (float, int)) else value
            self.async_write_ha_state()
            _LOGGER.debug("Updated %s: %s", self._sensor_type, self._state)
        except Exception as e:
            _LOGGER.error("Error updating %s sensor: %s", self._sensor_type, e)
