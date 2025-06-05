from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_state_change
from homeassistant.core import callback

from .const import DOMAIN
from .lib.comfort_tool.comfort import pmv_ppd

async def async_setup_entry(hass, config_entry, async_add_entities):
    options = config_entry.options
    if not all(k in options for k in ("ta", "tr", "va", "rh", "clo", "met")):
        return

    sensor = ComfortSensor(hass, config_entry)
    async_add_entities([sensor])

class ComfortSensor(SensorEntity):
    def __init__(self, hass, config_entry):
        self._hass = hass
        self._config_entry = config_entry
        self._state = None
        self._attr_name = "PMV"
        self._attr_unique_id = f"{config_entry.entry_id}_pmv"

        self.entity_ids = [
            config_entry.options["ta"],
            config_entry.options["tr"],
            config_entry.options["va"],
            config_entry.options["rh"],
            config_entry.options["clo"],
            config_entry.options["met"],
        ]

        async_track_state_change(hass, self.entity_ids, self._state_changed)

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return "PMV"

    @callback
    def _state_changed(self, entity_id, old_state, new_state):
        try:
            states = self._hass.states
            ta = float(states.get(self._config_entry.options["ta"]).state)
            tr = float(states.get(self._config_entry.options["tr"]).state)
            va = float(states.get(self._config_entry.options["va"]).state)
            rh = float(states.get(self._config_entry.options["rh"]).state)
            clo = float(states.get(self._config_entry.options["clo"]).state)
            met = float(states.get(self._config_entry.options["met"]).state)

            pmv, _ = pmv_ppd(
                ta=ta,
                tr=tr,
                vel=va,
                rh=rh,
                clo=clo,
                met=met,
                wme=0,
                standard="ashrae"
            )

            self._state = round(pmv, 2)
            self.async_write_ha_state()
        except Exception:
            self._state = None
