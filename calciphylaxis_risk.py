#!/usr/bin/env python3
"""Calciphylaxis context helpers.

This module lists supplied associations only. It does not estimate an individual
probability, assign a clinical risk tier, or recommend treatment.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

MG_TO_MMOL_FACTOR = 0.08056
HISTORICAL_KDOQI_PRODUCT_LIMIT = 55.0


@dataclass
class CalciphylaxisInputs:
    serum_calcium_mg_dl: float
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


def ca_po4_product(calcium_mg_dl: float, phosphate_mg_dl: float) -> Dict[str, Any]:
    product = calcium_mg_dl * phosphate_mg_dl
    return {
        "product_mg2_dl2": round(product, 2),
        "product_mmol2_L2": round(product * MG_TO_MMOL_FACTOR, 2),
        "historical_kdoqi_below_55": product < HISTORICAL_KDOQI_PRODUCT_LIMIT,
        "context_note": (
            "The 55 mg2/dL2 threshold is historical KDOQI context. "
            "KDIGO 2017 advises using individual calcium and phosphate values together."
        ),
    }


def predict_calciphylaxis_risk(x: CalciphylaxisInputs) -> Dict[str, Any]:
    """Compatibility entry point that deliberately does not calculate probability."""
    ca_corr = corrected_calcium(x.serum_calcium_mg_dl, x.albumin_g_dl)
    chemistry = ca_po4_product(ca_corr, x.phosphate_mg_dl)

    factors: List[str] = []
    if x.warfarin_use:
        factors.append("warfarin_exposure")
    if x.albumin_g_dl < 3.5:
        factors.append("hypoalbuminemia")
    if x.bmi >= 30:
        factors.append("obesity")
    if x.diabetes:
        factors.append("diabetes")
    if x.female_sex:
        factors.append("female_sex")
    if x.dialysis_vintage_years >= 3:
        factors.append("dialysis_vintage_ge_3y")
    if x.recurrent_hypotension:
        factors.append("recurrent_hypotension")
    if x.active_infection:
        factors.append("active_infection")
    if x.liver_disease:
        factors.append("liver_disease")

    return {
        "corrected_calcium_mg_dl": ca_corr,
        **chemistry,
        "probability_1y": None,
        "risk_tier": "not_estimated",
        "recommended_action": None,
        "top_drivers": factors,
        "model_note": (
            "No validated individual calciphylaxis probability is calculated. "
            "Factors are listed for context only."
        ),
    }


if __name__ == "__main__":
    result = predict_calciphylaxis_risk(CalciphylaxisInputs(9.2, 4.6))
    print(result)
