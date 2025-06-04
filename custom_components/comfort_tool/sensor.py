from homeassistant.components.sensor import SensorEntity
from homeassistant.const import TEMP_CELSIUS

from .lib.comfort_tool.comfort import calculate_pmv, calculate_ppd

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([ThermalComfortSensor()])

class ThermalComfortSensor(SensorEntity):
    _attr_name = "Thermal Comfort PMV"
    _attr_native_unit_of_measurement = TEMP_CELSIUS

    def __init__(self):
        self._state = None

    def update(self):
        ta, tr, vel, rh, clo, met = 24, 24, 0.1, 50, 0.5, 1.2
        self._state = round(calculate_pmv(ta, tr, vel, rh, clo, met), 2)

    @property
    def native_value(self):
        return self._state
