import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import UnitOfTemperature, UnitOfSpeed, PERCENTAGE
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util.unit_conversion import TemperatureConverter, SpeedConverter
from homeassistant.helpers import entity_registry as er
from .const import (
    DOMAIN,
    CONF_SOLAR_AZIMUTH, CONF_DIRECT_IRRADIANCE,
    CONF_T_SOL, CONF_F_SVV, CONF_F_BES, CONF_ASA, CONF_POSTURE,
    DEFAULT_POSTURE, DEFAULT_T_SOL, DEFAULT_F_SVV, DEFAULT_F_BES, DEFAULT_ASA,
)
from .comfort import calculate_thermal_comfort
from .solar import calculate_erf, calculate_delta_mrt

_LOGGER = logging.getLogger(__name__)
_SUN_ENTITY = "sun.sun"


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("Setting up comfort sensors")
    config = {**entry.data, **entry.options}

    ta     = config["ta"]
    rh     = config["rh"]
    clo    = config["clo"]
    met    = config["met"]
    tr     = config.get("tr")
    va     = config.get("va")
    prefix = config.get("name", "Comfort")

    solar_on = bool(config.get(CONF_DIRECT_IRRADIANCE))

    entities = []
    for metric in ["pmv", "ppd", "set", "ce", "ts"]:
        entities.append(
            ComfortSensor(hass, entry, ta, tr, va, rh, clo, met, metric, prefix)
        )

    if solar_on:
        entities.append(SolarErfSensor(hass, entry, prefix))
        entities.append(SolarDeltaMrtSensor(hass, entry, prefix))

    async_add_entities(entities, True)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class _BaseComfortSensor(SensorEntity):

    def __init__(self, hass, entry, prefix: str):
        self._hass   = hass
        self._entry  = entry
        self._prefix = prefix
        self._tracked_entities: list[str] = []
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=prefix,
            manufacturer="",
            model="Indoor Thermal Comfort",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _config(self) -> dict:
        return {**self._entry.data, **self._entry.options}

    def _base_tracked_entities(self) -> list[str]:
        """Override in subclasses to declare which entities to track."""
        return []

    async def async_added_to_hass(self) -> None:
        """Subscribe to state changes of all input entities."""
        await super().async_added_to_hass()

        entities = list(filter(None, self._base_tracked_entities()))

        config = self._config
        if config.get(CONF_DIRECT_IRRADIANCE):
            entities.append(config[CONF_DIRECT_IRRADIANCE])
            entities.append(_SUN_ENTITY)
            registry = er.async_get(self._hass)
            entry_id = self._entry.entry_id
            for conf_key in (CONF_SOLAR_AZIMUTH, CONF_T_SOL,
                             CONF_F_SVV, CONF_F_BES, CONF_ASA):
                uid = f"{DOMAIN}_{entry_id}_{conf_key}"
                eid = registry.async_get_entity_id("number", DOMAIN, uid)
                if eid:
                    entities.append(eid)
            uid = f"{DOMAIN}_{entry_id}_{CONF_POSTURE}"
            eid = registry.async_get_entity_id("select", DOMAIN, uid)
            if eid:
                entities.append(eid)

        self._tracked_entities = list(set(entities))

        if self._tracked_entities:
            self.async_on_remove(
                async_track_state_change_event(
                    self._hass,
                    self._tracked_entities,
                    self._handle_state_change,
                )
            )
            _LOGGER.debug(
                "%s: tracking %d entities: %s",
                self.name, len(self._tracked_entities), self._tracked_entities,
            )

    async def _handle_state_change(self, event) -> None:
        """Immediate recalculation on any tracked entity change."""
        self.async_schedule_update_ha_state(force_refresh=True)

    def _get(self, entity_id, value_type=None):
        """
        Read a value from a sensor entity and convert to the correct
        base unit:

        value_type:
            - "temperature" → °C
            - "speed" → m/s
            - None → no conversion
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

        #
        # Temperature conversion to °C
        #
        if (
            value_type == "temperature"
            or device_class == SensorDeviceClass.TEMPERATURE
        ):
            # Fallback only for actual temperature values
            if unit is None:
                unit = self._hass.config.units.temperature_unit

            if unit == UnitOfTemperature.FAHRENHEIT:
                value = TemperatureConverter.convert(
                    value,
                    UnitOfTemperature.FAHRENHEIT,
                    UnitOfTemperature.CELSIUS,
                )

        #
        # Air velocity conversion to m/s
        #
        elif (
            value_type == "speed"
            or device_class == SensorDeviceClass.SPEED
        ):
            if unit in (
                UnitOfSpeed.KILOMETERS_PER_HOUR,
                UnitOfSpeed.MILES_PER_HOUR,
                UnitOfSpeed.FEET_PER_SECOND,
            ):
                try:
                    value = SpeedConverter.convert(
                        value,
                        unit,
                        UnitOfSpeed.METERS_PER_SECOND,
                    )
                except Exception:
                    _LOGGER.warning(
                        "Failed to convert speed: %s %s",
                        value,
                        unit,
                    )

        return value

    def _uses_fahrenheit(self) -> bool:
        """Return True if the HA instance is configured for imperial units."""
        return (
            self._hass.config.units.temperature_unit == UnitOfTemperature.FAHRENHEIT
        )

    def _solar_altitude(self) -> float | None:
        """Read solar elevation from sun.sun entity."""
        state = self._hass.states.get(_SUN_ENTITY)
        if state is None:
            return None
        try:
            return float(state.attributes.get("elevation", 0))
        except (ValueError, TypeError):
            return None

    def _get_solar_inputs(self) -> dict | None:
        """
        Collect solar inputs from the number/select entities
        created by this integration.
        Returns None if solar is not configured.
        """
        config     = self._config
        dir_entity = config.get(CONF_DIRECT_IRRADIANCE)
        if not dir_entity:
            return None

        i_dir          = self._get(dir_entity)
        solar_altitude = self._solar_altitude()
        if i_dir is None or solar_altitude is None:
            return None

        entry_id = self._entry.entry_id
        registry = er.async_get(self._hass)

        def _read_number(conf_key: str, fallback: float) -> float:
            uid   = f"{DOMAIN}_{entry_id}_{conf_key}"
            eid   = registry.async_get_entity_id("number", DOMAIN, uid)
            if eid is None:
                return fallback
            state = self._hass.states.get(eid)
            if state is None:
                return fallback
            try:
                return float(state.state)
            except (ValueError, TypeError):
                return fallback

        def _read_select(conf_key: str, fallback: str) -> str:
            uid   = f"{DOMAIN}_{entry_id}_{conf_key}"
            eid   = registry.async_get_entity_id("select", DOMAIN, uid)
            if eid is None:
                return fallback
            state = self._hass.states.get(eid)
            if state is None:
                return fallback
            return state.state

        return {
            "solar_altitude": solar_altitude,
            "solar_azimuth":  _read_number(CONF_SOLAR_AZIMUTH, 0.0),
            "i_dir":          i_dir,
            "t_sol":          _read_number(CONF_T_SOL, DEFAULT_T_SOL),
            "f_svv":          _read_number(CONF_F_SVV, DEFAULT_F_SVV),
            "f_bes":          _read_number(CONF_F_BES, DEFAULT_F_BES),
            "asa":            _read_number(CONF_ASA,   DEFAULT_ASA),
            "posture":        _read_select(CONF_POSTURE, DEFAULT_POSTURE),
        }


# ---------------------------------------------------------------------------
# PMV / PPD / SET / CE / TS
# ---------------------------------------------------------------------------

class ComfortSensor(_BaseComfortSensor):

    def __init__(self, hass, entry, ta, tr, va, rh, clo, met, metric, prefix):
        super().__init__(hass, entry, prefix)
        self._metric = metric
        self._ta = ta; self._tr = tr; self._va = va
        self._rh = rh; self._clo = clo; self._met = met

        self._attr_name         = f"{prefix} {metric.upper()}"
        self._attr_unique_id    = f"{DOMAIN}_{entry.entry_id}_{metric}"
        self._attr_native_value = None

        icon_map = {
            "pmv": "mdi:scale-balance",
            "ppd": "mdi:account-group-outline",
            "set": "mdi:thermometer",
            "ce":  "mdi:snowflake-thermometer",
            "ts":  "mdi:meditation",
        }
        self._attr_icon = icon_map.get(metric)

        if metric in ("set", "ce"):
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_state_class  = SensorStateClass.MEASUREMENT
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif metric == "ppd":
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif metric == "pmv":
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_native_unit_of_measurement = None

    def _base_tracked_entities(self) -> list[str]:
        return [self._ta, self._rh, self._clo, self._met, self._tr, self._va]

    @property
    def native_value(self):
        return self._attr_native_value

    async def async_update(self):
        ta  = self._get(self._ta, "temperature")
        rh  = self._get(self._rh)
        clo = self._get(self._clo)
        met = self._get(self._met)
        va  = self._get(self._va, "speed") if self._va else 0.0
        tr  = self._get(self._tr, "temperature") if self._tr else ta

        if any(x is None for x in [ta, rh, clo, met]) or tr is None:
            self._attr_native_value = None
            return

        # Solar ΔMrt correction — only if solar is configured
        # delta_mrt is always in °C (temperature difference), applied before
        # comfort calculation which also works in °C internally
        solar = self._get_solar_inputs()
        if solar is not None:
            try:
                delta = calculate_delta_mrt(**solar)
                _LOGGER.debug(
                    "%s: solar ΔMrt=%.2f°C applied to tr=%.2f°C",
                    self._attr_name, delta, tr,
                )
                tr += delta
            except Exception as e:
                _LOGGER.warning("%s: solar ΔMrt error: %s", self._attr_name, e)

        result = calculate_thermal_comfort(ta, tr, va, rh, clo, met)
        self._attr_native_value = result.get(self._metric)


# ---------------------------------------------------------------------------
# Solar sidecar sensors
# ---------------------------------------------------------------------------

class SolarErfSensor(_BaseComfortSensor):
    """Enhanced Radiant Field, W/m²."""

    _attr_native_unit_of_measurement  = "W/m²"
    _attr_icon                        = "mdi:heat-wave"
    _attr_state_class                 = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, hass, entry, prefix: str):
        super().__init__(hass, entry, prefix)
        self._attr_name         = f"{prefix} ERF"
        self._attr_unique_id    = f"{DOMAIN}_{entry.entry_id}_erf_solar"
        self._attr_native_value = None

    @property
    def native_value(self):
        return self._attr_native_value

    async def async_update(self):
        solar = self._get_solar_inputs()
        if solar is None:
            self._attr_native_value = None
            return
        try:
            self._attr_native_value = round(calculate_erf(**solar), 1)
        except Exception as e:
            _LOGGER.warning("%s: ERF error: %s", self._attr_name, e)
            self._attr_native_value = None


class SolarDeltaMrtSensor(_BaseComfortSensor):
    """Solar ΔMrt correction.

    Internally always calculated and stored in °C.
    ΔMrt is a temperature *difference*, not an absolute temperature:
      - °C delta  →  °F delta  requires  ×9/5  (no +32)
    HA's built-in TEMPERATURE device_class converts absolute values (+32),
    so we handle the unit ourselves and expose the correct unit symbol.
    """

    _attr_icon        = "mdi:sun-thermometer"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, hass, entry, prefix: str):
        super().__init__(hass, entry, prefix)
        self._attr_name         = f"{prefix} ΔMrt Solar"
        self._attr_unique_id    = f"{DOMAIN}_{entry.entry_id}_delta_mrt_solar"
        self._attr_native_value = None
        self._delta_celsius: float | None = None  # always in °C

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit matching the HA temperature system."""
        if self._uses_fahrenheit():
            return UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.CELSIUS

    async def async_update(self):
        solar = self._get_solar_inputs()
        if solar is None:
            self._attr_native_value = None
            self._delta_celsius = None
            return
        try:
            delta_c = round(calculate_delta_mrt(**solar), 2)
            self._delta_celsius = delta_c

            # Convert °C difference → °F difference if needed (×9/5, no +32)
            if self._uses_fahrenheit():
                self._attr_native_value = round(delta_c * 9 / 5, 2)
            else:
                self._attr_native_value = delta_c

        except Exception as e:
            _LOGGER.warning("%s: ΔMrt error: %s", self._attr_name, e)
            self._attr_native_value = None
            self._delta_celsius = None
