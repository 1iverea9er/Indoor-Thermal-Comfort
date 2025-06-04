from homeassistant import config_entries
from homeassistant.const import CONF_NAME
import voluptuous as vol

from .const import DOMAIN, CONF_TA, CONF_TR, CONF_VA, CONF_RH, CONF_CLO, CONF_MET

class ComfortToolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Comfort Tool."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_TA): str,
                vol.Required(CONF_TR): str,
                vol.Required(CONF_VA): str,
                vol.Required(CONF_RH): str,
                vol.Required(CONF_CLO): str,
                vol.Required(CONF_MET): str,
            }),
        )
