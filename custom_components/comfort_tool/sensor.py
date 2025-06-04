from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS, PERCENTAGE
from homeassistant.core import callback

from .lib.comfort_tool.comfort import calculate_pmv, calculate_ppd

SENSOR_TYPES = {
    "pmv": ["PMV", "Predicted Mean Vote", "pmv", TEMP_CELSIUS],
    "ppd": ["PPD", "Predicted Percentage of Dissatisfied", "ppd", PERCENTAGE],
}

async def async_setup_entry(hass, config_entry, async_add_entities):
    options = config_entry.options

    input_entities = {
        "ta": options.get("ta"),
        "tr": options.get("tr"),
        "va": options.get("va"),
        "rh": options.get("rh"),
        "clo": options.get("clo"),
        "met": options.get("met"),
    }

    sensors = [
        ThermalComfortSensor(sensor_type, input_entities)
        for sensor_type in SENSOR_TYPES
    ]

    async_add_entities(sensors)

class ThermalComfortSensor(SensorEntity):
    def __init__(self, sensor_type, input_entities):
        self._type = sensor_type
        self._attr_name = SENSOR_TYPES[sensor_type][0]
        self._attr_icon = f"mdi:thermometer"
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type][3]
        self._state = None
        self._input_entities = input_entities

    async def async_update(self):
        hass = self.hass
        try:
            ta = float(hass.states.get(self._input_entities["ta"]).state)
            tr = float(hass.states.get(self._input_entities["tr"]).state)
            va = float(hass.states.get(self._input_entities["va"]).state)
            rh = float(hass.states.get(self._input_entities["rh"]).state)
            clo = float(hass.states.get(self._input_entities["clo"]).state)
            met = float(hass.states.get(self._input_entities["met"]).state)
        except (TypeError, ValueError, AttributeError):
            self._state = None
            return

        pmv = calculate_pmv(ta, tr, va, rh, clo, met)
        ppd = calculate_ppd(pmv)

        if self._type == "pmv":
            self._state = round(pmv, 2)
        elif self._type == "ppd":
            self._state = round(ppd, 1)

    @property
    def native_value(self):
        return self._state
