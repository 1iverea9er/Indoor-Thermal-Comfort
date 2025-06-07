import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .comfort import calculate_thermal_comfort

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    _LOGGER.debug("Setting up comfort sensors from config entry")

    coordinator = hass.data["comfort_tool"][config_entry.entry_id]["coordinator"]
    config = config_entry.data

    ta_entity = config.get("ta")
    tr_entity = config.get("tr")
    va_entity = config.get("va")
    rh_entity = config.get("rh")
    clo_entity = config.get("clo")
    met_entity = config.get("met")

    entities = [
        ComfortSensor(
            hass,
            coordinator,
            ta_entity,
            tr_entity,
            va_entity,
            rh_entity,
            clo_entity,
            met_entity,
        )
    ]

    _LOGGER.debug("Adding entities: %s", entities)
    async_add_entities(entities)

class ComfortSensor(SensorEntity):
    def __init__(self, hass, coordinator, ta_entity, tr_entity, va_entity, rh_entity, clo_entity, met_entity):
        self._attr_should_poll = True
        self._hass = hass
        self._coordinator = coordinator
        self._ta_entity = ta_entity
        self._tr_entity = tr_entity
        self._va_entity = va_entity
        self._rh_entity = rh_entity
        self._clo_entity = clo_entity
        self._met_entity = met_entity
        self._attr_name = "Thermal Comfort Index"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_unique_id = f"{DOMAIN}_{name}"
        self._state = None

    @property

    async def async_added_to_hass(self):
        await self.async_update()
        self.async_write_ha_state()
    def native_value(self):
        return self._state

    async def async_update(self):
        _LOGGER.debug("Updating Thermal Comfort Sensor")

        ta = self._get_state(self._ta_entity)
        tr = self._get_state(self._tr_entity)
        va = self._get_state(self._va_entity)
        rh = self._get_state(self._rh_entity)
        clo = self._get_state(self._clo_entity)
        met = self._get_state(self._met_entity)

        _LOGGER.debug("Sensor values: ta=%s, tr=%s, va=%s, rh=%s, clo=%s, met=%s", ta, tr, va, rh, clo, met)

        if None in (ta, tr, va, rh, clo, met):
            _LOGGER.warning("One or more sensor values are None, skipping calculation")
            self._state = None
            return

        try:
            self._state = calculate_thermal_comfort(ta, tr, va, rh, clo, met)
            _LOGGER.debug("Calculated thermal comfort index: %s", self._state)
        except Exception as e:
            _LOGGER.error("Error calculating thermal comfort: %s", e)
            self._state = None

    def _get_state(self, entity_id):
        state = self._hass.states.get(entity_id)
        if state is None:
            _LOGGER.warning("Entity %s not found", entity_id)
            return None

        try:
            return float(state.state)
        except ValueError:
            _LOGGER.warning("Could not convert state of %s to float: %s", entity_id, state.state)
            return None
