import logging
import math
from . import util
from . import psychrometrics as psy


_LOGGER = logging.getLogger(__name__)

def relative_air_speed(v: float, met: float) -> float:
    """Корректировка скорости воздуха в зависимости от метаболизма."""
    if met > 1:
        return v + 0.3 * (met - 1)
    return v


def dynamic_clothing(clo: float, met: float) -> float:
    """Динамическая корректировка одежды в зависимости от метаболизма."""
    if met > 1.2:
        return clo * (0.6 + 0.4 / met)
    return clo


STILL_AIR_THRESHOLD = 0.1  # m/s


def between(x: float, left: float, right: float) -> bool:
    """Проверка, находится ли x в пределах [left, right]."""
    return left <= x <= right

def calculate_thermal_comfort(ta, tr, va, rh, clo, met, wme=0, body_position="standing"):
    _LOGGER.debug(
        "Calculating thermal comfort (with Pierce SET) using inputs: ta=%.2f, tr=%.2f, va=%.2f, rh=%.2f, clo=%.2f, met=%.2f",
        ta, tr, va, rh, clo, met
    )

    res = {}
    try:
        # Точный расчёт SET по модели Pierce
        set_result = pierce_set(
            ta=ta,
            tr=tr,
            vel=va,
            rh=rh,
            met=met,
            clo=clo,
            wme=wme,
            round_output=True,
            standard_effective_temperature_mode=True,
            posture_angle=90,
            body_position=body_position
        )

        set_temp = set_result["set"]

        # Упрощённая оценка PMV
        pmv = 0.303 * pow(2.718, -0.036 * met) + 0.028 * (met - clo) * (ta - 22)
        pmv = max(-3, min(3, pmv))
        ppd = max(5, min(100, 100 - 95 * pow(2.718, (-0.03353 * pmv ** 4 - 0.2179 * pmv ** 2))))

        # Классификация теплового состояния по шкале PMV
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

        # Точный расчёт Cooling Effect
        ce = round(
            cooling_effect(
                ta=ta,
                tr=tr,
                vel=va,
                rh=rh,
                met=met,
                clo=clo,
                wme=wme,
                body_position=body_position
            ), 2
        )

        res = {
            "pmv": round(pmv, 2),
            "ppd": round(ppd, 1),
            "set": set_temp,
            "ce": ce,
            "ts": ts
        }

        _LOGGER.debug("Thermal comfort result: %s", res)

    except Exception as e:
        _LOGGER.error("Error in comfort calculation: %s", e)
        res = {k: None for k in ["pmv", "ppd", "set", "ce", "ts"]}

    return res



def cooling_effect(ta, tr, vel, rh, met, clo, wme, body_position="standing"):
    """
    Расчет охлаждающего эффекта (Cooling Effect) по модели Pierce SET.
    
    :param ta: Температура воздуха (°C)
    :param tr: Температура излучения (°C)
    :param vel: Скорость воздуха (м/с)
    :param rh: Относительная влажность (%)
    :param met: Метаболизм (met)
    :param clo: Одежда (clo)
    :param wme: Внешняя работа (Вт/м²)
    :param body_position: Положение тела: 'sitting' или 'standing'
    :return: Cooling Effect (°C)
    """
    ce_l = 0.0
    ce_r = 40.0
    eps = 0.001

    if vel <= 0.1:
        return 0.0

    set_ref = pierce_set(
        ta, tr, vel, rh, met, clo, wme,
        standard_effective_temperature_mode=True,
        calculate_ce=False,
        posture_angle=90,
        body_position=body_position
    )["set"]

    def fn(_ce):
        set_still = pierce_set(
            ta - _ce,
            tr - _ce,
            STILL_AIR_THRESHOLD,
            rh,
            met,
            clo,
            wme,
            standard_effective_temperature_mode=True,
            calculate_ce=False,
            posture_angle=90,
            body_position=body_position
        )["set"]
        return set_ref - set_still

    # Численное решение методом секущих с подстраховкой бисекцией
    ce = secant(fn, ce_l, ce_r, eps)

    if ce is None or math.isnan(ce):
        ce = bisect(fn, ce_l, ce_r, eps, max_iter=100)

    return max(0.0, ce)


# Вспомогательные численные методы
def secant(f, x0, x1, tol=1e-6, max_iter=100):
    for _ in range(max_iter):
        fx0 = f(x0)
        fx1 = f(x1)
        if abs(fx1 - fx0) < 1e-12:
            return None
        x2 = x1 - fx1 * (x1 - x0) / (fx1 - fx0)
        if abs(x2 - x1) < tol:
            return x2
        x0, x1 = x1, x2
    return None

def bisect(f, a, b, tol=1e-6, max_iter=100):
    fa = f(a)
    fb = f(b)
    if fa * fb > 0:
        return None
    for _ in range(max_iter):
        c = (a + b) / 2.0
        fc = f(c)
        if abs(fc) < tol or (b - a) / 2 < tol:
            return c
        if fc * fa < 0:
            b = c
            fb = fc
        else:
            a = c
            fa = fc
    return (a + b) / 2.0




def pierce_set(
    ta,
    tr,
    vel,
    rh,
    met,
    clo,
    wme=0,
    round_output=False,
    calculate_ce=False,
    max_skin_blood_flow=90,
    body_position="sitting"
):
    SBC = 5.6697e-8  # Stefan-Boltzmann constant
    DELTA = 0.0001
    MetFactor = 58.2
    BodyWeight = 69.9
    BodySurfaceArea = 1.8258
    KClo = 0.25
    CSW = 170
    CDil = 120
    CStr = 0.5
    TempSkinNeutral = 33.7
    TempCoreNeutral = 36.8
    TempBodyNeutral = 0.1 * TempSkinNeutral + 0.9 * TempCoreNeutral
    SkinBloodFlowNeutral = 6.3
    VaporPressure = rh * util.FindSaturatedVaporPressureTorr(ta) / 100
    AirSpeed = max(vel, 0.1)
    p = psy.PROP["Patm"] / 1000
    PressureInAtmospheres = p * 0.009869
    LTime = 60.0
    RCl = 0.155 * clo
    FACL = 1.0 + 0.15 * clo
    LR = 2.2 / PressureInAtmospheres
    RM = met * MetFactor
    M = RM

    if clo <= 0:
        WCRIT = 0.38 * AirSpeed**-0.29
        ICL = 1.0
    else:
        WCRIT = 0.59 * AirSpeed**-0.08
        ICL = 0.45

    heatTransferConvMet = (
        3.0 if met < 0.85 else 5.66 * (met - 0.85) ** 0.39
    )
    CHC = max(3.0 * PressureInAtmospheres**0.53, 8.600001 * (AirSpeed * PressureInAtmospheres)**0.53)
    if not calculate_ce:
        CHC = max(CHC, heatTransferConvMet)

    CHR = 4.7
    CTC = CHR + CHC
    RA = 1.0 / (FACL * CTC)
    TOP = (CHR * tr + CHC * ta) / CTC
    TempSkin = TempSkinNeutral
    TempCore = TempCoreNeutral
    SkinBloodFlow = SkinBloodFlowNeutral
    ALFA = 0.1
    ESK = 0.1 * met
    TCL = TOP + (TempSkin - TOP) / (CTC * (RA + RCl))
    flag = True

    ExcBloodFlow = False
    ExcRegulatorySweating = False
    ExcCriticalWettedness = False

    for _ in range(int(LTime)):
        while True:
            TCL_OLD = TCL
            if body_position == "sitting":
                CHR = 4.0 * 0.95 * SBC * ((TCL + tr) / 2.0 + 273.15) ** 3 * 0.7
            else:
                CHR = 4.0 * 0.95 * SBC * ((TCL + tr) / 2.0 + 273.15) ** 3 * 0.73
            CTC = CHR + CHC
            RA = 1.0 / (FACL * CTC)
            TOP = (CHR * tr + CHC * ta) / CTC
            TCL = (RA * TempSkin + RCl * TOP) / (RA + RCl)
            if abs(TCL - TCL_OLD) <= 0.01:
                break

        DRY = (TempSkin - TOP) / (RA + RCl)
        HFCS = (TempCore - TempSkin) * (5.28 + 1.163 * SkinBloodFlow)
        ERES = 0.0023 * M * (44.0 - VaporPressure)
        CRES = 0.0014 * M * (34.0 - ta)
        SCR = M - HFCS - ERES - CRES - wme
        SSK = HFCS - DRY - ESK
        TCSK = 0.97 * ALFA * BodyWeight
        TCCR = 0.97 * (1 - ALFA) * BodyWeight
        DTSK = (SSK * BodySurfaceArea) / (TCSK * 60.0)
        DTCR = (SCR * BodySurfaceArea) / (TCCR * 60.0)
        TempSkin += DTSK
        TempCore += DTCR
        TB = ALFA * TempSkin + (1 - ALFA) * TempCore

        SKSIG = TempSkin - TempSkinNeutral
        COLDS = max(0.0, -SKSIG)
        WARMS = max(0.0, SKSIG)
        CRSIG = TempCore - TempCoreNeutral
        COLDC = max(0.0, -CRSIG)
        WARMC = max(0.0, CRSIG)
        BDSIG = TB - TempBodyNeutral
        WARMB = max(0.0, BDSIG)

        SkinBloodFlow = (SkinBloodFlowNeutral + CDil * WARMC) / (1 + CStr * COLDS)
        if SkinBloodFlow > max_skin_blood_flow:
            SkinBloodFlow = max_skin_blood_flow
            ExcBloodFlow = True
        if SkinBloodFlow < 0.5:
            SkinBloodFlow = 0.5

        REGSW = CSW * WARMB * math.exp(WARMS / 10.7)
        if REGSW > 500:
            REGSW = 500
            ExcRegulatorySweating = True

        ERSW = 0.68 * REGSW
        REA = 1.0 / (LR * FACL * CHC)
        RECL = RCl / (LR * ICL)
        EMAX = (
            util.FindSaturatedVaporPressureTorr(TempSkin) - VaporPressure
        ) / (REA + RECL)
        PRSW = ERSW / EMAX if EMAX > 0 else 0
        PWET = 0.06 + 0.94 * PRSW
        EDIF = PWET * EMAX - ERSW if EMAX > 0 else 0

        if PWET > WCRIT:
            PWET = WCRIT
            PRSW = WCRIT / 0.94
            ERSW = PRSW * EMAX
            EDIF = 0.06 * (1.0 - PRSW) * EMAX
            ExcCriticalWettedness = True

        if EMAX < 0:
            EDIF = 0
            ERSW = 0
            PWET = WCRIT
            PRSW = WCRIT

        ESK = ERSW + EDIF
        MSHIV = 19.4 * COLDS * COLDC
        M = RM + MSHIV
        ALFA = 0.0417737 + 0.7451833 / (SkinBloodFlow + 0.585417)

    HSK = DRY + ESK
    W = PWET
    PSSK = util.FindSaturatedVaporPressureTorr(TempSkin)
    CHRS = CHR
    CHCS = max(3.0, 3.0 * PressureInAtmospheres**0.53)
    if not calculate_ce and met > 0.85:
        CHCS = max(CHCS, heatTransferConvMet)
    CTCS = CHCS + CHRS

    RCLOS = 1.52 / (met - wme / MetFactor + 0.6944) - 0.1835
    RCLS = 0.155 * RCLOS
    FACLS = 1.0 + KClo * RCLOS
    FCLS = 1.0 / (1.0 + 0.155 * FACLS * CTCS * RCLOS)
    IMS = 0.45
    ICLS = ((IMS * CHCS) / CTCS * (1 - FCLS)) / (CHCS / CTCS - FCLS * IMS)
    RAS = 1.0 / (FACLS * CTCS)
    REAS = 1.0 / (LR * FACLS * CHCS)
    RECLS = RCLS / (LR * ICLS)
    HD_S = 1.0 / (RAS + RCLS)
    HE_S = 1.0 / (REAS + RECLS)

    X_OLD = TempSkin - HSK / HD_S
    dx = 100.0
    while abs(dx) > 0.01:
        ERR1 = HSK - HD_S * (TempSkin - X_OLD) - W * HE_S * (PSSK - 0.5 * util.FindSaturatedVaporPressureTorr(X_OLD))
        ERR2 = HSK - HD_S * (TempSkin - (X_OLD + DELTA)) - W * HE_S * (PSSK - 0.5 * util.FindSaturatedVaporPressureTorr(X_OLD + DELTA))
        _set = X_OLD - (DELTA * ERR1) / (ERR2 - ERR1)
        dx = _set - X_OLD
        X_OLD = _set

    return {
        "set": round(_set, 1) if round_output else _set,
        "t_skin": TempSkin,
        "t_core": TempCore,
        "t_clo": TCL,
        "t_mean_body": TB,
        "q_tot_evap": ESK,
        "q_sweat_evap": ERSW,
        "q_vap_diff": EDIF,
        "q_tot_sensible": DRY,
        "q_tot_skin": HSK,
        "q_resp": ERES,
        "skin_wet": PWET * 100,
        "thermal_strain": any([ExcRegulatorySweating, ExcBloodFlow, ExcCriticalWettedness])
    }
