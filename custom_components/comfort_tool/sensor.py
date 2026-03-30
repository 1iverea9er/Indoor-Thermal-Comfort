from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.util import TemperatureConverter

class CustomSensor:
    def _get(self, temperature, unit):
        if unit == 'F':
            return TemperatureConverter.fahrenheit_to_celsius(temperature)
        return temperature
