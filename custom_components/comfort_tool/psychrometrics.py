import math
from . import util

PROP = {
    "Patm": 101325.0,
    "CpAir": 1004.0,
    "CpWat": 4186.0,
    "CpVap": 1805.0,
    "Hfg": 2501000.0,
    "RAir": 287.055,
    "TKelConv": 273.15,
}

def satpress(tdb):
    tKel = tdb + PROP["TKelConv"]
    if tKel < 273.15:
        return math.exp(
            -5674.5359 / tKel
            + 6.3925247
            + tKel * (-0.009677843 + tKel * (0.00000062215701 + tKel * (0.0000000020747825 - 0.0000000000009484024 * tKel)))
            + 4.1635019 * math.log(tKel)
        )
    else:
        return math.exp(
            -5800.2206 / tKel
            + 1.3914993
            + tKel * (-0.048640239 + tKel * (0.000041764768 + tKel * -0.000000014452093))
            + 6.5459673 * math.log(tKel)
        )

def humratio(p_atm, pw):
    return (0.62198 * pw) / (p_atm - pw)

def relhum(patm, psat, humRatio):
    pw = (patm * humRatio) / (0.62198 + humRatio)
    return pw / psat

def enthalpy(tdb, w):
    return PROP["CpAir"] * tdb + w * (PROP["Hfg"] + PROP["CpVap"] * tdb)

def rhodry(tdb, w):
    pAir = (0.62198 * PROP["Patm"]) / (0.62198 + w)
    return pAir / PROP["RAir"] / (tdb + PROP["TKelConv"])

def rhomoist(rhodry, w):
    return rhodry * (1 + w)

def enthsat(tdb):
    psat = satpress(tdb)
    w = humratio(PROP["Patm"], psat)
    return enthalpy(tdb, w)

def dewpoint(w):
    pw = (PROP["Patm"] * w) / (0.62198 + w)
    return sattemp(pw)

def sattemp(p):
    fn = lambda t: p - satpress(t)
    return util.bisect(0, 500, fn, 0.0001, 0)

def tairsat(hsat):
    fn = lambda t: hsat - enthsat(t)
    return util.bisect(0, 1000, fn, 0.01, 0)

def wetbulb(tdb, w):
    def fn(t):
        psat_star = satpress(t)
        w_star = humratio(PROP["Patm"], psat_star)
        newW = ((PROP["Hfg"] - PROP["CpWat"] - PROP["CpVap"] * t) * w_star - PROP["CpAir"] * (tdb - t)) / \
               (PROP["Hfg"] + PROP["CpVap"] * tdb - PROP["CpWat"] * t)
        return w - newW
    return util.bisect(-100, 200, fn, 0.01, 0)

def tdb_rh(tdb, rh):
    psat = satpress(tdb)
    vappress = (rh / 100) * psat
    w = humratio(PROP["Patm"], vappress)
    return {
        "rh": rh,
        "vappress": vappress,
        "w": w,
        "wetbulb": wetbulb(tdb, w),
        "dewpoint": dewpoint(w),
    }

def tdb_twb(tdb, twb):
    psat = satpress(twb)
    wstar = humratio(PROP["Patm"], psat)
    w = ((PROP["Hfg"] + (PROP["CpVap"] - PROP["CpWat"]) * twb) * wstar - PROP["CpAir"] * (tdb - twb)) / \
        (PROP["Hfg"] + PROP["CpVap"] * tdb - PROP["CpWat"] * twb)
    psat = satpress(tdb)
    rh = 100 * relhum(PROP["Patm"], psat, w)
    return {
        "wetbulb": twb,
        "w": w,
        "rh": rh,
        "dewpoint": dewpoint(w),
        "vappress": (rh / 100) * psat,
    }

def tdb_w(tdb, w):
    psat = satpress(tdb)
    rh = 100 * relhum(PROP["Patm"], psat, w)
    return {
        "w": w,
        "rh": rh if rh <= 100 else float('nan'),
        "wetbulb": wetbulb(tdb, w),
        "dewpoint": dewpoint(w),
        "vappress": (rh / 100) * psat,
    }

def tdb_dewpoint(tdb, dewpoint_temp):
    fn = lambda w: dewpoint_temp - dewpoint(w)
    w = util.bisect(0.00001, 0.2, fn, 0.0001, 0)
    return tdb_w(tdb, w)

def tdb_vappress(tdb, vappress):
    psat = satpress(tdb)
    rh = (100 * vappress) / psat
    return tdb_rh(tdb, rh)

def convert(x, tdb, origin, target):
    converters = {
        "rh": tdb_rh,
        "wetbulb": tdb_twb,
        "w": tdb_w,
        "dewpoint": tdb_dewpoint,
        "vappress": tdb_vappress,
    }
    a = converters[origin](tdb, x)
    return a[target]

def globetemp(ta, vel, tglobe, diameter, emissivity):
    return (
        (tglobe + 273) ** 4 +
        ((1.1 * 10**8 * vel**0.6) / (emissivity * diameter**0.4)) * (tglobe - ta)
    ) ** 0.25 - 273
