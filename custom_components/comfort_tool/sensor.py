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
    _LOGGER.debug("Setting up comfort sensors")
    config = entry.data

    ta = config["ta"]
    rh = config["rh"]
    clo = config["clo"]
    met = config["met"]
    tr = config.get("tr")
    va = config.get("va")
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
    def __init__(self, hass, entry_id, ta, tr, va, rh, clo, met, metric, prefix):
        self._hass = hass
        self._metric = metric
        self._ta = ta
        self._tr = tr
        self._va = va
        self._rh = rh
        self._clo = clo
        self._met = met

        self._attr_name = f"{prefix} {metric.upper()}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{metric}"
        self._attr_native_value = None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=prefix,
            manufacturer="Indoor Thermal Comfort",
            model="Comfort Tool",
            entry_type=DeviceEntryType.SERVICE,
        )

        icon_map = {
            "pmv": "mdi:scale-balance",
            "ppd": "mdi:account-group-outline",
            "set": "mdi:thermometer",
            "ce": "mdi:snowflake-thermometer",
            "ts": "mdi:meditation",
        }
        self._attr_icon = icon_map.get(metric)

        self._attr_native_unit_of_measurement = None

        if metric == "ppd":
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif metric == "pmv":
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif metric in ("set", "ce"):
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self._attr_native_value

    async def async_update(self):
        ta_state = self._hass.states.get(self._ta)

        ta = self._get(self._ta)
        rh = self._get(self._rh)
        clo = self._get(self._clo)
        met = self._get(self._met)

        va = self._get(self._va) if self._va else 0.0
        tr = self._get(self._tr) if self._tr else ta

        if any(x is None for x in [ta, rh, clo, met]) or tr is None:
            self._attr_native_value = None
            return

        result = calculate_thermal_comfort(ta, tr, va, rh, clo, met)
        value = result.get(self._metric)

        # ===== get unit of ta  =====
        unit = None
        if ta_state:
            unit = ta_state.attributes.get("unit_of_measurement")

        if unit is None:
            unit = self._hass.config.units.temperature_unit

        # ===== convert OUTPUT =====
        if self._metric in ("set", "ce"):
            if unit == UnitOfTemperature.FAHRENHEIT:
                value = TemperatureConverter.convert(
                    value,
                    UnitOfTemperature.CELSIUS,
                    UnitOfTemperature.FAHRENHEIT,
                )
                self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
            else:
                self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

        self._attr_native_value = value

    def _get(self, entity_id):
        state = self._hass.states.get(entity_id)
    
        if not state:
            return None
    
        try:
            value = float(state.state)
        except (ValueError, TypeError):
            return None
    
        device_class = state.attributes.get("device_class")
        unit = state.attributes.get("unit_of_measurement")
    
        # fallback
        if unit is None:
            unit = self._hass.config.units.temperature_unit
    
        # ===== TEMP =====
        if device_class == SensorDeviceClass.TEMPERATURE or unit in (
            UnitOfTemperature.CELSIUS,
            UnitOfTemperature.FAHRENHEIT,
        ):
            if unit == UnitOfTemperature.FAHRENHEIT:
                value = TemperatureConverter.convert(
                    value,
                    UnitOfTemperature.FAHRENHEIT,
                    UnitOfTemperature.CELSIUS,
                )
    
        # ===== SPEED =====
        elif device_class == SensorDeviceClass.SPEED or unit in (
            UnitOfSpeed.METERS_PER_SECOND,
            UnitOfSpeed.KILOMETERS_PER_HOUR,
            UnitOfSpeed.MILES_PER_HOUR,
            UnitOfSpeed.FEET_PER_SECOND,
        ):
            if unit != UnitOfSpeed.METERS_PER_SECOND:
                try:
                    value = SpeedConverter.convert(
                        value,
                        unit,
                        UnitOfSpeed.METERS_PER_SECOND,
                    )
                except Exception:
                    _LOGGER.warning("Failed to convert speed: %s %s", value, unit)
    
        return value
