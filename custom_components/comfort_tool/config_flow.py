from homeassistant import config_entries
import voluptuous as vol
from homeassistant.helpers.selector import selector

from .const import DOMAIN

SENSOR_SELECTOR = selector({
    "entity": {
        "domain": ["sensor", "input_number"]
    }
})

CONFIG_SCHEMA = vol.Schema({
    vol.Required("ta"): SENSOR_SELECTOR,
    vol.Required("tr"): SENSOR_SELECTOR,
    vol.Required("va"): SENSOR_SELECTOR,
    vol.Required("rh"): SENSOR_SELECTOR,
    vol.Required("clo"): SENSOR_SELECTOR,
    vol.Required("met"): SENSOR_SELECTOR,
})

class ComfortToolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Comfort Tool", data=user_input)

        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

    async def async_step_reauth(self, user_input=None):
        return await self.async_step_user()

    async def async_step_import(self, import_config):
        return await self.async_step_user()

class ComfortToolOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("ta", default=options.get("ta", "")): SENSOR_SELECTOR,
                vol.Required("tr", default=options.get("tr", "")): SENSOR_SELECTOR,
                vol.Required("va", default=options.get("va", "")): SENSOR_SELECTOR,
                vol.Required("rh", default=options.get("rh", "")): SENSOR_SELECTOR,
                vol.Required("clo", default=options.get("clo", "")): SENSOR_SELECTOR,
                vol.Required("met", default=options.get("met", "")): SENSOR_SELECTOR,
            })
        )

async def async_get_options_flow(config_entry):
    return ComfortToolOptionsFlowHandler(config_entry)
