DOMAIN = "comfort_tool"

CONF_TA = "ta"
CONF_TR = "tr"
CONF_VA = "va"
CONF_RH = "rh"
CONF_CLO = "clo"
CONF_MET = "met"

SENSOR_TYPES = {
    "pmv": {"name": "PMV", "unit": "index"},
    "ppd": {"name": "PPD", "unit": "%"},
    "set": {"name": "SET", "unit": "°C"},
    "ce": {"name": "Cooling Effect", "unit": "°C"},
    "sensation": {"name": "Sensation", "unit": None},
}