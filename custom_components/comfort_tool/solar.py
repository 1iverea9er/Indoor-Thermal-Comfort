"""
Solar radiant correction for Mean Radiant Temperature.
ASHRAE 55 / CBE methodology.
"""
from __future__ import annotations
import math

# Projection factor tables fp[az_index][alt_index]
# az:  0..180 step 15° → 13 values
# alt: 0..90  step 15° → 7 values

_FP_STANDING = [
    [0.350, 0.350, 0.314, 0.258, 0.206, 0.144, 0.082],
    [0.342, 0.342, 0.310, 0.252, 0.200, 0.140, 0.082],
    [0.330, 0.330, 0.300, 0.244, 0.190, 0.132, 0.082],
    [0.310, 0.310, 0.275, 0.228, 0.175, 0.124, 0.082],
    [0.283, 0.283, 0.251, 0.208, 0.160, 0.114, 0.082],
    [0.252, 0.252, 0.228, 0.188, 0.150, 0.108, 0.082],
    [0.230, 0.230, 0.214, 0.180, 0.148, 0.108, 0.082],
    [0.242, 0.242, 0.222, 0.180, 0.153, 0.112, 0.082],
    [0.274, 0.274, 0.245, 0.203, 0.165, 0.116, 0.082],
    [0.304, 0.304, 0.270, 0.220, 0.174, 0.121, 0.082],
    [0.328, 0.328, 0.290, 0.234, 0.183, 0.125, 0.082],
    [0.344, 0.344, 0.304, 0.244, 0.190, 0.128, 0.082],
    [0.347, 0.347, 0.308, 0.246, 0.191, 0.128, 0.082],
]

_FP_SEATED = [
    [0.290, 0.324, 0.305, 0.303, 0.262, 0.224, 0.177],
    [0.292, 0.328, 0.294, 0.288, 0.268, 0.227, 0.177],
    [0.288, 0.332, 0.298, 0.290, 0.264, 0.222, 0.177],
    [0.274, 0.326, 0.294, 0.289, 0.252, 0.214, 0.177],
    [0.254, 0.308, 0.280, 0.276, 0.241, 0.202, 0.177],
    [0.230, 0.282, 0.262, 0.260, 0.233, 0.193, 0.177],
    [0.216, 0.260, 0.248, 0.244, 0.220, 0.186, 0.177],
    [0.234, 0.258, 0.236, 0.227, 0.208, 0.180, 0.177],
    [0.262, 0.260, 0.224, 0.208, 0.196, 0.176, 0.177],
    [0.280, 0.260, 0.210, 0.192, 0.184, 0.170, 0.177],
    [0.298, 0.256, 0.194, 0.174, 0.168, 0.168, 0.177],
    [0.306, 0.250, 0.180, 0.156, 0.156, 0.166, 0.177],
    [0.300, 0.240, 0.168, 0.152, 0.152, 0.164, 0.177],
]

_ALT_RANGE = [0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
_AZ_RANGE  = [0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0,
              105.0, 120.0, 135.0, 150.0, 165.0, 180.0]

_R_FLOOR = 0.6    # floor reflectance
_LW_ABS  = 0.95   # longwave absorptivity of body surface
_HR      = 6.0    # linearised radiation heat transfer coefficient, W/m²·K


def _interpolate_fp(alt: float, az: float, posture: str) -> float:
    """Bilinear interpolation of projection factor fp."""
    table = _FP_SEATED if posture == "seated" else _FP_STANDING

    alt = max(_ALT_RANGE[0], min(_ALT_RANGE[-1], alt))
    az  = max(_AZ_RANGE[0],  min(_AZ_RANGE[-1],  az))

    alti = next(i for i in range(len(_ALT_RANGE) - 1) if _ALT_RANGE[i + 1] >= alt)
    azi  = next(i for i in range(len(_AZ_RANGE)  - 1) if _AZ_RANGE[i + 1]  >= az)

    alt0, alt1 = _ALT_RANGE[alti], _ALT_RANGE[alti + 1]
    az0,  az1  = _AZ_RANGE[azi],   _AZ_RANGE[azi + 1]

    fp00 = table[azi][alti];     fp10 = table[azi][alti + 1]
    fp01 = table[azi + 1][alti]; fp11 = table[azi + 1][alti + 1]

    z0 = fp00 + (alt - alt0) * (fp10 - fp00) / (alt1 - alt0)
    z1 = fp01 + (alt - alt0) * (fp11 - fp01) / (alt1 - alt0)
    return z0 + (az - az0) * (z1 - z0) / (az1 - az0)


def _transform_supine(alt_deg: float, az_deg: float) -> tuple[float, float]:
    """Transform solar angles for supine posture."""
    az_diff_rad = math.radians(abs(az_deg - 90.0))
    alt_rad     = math.radians(alt_deg)
    alt_new = math.degrees(math.asin(math.sin(az_diff_rad) * math.cos(alt_rad)))
    az_new  = math.degrees(math.atan(math.sin(math.radians(az_deg)) *
                                     math.tan(math.radians(90.0 - alt_deg))))
    return alt_new, az_new


def calculate_erf(
    solar_altitude: float,
    solar_azimuth:  float,
    i_dir:          float,
    t_sol:          float,
    f_svv:          float,
    f_bes:          float,
    asa:            float,
    posture:        str = "standing",
) -> float:
    """Return Enhanced Radiant Field (ERF), W/m²."""

    solar_altitude = max(0.0, min(90.0, solar_altitude))
    
    alt, az = solar_altitude, solar_azimuth

    if posture == "supine":
        alt, az = _transform_supine(alt, az)

    fp    = _interpolate_fp(alt, az, posture)
    f_eff = 0.696 if posture == "seated" else 0.725
    i_diff = 0.2 * i_dir

    # use original altitude for floor-reflected component
    alt_rad = math.radians(solar_altitude)

    e_diff      = f_eff * f_svv * 0.5 * t_sol * i_diff
    e_direct    = f_eff * fp * t_sol * f_bes * i_dir
    e_reflected = f_eff * f_svv * 0.5 * t_sol * (i_dir * math.sin(alt_rad) + i_diff) * _R_FLOOR

    return (e_diff + e_direct + e_reflected) * (asa / _LW_ABS)


def calculate_delta_mrt(
    solar_altitude: float,
    solar_azimuth:  float,
    i_dir:          float,
    t_sol:          float,
    f_svv:          float,
    f_bes:          float,
    asa:            float,
    posture:        str = "standing",
) -> float:
    """Return solar ΔMrt correction to add to base MRT, °C."""
    f_eff = 0.696 if posture == "seated" else 0.725
    erf   = calculate_erf(solar_altitude, solar_azimuth,
                          i_dir, t_sol, f_svv, f_bes, asa, posture)
    return erf / (_HR * f_eff)