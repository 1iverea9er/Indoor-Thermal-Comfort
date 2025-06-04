from homeassistant.helpers.entity import SensorEntity
from homeassistant.const import TEMP_CELSIUS

from .const import DOMAIN, SENSOR_TYPES

from comfort_tool import calculate_pmv, calculate_ppd, calculate_set, calculate_ce, get_sensation

async def async_setup_entry(hass, config_entry, async_add_entities):
    config = config_entry.data
    sensors = []

    for sensor_type in SENSOR_TYPES:
        sensors.append(ComfortToolSensor(hass, config, sensor_type))

    async_add_entities(sensors, True)

class ComfortToolSensor(SensorEntity):
    def __init__(self, hass, config, sensor_type):
        self.hass = hass
        self._config = config
        self._type = sensor_type
        self._name = f"{config.get('name')} {SENSOR_TYPES[sensor_type]['name']}"
        self._unit = SENSOR_TYPES[sensor_type]["unit"]
        self._state = None

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._state

    @property
    def native_unit_of_measurement(self):
        return self._unit

    async def async_update(self):
        ta = self.hass.states.get(self._config["ta"]).state
        tr = self.hass.states.get(self._config["tr"]).state
        va = self.hass.states.get(self._config["va"]).state
        rh = self.hass.states.get(self._config["rh"]).state
        clo = self.hass.states.get(self._config["clo"]).state
        met = self.hass.states.get(self._config["met"]).state

        try:
            ta = float(ta)
            tr = float(tr)
            va = float(va)
            rh = float(rh)
            clo = float(clo)
            met = float(met)
        except ValueError:
            self._state = None
            return

        if self._type == "pmv":
            self._state = calculate_pmv(ta, tr, va, rh, clo, met)
        elif self._type == "ppd":
            self._state = calculate_ppd(ta, tr, va, rh, clo, met)
        elif self._type == "set":
            self._state = calculate_set(ta, tr, va, rh, clo, met)
        elif self._type == "ce":
            self._state = calculate_ce(ta, tr, va, rh, clo, met)
        elif self._type == "sensation":
            self._state = get_sensation(ta, tr, va, rh, clo, met)
        else:
            self._state = None
