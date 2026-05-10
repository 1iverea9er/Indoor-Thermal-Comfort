from homeassistant import config_entries
import voluptuous as vol
from homeassistant.helpers.selector import selector
from .const import (
    DOMAIN,
    CONF_DIRECT_IRRADIANCE,
    POSTURES, DEFAULT_POSTURE,
)

SENSOR_SELECTOR = selector({"entity": {"domain": ["sensor", "input_number"]}})

MAIN_SCHEMA = vol.Schema({
    vol.Optional("name"): str,
    vol.Required("ta"):  SENSOR_SELECTOR,
    vol.Optional("tr"):  SENSOR_SELECTOR,
    vol.Optional("va"):  SENSOR_SELECTOR,
    vol.Required("rh"):  SENSOR_SELECTOR,
    vol.Required("clo"): SENSOR_SELECTOR,
    vol.Required("met"): SENSOR_SELECTOR,
    vol.Optional(CONF_DIRECT_IRRADIANCE): SENSOR_SELECTOR,
})


class ComfortToolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("name", "Indoor Thermal Comfort"),
                data=user_input,
            )
        return self.async_show_form(step_id="user", data_schema=MAIN_SCHEMA)

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

        current = {**self.config_entry.data, **self.config_entry.options}

        schema = vol.Schema({
            vol.Optional("name",
                default=current.get("name", self.config_entry.title)): str,
            vol.Required("ta",  default=current.get("ta",  "")): SENSOR_SELECTOR,
            vol.Optional("tr",  default=current.get("tr",  "")): SENSOR_SELECTOR,
            vol.Optional("va",  default=current.get("va",  "")): SENSOR_SELECTOR,
            vol.Required("rh",  default=current.get("rh",  "")): SENSOR_SELECTOR,
            vol.Required("clo", default=current.get("clo", "")): SENSOR_SELECTOR,
            vol.Required("met", default=current.get("met", "")): SENSOR_SELECTOR,
            vol.Optional(CONF_DIRECT_IRRADIANCE,
                default=current.get(CONF_DIRECT_IRRADIANCE, "")): SENSOR_SELECTOR,
        })

        return self.async_show_form(step_id="init", data_schema=schema)


async def async_get_options_flow(config_entry):
    return ComfortToolOptionsFlowHandler(config_entry)
