import logging
from pythermalcomfort.models import pmv_ppd, set_tmp, cooling_effect

_LOGGER = logging.getLogger(__name__)

def calculate_thermal_comfort(ta, tr, va, rh, clo, met):
    _LOGGER.debug("Calculating thermal comfort with inputs: ta=%.2f, tr=%.2f, va=%.2f, rh=%.2f, clo=%.2f, met=%.2f", ta, tr, va, rh, clo, met)
    res = {}
    try:
        ppd_data = pmv_ppd(tdb=ta, tr=tr, vr=va, rh=rh, clo=clo, met=met)
        res["pmv"] = round(ppd_data.get("pmv"), 2)
        res["ppd"] = round(ppd_data.get("ppd"), 1)

        set_data = set_tmp(tdb=ta, tr=tr, vr=va, rh=rh, clo=clo, met=met)
        res["set"] = round(set_data.get("set"), 2)

        ce_data = cooling_effect(tdb=ta, tr=tr, vr=va, rh=rh, clo=clo, met=met, v_relative=0.3)
        res["ce"] = round(ce_data.get("ce"), 2)

        pmv = res["pmv"]
        if pmv < -2.5:
            ts = "Very Cold"
        elif pmv < -1.5:
            ts = "Cold"
        elif pmv < -0.5:
            ts = "Cool"
        elif pmv < 0.5:
            ts = "Neutral"
        elif pmv < 1.5:
            ts = "Warm"
        elif pmv < 2.5:
            ts = "Hot"
        else:
            ts = "Very Hot"

        res["ts"] = ts

        _LOGGER.debug("Thermal comfort calculation result: %s", res)
    except Exception as e:
        _LOGGER.error("Error in thermal comfort calculation: %s", e)
        res = {k: None for k in ["pmv", "ppd", "set", "ce", "ts"]}

    return res
