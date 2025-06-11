import logging

_LOGGER = logging.getLogger(__name__)

def calculate_thermal_comfort(ta, tr, va, rh, clo, met):
    _LOGGER.debug("Calculating (approximate) thermal comfort with inputs: ta=%.2f, tr=%.2f, va=%.2f, rh=%.2f, clo=%.2f, met=%.2f", ta, tr, va, rh, clo, met)
    res = {}
    try:
        # Приближенные эвристические расчёты, не точные модели
        pmv = 0.303 * pow(2.718, -0.036 * met) + 0.028 * (met - clo) * (ta - 22)
        pmv = max(-3, min(3, pmv))
        ppd = max(5, min(100, 100 - 95 * pow(2.718, (-0.03353 * pmv ** 4 - 0.2179 * pmv ** 2))))

        # Псевдо-SET и CE (приближённые оценки)
        set_temp = ta + (tr - ta) * 0.5 + (va * 1.5)
        ce = (va * 2.5) - (clo * 2)

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

        res = {
            "pmv": round(pmv, 2),
            "ppd": round(ppd, 1),
            "set": round(set_temp, 2),
            "ce": round(ce, 2),
            "ts": ts
        }

        _LOGGER.debug("Approximate thermal comfort result: %s", res)

    except Exception as e:
        _LOGGER.error("Error in comfort calculation: %s", e)
        res = {k: None for k in ["pmv", "ppd", "set", "ce", "ts"]}

    return res
