
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS
from .comfort import calculate_thermal_comfort

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    from homeassistant.helpers.entity import Entity
    _LOGGER.info("Setting up Indoor Thermal Comfort sensors")
    config = hass.data[DOMAIN][config_entry.entry_id]
    _LOGGER.debug(f"Received config: {config}")
    _LOGGER.debug("Setting up comfort_tool sensor entry")
    options = config_entry.options

    required = ("ta", "tr", "va", "rh", "clo", "met")
    if not all(k in options for k in required):
        _LOGGER.error("Missing one or more required options: %s", required)
        return

    sensor = PMVSensor(hass, options)
    async_add_entities([sensor])
    _LOGGER.debug("Sensor entity added: %s", sensor.name)

class PMVSensor(SensorEntity):
    def __init__(self, hass, options):
        _LOGGER.debug("Initializing PMVSensor with options: %s", options)
        self._hass = hass
        self._options = options
        self._attr_name = "Thermal Comfort PMV"
        self._attr_unit_of_measurement = TEMP_CELSIUS
        self._attr_unique_id = "thermal_comfort_pmv"
        self._state = None

        self._ta = options["ta"]
        self._tr = options["tr"]
        self._va = options["va"]
        self._rh = options["rh"]
        self._clo = options["clo"]
        self._met = options["met"]

        for entity_id in (self._ta, self._tr, self._va, self._rh, self._clo, self._met):
            hass.helpers.event.async_track_state_change_event(entity_id, self._state_changed)

    @property
    def native_value(self):
        return self._state

    async def _state_changed(self, event):
        _LOGGER.debug("State changed detected for event: %s", event)
        try:
            states = self._hass.states
            ta = float(states.get(self._ta).state)
            tr = float(states.get(self._tr).state)
            va = float(states.get(self._va).state)
            rh = float(states.get(self._rh).state)
            clo = float(states.get(self._clo).state)
            met = float(states.get(self._met).state)

            results = calculate_thermal_comfort(ta, tr, va, rh, clo, met)
            self._state = round(results["pmv"], 2)
            _LOGGER.debug("Calculated PMV: %s", self._state)
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error computing thermal comfort: %s", e)
