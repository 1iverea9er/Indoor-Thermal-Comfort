import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import UnitOfTemperature, UnitOfSpeed, PERCENTAGE
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from .const import DOMAIN
from .comfort import calculate_thermal_comfort
from homeassistant.util.unit_conversion import TemperatureConverter, SpeedConverter

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """
    Set up comfort sensors from a config entry.
    Creates one sensor per metric: pmv, ppd, set, ce, ts.
    """
    _LOGGER.debug("Setting up comfort sensors")
    config = entry.data

    ta = config["ta"]  # air temperature entity_id
    rh = config["rh"]  # relative humidity entity_id
    clo = config["clo"]  # clothing insulation
    met = config["met"]  # metabolic rate
    tr = config.get("tr")  # optional mean radiant temperature
    va = config.get("va")  # optional air velocity
    prefix = config.get("name", "Comfort")

    entities = []
    for metric in ["pmv", "ppd", "set", "ce", "ts"]:
        entities.append(
            ComfortSensor(
                hass,
                entry.entry_id,
                ta,
                tr,
                va,
                rh,
                clo,
                met,
                metric,
                prefix,
            )
        )

    async_add_entities(entities, True)


class ComfortSensor(SensorEntity):
    """Representation of a comfort metric sensor."""

    def __init__(self, hass, entry_id, ta, tr, va, rh, clo, met, metric, prefix):
        self._hass = hass
        self._metric = metric
        self._ta = ta
        self._tr = tr
        self._va = va
        self._rh = rh
        self._clo = clo
        self._met = met

        # Human-readable name
        self._attr_name = f"{prefix} {metric.upper()}"
        # Unique ID
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{metric}"
        # Placeholder for the sensor value
        self._attr_native_value = None

        # Device info for the sensor
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=prefix,
            manufacturer="Indoor Thermal Comfort",
            model="Comfort Tool",
            entry_type=DeviceEntryType.SERVICE,
        )

        # Choose icon per metric
        icon_map = {
            "pmv": "mdi:scale-balance",
            "ppd": "mdi:account-group-outline",
            "set": "mdi:thermometer",
            "ce": "mdi:snowflake-thermometer",
            "ts": "mdi:meditation",
        }
        self._attr_icon = icon_map.get(metric)

        # Set native unit and state class
        if metric in ("set", "ce"):
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif metric == "ppd":
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif metric == "pmv":
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_native_unit_of_measurement = None

    @property
    def native_value(self):
        """
        Return the sensor value in the base unit:
        - °C for temperature
        - m/s for velocity
        HA will automatically convert to °F or other units in the UI if needed.
        """
        return self._attr_native_value

    async def async_update(self):
        """
        Update sensor value by reading all required entities,
        converting them to base units if necessary, and running
        the thermal comfort calculation.
        """
        # Read all input entities and convert to float
        ta = self._get(self._ta)
        rh = self._get(self._rh)
        clo = self._get(self._clo)
        met = self._get(self._met)
        va = self._get(self._va) if self._va else 0.0
        tr = self._get(self._tr) if self._tr else ta  # fallback to air temperature

        if any(x is None for x in [ta, rh, clo, met]) or tr is None:
            self._attr_native_value = None
            return

        # Run comfort calculation
        result = calculate_thermal_comfort(ta, tr, va, rh, clo, met)
        self._attr_native_value = result.get(self._metric)

    def _get(self, entity_id):
        """
        Read a value from a sensor entity and convert to the correct
        base unit:
        - temperature → °C
        - speed → m/s
        """
        state = self._hass.states.get(entity_id)
        if not state:
            return None

        try:
            value = float(state.state)
        except (ValueError, TypeError):
            return None

        device_class = state.attributes.get("device_class")
        unit = state.attributes.get("unit_of_measurement")

        # Fallback if unit is missing
        if unit is None:
            unit = self._hass.config.units.temperature_unit

        # Temperature conversion to °C
        if device_class == SensorDeviceClass.TEMPERATURE or unit in (
            UnitOfTemperature.CELSIUS,
            UnitOfTemperature.FAHRENHEIT,
        ):
            if unit == UnitOfTemperature.FAHRENHEIT:
                value = TemperatureConverter.convert(
                    value, UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS
                )

        # Air velocity conversion to m/s
        elif device_class == SensorDeviceClass.SPEED or unit in (
            UnitOfSpeed.METERS_PER_SECOND,
            UnitOfSpeed.KILOMETERS_PER_HOUR,
            UnitOfSpeed.MILES_PER_HOUR,
            UnitOfSpeed.FEET_PER_SECOND,
        ):
            if unit != UnitOfSpeed.METERS_PER_SECOND:
                try:
                    value = SpeedConverter.convert(value, unit, UnitOfSpeed.METERS_PER_SECOND)
                except Exception:
                    _LOGGER.warning("Failed to convert speed: %s %s", value, unit)

        return value
