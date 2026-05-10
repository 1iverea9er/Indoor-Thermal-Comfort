DOMAIN = "comfort_tool"

# Solar MRT correction
CONF_SOLAR_AZIMUTH     = "solar_azimuth"
CONF_DIRECT_IRRADIANCE = "direct_irradiance"
CONF_T_SOL             = "t_sol"
CONF_F_SVV             = "f_svv"
CONF_F_BES             = "f_bes"
CONF_ASA               = "asa"
CONF_POSTURE           = "posture"

POSTURE_STANDING = "standing"
POSTURE_SEATED   = "seated"
POSTURE_SUPINE   = "supine"
POSTURES         = [POSTURE_STANDING, POSTURE_SEATED, POSTURE_SUPINE]

DEFAULT_T_SOL   = 0.0
DEFAULT_F_SVV   = 0.0
DEFAULT_F_BES   = 0.0
DEFAULT_ASA     = 0.7
DEFAULT_POSTURE = POSTURE_STANDING
