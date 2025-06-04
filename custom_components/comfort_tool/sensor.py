from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS, PERCENTAGE

from .lib.comfort_tool.comfort import calculate_pmv, calculate_ppd

SENSOR_TYPES = {
    "pmv": ["PMV", "Predicted Mean Vote", "pmv", TEMP_CELSIUS],
    "ppd": ["PPD", "Predicted Percentage of Dissatisfied", "ppd", PERCENTAGE],
}

async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([ThermalComfortSensor(sensor_type) for sensor_type in SENSOR_TYPES])

class ThermalComfortSensor(SensorEntity):
    def __init__(self, sensor_type):
        self._type = sensor_type
        self._attr_name = SENSOR_TYPES[sensor_type][0]
        self._attr_icon = f"mdi:thermometer"
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type][3]
        self._state = None

    def update(self):
        # Примерные входные данные, позже заменим на реальные сенсоры
        ta, tr, vel, rh, clo, met = 24, 24, 0.1, 50, 0.5, 1.2
        pmv = calculate_pmv(ta, tr, vel, rh, clo, met)
        ppd = calculate_ppd(pmv)

        if self._type == "pmv":
            self._state = round(pmv, 2)
        elif self._type == "ppd":
            self._state = round(ppd, 1)

    @property
    def native_value(self):
        return self._state
