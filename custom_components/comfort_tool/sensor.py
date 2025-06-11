import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .comfort import calculate_thermal_comfort

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("Setting up comfort sensors")
    config = entry.data

    ta = config["ta"]
    tr = config["tr"]
    va = config["va"]
    rh = config["rh"]
    clo = config["clo"]
    met = config["met"]

    entities = []
    for metric in ["pmv", "ppd", "set", "ce", "ts"]:
        entities.append(ComfortSensor(
            hass, entry.entry_id,
            ta, tr, va, rh, clo, met,
            metric
        ))

    async_add_entities(entities, True)

class ComfortSensor(SensorEntity):
    def __init__(self, hass, entry_id, ta, tr, va, rh, clo, met, metric):
        self._hass = hass
        self._metric = metric
        self._ta = ta
        self._tr = tr
        self._va = va
        self._rh = rh
        self._clo = clo
        self._met = met

        self._attr_name = f"Comfort {metric.upper()}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{metric}"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = None

        if metric in ["pmv", "set", "ce"]:
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif metric == "ppd":
            self._attr_native_unit_of_measurement = PERCENTAGE
        else:
            self._attr_native_unit_of_measurement = None

    @property
    def native_value(self):
        return self._attr_native_value

    async def async_update(self):
        ta = self._get(self._ta)
        tr = self._get(self._tr)
        va = self._get(self._va)
        rh = self._get(self._rh)
        clo = self._get(self._clo)
        met = self._get(self._met)

        if any(x is None for x in [ta, tr, va, rh, clo, met]):
            self._attr_native_value = None
            return

        result = calculate_thermal_comfort(ta, tr, va, rh, clo, met)
        self._attr_native_value = result.get(self._metric)

    def _get(self, entity_id):
        state = self._hass.states.get(entity_id)
        try:
            return float(state.state) if state else None
        except (ValueError, TypeError):
            return None
