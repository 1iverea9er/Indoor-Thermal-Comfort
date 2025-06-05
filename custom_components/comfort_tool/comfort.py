
from pythermalcomfort.models import pmv_ppd, cooling_effect

def calculate_thermal_comfort(ta, tr, va, rh, clo, met):
    try:
        result = pmv_ppd(tdb=ta, tr=tr, vr=va, rh=rh, clo=clo, met=met)
        ce = cooling_effect(tdb=ta, tr=tr, vr=va, rh=rh, clo=clo, met=met)
        return {
            "pmv": result["pmv"],
            "ppd": result["ppd"],
            "set": result.get("set", None),
            "ce": ce["ce"],
            "sensation": result.get("thermal_sensation", None)
        }
    except Exception as e:
        return {
            "error": str(e)
        }
