import logging

_LOGGER = logging.getLogger(__name__)

def calculate_thermal_comfort(ta, tr, va, rh, clo, met):
    _LOGGER.debug("Calculating thermal comfort with inputs: ta=%.2f, tr=%.2f, va=%.2f, rh=%.2f, clo=%.2f, met=%.2f", ta, tr, va, rh, clo, met)
    try:
        res = {
            "pmv": 0.0,  # placeholder
            "ppd": 0.0,  # placeholder
            "set": 0.0,  # placeholder
            "ce": 0.0,   # placeholder
            "ts": "Neutral"  # placeholder
        }
        _LOGGER.debug("Returning placeholder comfort results: %s", res)
        return res
    except Exception as e:
        _LOGGER.error("Error in placeholder thermal comfort calculation: %s", e)
        return {k: None for k in ["pmv", "ppd", "set", "ce", "ts"]}
