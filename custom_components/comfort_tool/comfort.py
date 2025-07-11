import logging
import math
from . import util
from . import psychrometrics as psy


_LOGGER = logging.getLogger(__name__)

def relative_air_speed(v: float, met: float) -> float:
    """Adjust air speed based on metabolic rate.

    When the metabolic rate exceeds 1.0 met, the relative air speed is increased
    to account for increased convection due to body movement.
    """
    if met > 1:
        return v + 0.3 * (met - 1)
    return v


def dynamic_clothing(clo: float, met: float) -> float:
    """Adjust clothing insulation dynamically based on metabolic rate.

    At higher activity levels (met > 1.2), the effective clothing insulation is reduced
    to reflect heat loss due to increased movement and ventilation.
    """
    if met > 1.2:
        return clo * (0.6 + 0.4 / met)
    return clo


STILL_AIR_THRESHOLD = 0.1  # m/s



def calculate_thermal_comfort(ta, tr, va, rh, clo, met, wme=0):
    _LOGGER.debug(
        "Calculating thermal comfort using pmv_elevated_airspeed with inputs: ta=%.2f, tr=%.2f, va=%.2f, rh=%.2f, clo=%.2f, met=%.2f",
        ta, tr, va, rh, clo, met
    )

    res = {}
    try:
        # Full comfort model: includes PMV, PPD, CE, SET based on elevated airspeed logic
        comfort = pmv_elevated_airspeed(
            ta=ta,
            tr=tr,
            vel=va,
            rh=rh,
            met=met,
            clo=clo,
            wme=wme
        )

        pmv_val = comfort["pmv"]
        ppd_val = comfort["ppd"]
        set_temp = comfort["set"]
        ce = comfort["cooling_effect"]

        # Determine thermal sensation category
        ts = get_sensation_by_class(pmv_val, "B")

        res = {
            "pmv": round(pmv_val, 2),
            "ppd": round(ppd_val, 0),
            "set": round(set_temp, 1),
            "ce": round(ce, 1),
            "ts": ts
        }

        _LOGGER.debug("Thermal comfort result: %s", res)

    except Exception as e:
        _LOGGER.error("Error in comfort calculation: %s", e)
        res = {k: None for k in ["pmv", "ppd", "set", "ce", "ts"]}

    return res


def pmv_elevated_airspeed(ta, tr, vel, rh, met, clo, wme=0):
    """
    Returns comfort parameters accounting for elevated air speed effects.

    Parameters:
    - ta: air temperature (°C)
    - tr: mean radiant temperature (°C)
    - vel: air speed (m/s)
    - rh: relative humidity (%)
    - met: metabolic rate (met)
    - clo: clothing insulation (clo)
    - wme: external work (met), default is 0

    Returns:
    - dict with the following keys:
        "pmv": Predicted Mean Vote,
        "ppd": Predicted Percentage Dissatisfied,
        "set": Standard Effective Temperature,
        "ta_adj": adjusted air temperature after cooling effect,
        "tr_adj": adjusted mean radiant temperature after cooling effect,
        "cooling_effect": calculated cooling effect (°C)
    """
    result = {}

    # Compute relative air speed based on metabolic rate
    rel_vel = relative_air_speed(vel, met)

    # Compute dynamic clothing insulation
    dyn_clo = dynamic_clothing(clo, met)

    # Compute cooling effect from elevated air speed
    ce = cooling_effect(ta, tr, rel_vel, rh, met, dyn_clo)

    # Use adjusted or original temperatures depending on velocity and cooling effect
    if rel_vel <= 0.1 or ce == 0:
        # No significant cooling, use original conditions
        pmv_result = pmv(ta, tr, rel_vel, rh, met, dyn_clo, wme)
        ce = 0
        ta_adj = ta
        tr_adj = tr
    else:
        # Adjust temperatures for elevated air speed cooling effect
        pmv_result = pmv(ta - ce, tr - ce, STILL_AIR_THRESHOLD, rh, met, dyn_clo, wme)
        ta_adj = ta - ce
        tr_adj = tr - ce

    # Compute accurate SET using the original input parameters
    set_val = pierce_set(ta, tr, vel, rh, met, clo, wme)["set"]

    # Return all comfort parameters
    result["pmv"] = pmv_result["pmv"]
    result["ppd"] = pmv_result["ppd"]
    result["set"] = set_val
    result["ta_adj"] = ta_adj
    result["tr_adj"] = tr_adj
    result["cooling_effect"] = ce

    return result



def pmv(ta, tr, vel, rh, met, clo, wme=0):
    """
    PMV (Predicted Mean Vote) and PPD (Predicted Percentage Dissatisfied) calculation.

    Parameters:
        ta : float - air temperature (°C)
        tr : float - mean radiant temperature (°C)
        vel : float - relative air speed (m/s)
        rh : float - relative humidity (%)
        met : float - metabolic rate (met)
        clo : float - clothing insulation (clo)
        wme : float - external work (met), default is 0

    Returns:
        dict with keys: pmv, ppd, hl1 to hl6
    """
    pa = rh * 10 * math.exp(16.6536 - 4030.183 / (ta + 235))
    icl = 0.155 * clo
    m = met * 58.15
    w = wme * 58.15
    mw = m - w

    if icl <= 0.078:
        fcl = 1 + 1.29 * icl
    else:
        fcl = 1.05 + 0.645 * icl

    hcf = 12.1 * math.sqrt(vel)
    taa = ta + 273
    tra = tr + 273
    t_cla = taa + (35.5 - ta) / (3.5 * icl + 0.1)

    p1 = icl * fcl
    p2 = p1 * 3.96
    p3 = p1 * 100
    p4 = p1 * taa
    p5 = 308.7 - 0.028 * mw + p2 * ((tra / 100) ** 4)

    xn = t_cla / 100
    xf = t_cla / 50
    eps = 0.00015
    n = 0

    while abs(xn - xf) > eps:
        xf = (xf + xn) / 2
        hcn = 2.38 * abs(100.0 * xf - taa) ** 0.25
        hc = max(hcf, hcn)
        xn = (p5 + p4 * hc - p2 * (xf ** 4)) / (100 + p3 * hc)
        n += 1
        if n > 150:
            raise RuntimeError("Max iterations exceeded in PMV calculation")

    tcl = 100 * xn - 273

    hl1 = 3.05 * 0.001 * (5733 - 6.99 * mw - pa)
    hl2 = 0.42 * (mw - 58.15) if mw > 58.15 else 0
    hl3 = 1.7e-5 * m * (5867 - pa)
    hl4 = 0.0014 * m * (34 - ta)
    hl5 = 3.96 * fcl * ((xn ** 4) - (tra / 100) ** 4)
    hl6 = fcl * hc * (tcl - ta)

    ts = 0.303 * math.exp(-0.036 * m) + 0.028
    pmv = ts * (mw - hl1 - hl2 - hl3 - hl4 - hl5 - hl6)
    ppd = 100.0 - 95.0 * math.exp(-0.03353 * pmv ** 4 - 0.2179 * pmv ** 2)

    return {
        "pmv": pmv,
        "ppd": ppd,
        "hl1": hl1,
        "hl2": hl2,
        "hl3": hl3,
        "hl4": hl4,
        "hl5": hl5,
        "hl6": hl6
    }



def cooling_effect(ta, tr, vel, rh, met, clo, body_position="standing"):
    """
    Calculates the Cooling Effect (CE) — the difference in SET between current conditions
    and still air conditions (velocity = 0.1 m/s).
    """
    if vel <= 0.1:
        return 0.0

    ce_l = 0.0
    ce_r = 40.0
    eps = 0.001  # accuracy threshold

    # Reference SET at current air speed
    set_ref = pierce_set(
        ta=ta,
        tr=tr,
        vel=vel,
        rh=rh,
        met=met,
        clo=clo,
        wme=0,
        round_output=False,
        calculate_ce=True,
        max_skin_blood_flow=90,
        body_position=body_position
    )["set"]

    # Target function: difference in SET with reduced temperature and still air
    def fn(ce):
        set_still = pierce_set(
            ta=ta - ce,
            tr=tr - ce,
            vel=STILL_AIR_THRESHOLD,
            rh=rh,
            met=met,
            clo=clo,
            wme=0,
            round_output=False,
            calculate_ce=True,
            max_skin_blood_flow=90,
            body_position=body_position
        )["set"]
        return set_ref - set_still

    # Use secant method to solve for CE
    try:
        ce = util.secant(ce_l, ce_r, fn, eps)
    except ValueError:
        # If secant method fails, fall back to bisection method
        ce = util.bisect(ce_l, ce_r, fn, eps, 0)

    return round(max(0.0, ce), 2)







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


def operative_temperature(ta, tr, va):
    """
    Calculates the operative temperature using heat transfer coefficients.

    Parameters:
    - ta: air temperature (°C)
    - tr: mean radiant temperature (°C)
    - va: air speed (m/s)

    Returns:
    - to: operative temperature (°C)
    """

    # Fixed radiative heat transfer coefficient (typical indoor value)
    hr = 4.7

    # Convective heat transfer coefficient based on Mitchell's formula
    hc = max(3.1, 8.3 * va ** 0.6)

    # Operative temperature formula:
    # weighted average of air temperature and radiant temperature
    to = (hr * tr + hc * ta) / (hr + hc)

    return to


def get_sensation_by_class(pmv: float, comfort_class: str = "B") -> str:
    """
    Returns thermal sensation based on PMV value and thermal environment class (A, B, C),
    using adjusted sensation ranges according to ISO 7730:2005 Appendix A.

    Parameters:
        pmv (float): Predicted Mean Vote value.
        comfort_class (str): Thermal comfort class: "A", "B", or "C".

    Returns:
        str: Thermal sensation description.
    """
    # Define half-range of neutrality for each class
    class_ranges = {
        "A": 0.2,
        "B": 0.5,
        "C": 0.7
    }

    # Validate and get the neutral range for the class
    neutral_range = class_ranges.get(comfort_class.upper(), 0.5)  # default to class B if invalid

    # Define boundaries based on neutral_range as a scaling factor
    # e.g., for class A (±0.2): boundaries = ±0.2, ±2×0.2, ±3×0.2, etc.
    thresholds = [
        (-3 * neutral_range, "Cold"),
        (-2 * neutral_range, "Cool"),
        (-1 * neutral_range, "Slightly Cool"),
        (neutral_range, "Neutral"),
        (2 * neutral_range, "Slightly Warm"),
        (3 * neutral_range, "Warm"),
    ]

    # Classify PMV based on the thresholds
    for threshold, label in thresholds:
        if pmv < threshold:
            return label

    return "Hot"
