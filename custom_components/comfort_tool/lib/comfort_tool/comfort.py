# comfort.py (упрощенная версия)
def calculate_pmv(ta, tr, vel, rh, clo, met):
    return 0.5  # stub for demo

def calculate_ppd(pmv):
    return 100 - 95 * (2.71828 ** (-0.03353 * pmv ** 4 - 0.2179 * pmv ** 2))
