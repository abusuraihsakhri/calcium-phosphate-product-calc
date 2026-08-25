#!/usr/bin/env python3
"""
Calciphylaxis risk model integrating the calcium-phosphate product with
published clinical risk factors.

Core chemistry:
    Ca x PO4 product (mg^2/dL^2) = serum calcium x serum phosphate
    Corrected calcium = measured Ca + 0.8 x (4.0 - albumin g/dL)
    KDIGO safety target: product < 55.5 mg^2/dL^2 (~4.52 mmol^2/L^2);
    historical ectopic-calcification risk rises above ~70 mg^2/dL^2

The logistic risk model combines the product with factors repeatedly
associated with calciphylaxis in dialysis cohorts (warfarin exposure,
hypoalbuminemia, obesity, diabetes, female sex, long dialysis vintage,
hypotensive episodes). Weights are heuristic syntheses of published odds
ratios, not a validated instrument; output supports triage, not diagnosis.
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List


KDIGO_TARGET_MG2DL2 = 55.5
HISTORICAL_RISK_THRESHOLD = 70.0
MG_TO_MMOL_FACTOR = 0.0805   # (mg^2/dL^2) -> (mmol^2/L^2)


@dataclass
class CalciphylaxisInputs:
    serum_calcium_mg_dl: float          # measured (total) calcium
    phosphate_mg_dl: float
    albumin_g_dl: float = 4.0
    warfarin_use: bool = False
    bmi: float = 25.0
    diabetes: bool = False
    female_sex: bool = False
    dialysis_vintage_years: float = 0.0
    recurrent_hypotension: bool = False
    active_infection: bool = False
    liver_disease: bool = False


def corrected_calcium(measured_ca: float, albumin: float) -> float:
    return round(measured_ca + 0.8 * (4.0 - albumin), 2)


def ca_po4_product(calcium_mg_dl: float, phosphate_mg_dl: float) -> Dict[str, float]:
    product = calcium_mg_dl * phosphate_mg_dl
    return {
        "product_mg2_dl2": round(product, 1),
        "product_mmol2_L2": round(product * MG_TO_MMOL_FACTOR, 2),
        "kdigo_target_met": product < KDIGO_TARGET_MG2DL2,
        "above_historical_risk_line": product >= HISTORICAL_RISK_THRESHOLD,
    }


INTERCEPT = -4.0


def predict_calciphylaxis_risk(x: CalciphylaxisInputs) -> Dict[str, Any]:
    ca_corr = corrected_calcium(x.serum_calcium_mg_dl, x.albumin_g_dl)
    chem = ca_po4_product(ca_corr, x.phosphate_mg_dl)

    terms: Dict[str, float] = {}
    terms["warfarin_exposure"] = 2.0 if x.warfarin_use else 0.0
    if chem["product_mg2_dl2"] >= HISTORICAL_RISK_THRESHOLD:
        terms["ca_x_p_product_high"] = 1.2
    elif chem["product_mg2_dl2"] >= KDIGO_TARGET_MG2DL2:
        terms["ca_x_p_product_above_target"] = 0.6
    else:
        terms["ca_x_p_product_in_target"] = 0.0
    if x.albumin_g_dl < 2.5:
        terms["severe_hypoalbuminemia"] = 1.5
    elif x.albumin_g_dl < 3.0:
        terms["hypoalbuminemia"] = 0.8
    else:
        terms["albumin_normal"] = 0.0
    terms["obesity_bmi_over_35"] = 0.8 if x.bmi > 35 else 0.0
    terms["diabetes"] = 0.7 if x.diabetes else 0.0
    terms["female_sex"] = 0.4 if x.female_sex else 0.0
    terms["dialysis_vintage_over_5y"] = 0.5 if x.dialysis_vintage_years > 5 else 0.0
    terms["recurrent_hypotension"] = 0.5 if x.recurrent_hypotension else 0.0
    terms["active_infection"] = 0.6 if x.active_infection else 0.0
    terms["liver_disease"] = 0.5 if x.liver_disease else 0.0

    logit = INTERCEPT + sum(terms.values())
    p = 1.0 / (1.0 + math.exp(-logit))

    if p < 0.05:
        tier, action = "low", "routine CKD-MBD management"
    elif p < 0.15:
        tier, action = "moderate", "avoid warfarin/calcium load; review binders and vitamin D"
    elif p < 0.30:
        tier, action = "high", "dermatology evaluation; consider sodium thiosulfate"
    else:
        tier, action = "very high", "urgent multidisciplinary calciphylaxis workup"

    drivers = sorted((kv for kv in terms.items() if kv[1] > 0),
                     key=lambda kv: -kv[1])
    return {
        "corrected_calcium_mg_dl": ca_corr,
        **chem,
        "probability_1y": round(p, 4),
        "risk_tier": tier,
        "recommended_action": action,
        "top_drivers": [k for k, _ in drivers],
        "model_note": "heuristic logistic synthesis of published associations",
    }


if __name__ == "__main__":
    cases = [
        ("stable HD patient", CalciphylaxisInputs(9.2, 4.6)),
        ("warfarinized, high CaP", CalciphylaxisInputs(10.4, 7.2, 2.8, True, 36,
                                                      True, True, 6.5, True, False)),
        ("mid-range", CalciphylaxisInputs(9.8, 5.8, 3.2, False, 31, True, False, 3)),
    ]
    for name, case in cases:
        r = predict_calciphylaxis_risk(case)
        print(f"\n=== {name} ===")
        print(f"Ca(corr) {r['corrected_calcium_mg_dl']} mg/dL | "
              f"Ca x P = {r['product_mg2_dl2']} mg2/dL2 "
              f"({r['product_mmol2_L2']} mmol2/L2)")
        print(f"KDIGO target met: {r['kdigo_target_met']} | "
              f"risk {r['probability_1y']:.1%} [{r['risk_tier']}]")
        print(f"action: {r['recommended_action']}")
