def calculate_thermal_comfort(ta, tr, va, rh, clo, met):
    """
    Простейшая модель комфорта. Можно заменить реальным расчётом PMV/PPD или другим.
    """
    try:
        return round((ta + tr + va + rh + clo + met) / 6, 2)
    except Exception:
        return None
