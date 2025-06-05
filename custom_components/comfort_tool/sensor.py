import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from .comfort import calculate_thermal_comfort

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "pmv": "Predicted Mean Vote",
    "ppd": "Predicted Percentage of Dissatisfied",
    "set": "Standard Effective Temperature",
}

async def async_setup_entry(hass, config_entry, async_add_entities):
    options = config_entry.options
    _LOGGER.debug("Setting up comfort sensors with options: %s", options)

    required = ("ta", "tr", "va", "rh", "clo", "met")
    missing = [k for k in required if k not in options]

    if missing:
        _LOGGER.error("Missing one or more required options: %s", missing)
        return

    try:
        sensors = [
            ThermalComfortSensor(hass, config_entry, sensor_type)
            for sensor_type in SENSOR_TYPES
        ]
        async_add_entities(sensors, update_before_add=True)
        _LOGGER.info("Thermal comfort sensors initialized successfully.")
    except Exception as e:
        _LOGGER.exception("Error initializing sensors: %s", e)

class ThermalComfortSensor(SensorEntity):
    def __init__(self, hass, config_entry, sensor_type):
        self._hass = hass
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._name = f"Comfort {sensor_type.upper()}"
        self._state = None
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS if sensor_type == "set" else None
        _LOGGER.debug("Created sensor: %s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"{self._config_entry.entry_id}_{self._sensor_type}"

    @property
    def state(self):
        return self._state

    
    async def async_update(self):
    def safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    _LOGGER.debug("Updating sensor %s...", self.name)

        opts = self._config_entry.options
        _LOGGER.debug("Updating sensor %s with options: %s", self._sensor_type, opts)
        try:
            ta = float(self._hass.states.get(opts["ta"]["entity_id"]).state)
            tr = float(self._hass.states.get(opts["tr"]["entity_id"]).state)
            va = float(self._hass.states.get(opts["va"]["entity_id"]).state)
            rh = float(self._hass.states.get(opts["rh"]["entity_id"]).state)
            clo = float(self._hass.states.get(opts["clo"]["entity_id"]).state)
            met = float(self._hass.states.get(opts["met"]["entity_id"]).state)

            result = calculate_thermal_comfort(ta, tr, va, rh, clo, met)
            self._state = result.get(self._sensor_type)
            _LOGGER.debug("Sensor %s updated state: %s", self._sensor_type, self._state)
        except Exception as e:
            _LOGGER.exception("Error updating sensor %s: %s", self._sensor_type, e)
            self._state = None
