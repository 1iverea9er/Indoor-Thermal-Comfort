from homeassistant import config_entries

class ComfortToolConfigFlow(config_entries.ConfigFlow, domain="comfort_tool"):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Comfort Tool", data={})
        return self.async_show_form(step_id="user")
