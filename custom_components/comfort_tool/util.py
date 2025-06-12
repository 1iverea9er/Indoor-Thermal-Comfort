import math
import logging

_LOGGER = logging.getLogger(__name__)

STATIC_URL = "/static"


def bisect(a, b, fn, epsilon, target):
    """
    Bisection root-finding algorithm for fn(x) == target.
    """
    while abs(b - a) > 2 * epsilon:
        midpoint = (b + a) / 2
        a_T = fn(a)
        b_T = fn(b)
        midpoint_T = fn(midpoint)
        if (a_T - target) * (midpoint_T - target) < 0:
            b = midpoint
        elif (b_T - target) * (midpoint_T - target) < 0:
            a = midpoint
        else:
            _LOGGER.warning("Bisection failed to bracket the root.")
            return -999
    return midpoint


def secant(a, b, fn, epsilon):
    """
    Secant method for root-finding: finds x such that fn(x) ≈ 0.
    """
    f1 = fn(a)
    if abs(f1) <= epsilon:
        return a

    f2 = fn(b)
    if abs(f2) <= epsilon:
        return b

    for _ in range(100):
        slope = (f2 - f1) / (b - a) if (b - a) != 0 else 0
        if slope == 0:
            _LOGGER.warning("Zero slope in secant method. Division by zero prevented.")
            return float('nan')
        c = b - f2 / slope
        c = max(0, min(c, 100))  # clamp to [0, 100]
        f3 = fn(c)
        if abs(f3) < epsilon:
            return c
        a, f1 = b, f2
        b, f2 = c, f3

    _LOGGER.warning("Secant method did not converge within 100 iterations.")
    return float('nan')


def get_sensation(pmv):
    """
    Returns thermal sensation description based on PMV value.
    """
    if pmv < -2.5:
        return "Cold"
    elif pmv < -1.5:
        return "Cool"
    elif pmv < -0.5:
        return "Slightly Cool"
    elif pmv < 0.5:
        return "Neutral"
    elif pmv < 1.5:
        return "Slightly Warm"
    elif pmv < 2.5:
        return "Warm"
    else:
        return "Hot"


def CtoF(x):
    return (x * 9) / 5 + 32


def FtoC(x):
    return (x - 32) * 5 / 9

def FindSaturatedVaporPressureTorr(T):
    """
    Calculates saturated vapor pressure (in Torr) at temperature T (°C)
    Based on equation: exp(18.6686 - 4030.183 / (T + 235.0))

    :param T: Temperature in degrees Celsius
    :return: Saturated vapor pressure in Torr
    """
    return math.exp(18.6686 - 4030.183 / (T + 235.0))
