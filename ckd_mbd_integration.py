#!/usr/bin/env python3
"""CKD-MBD descriptive integration helpers.

The output is descriptive and does not diagnose CKD from eGFR alone or generate
medication recommendations.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class CKDMBDParameters:
    egfr: float
    calcium_mg_dl: float
    phosphate_mg_dl: float
    pth_pg_ml: float
    vitamin_d_ng_ml: float
    alkaline_phosphatase_u_l: float = 0.0
    bicarbonate_meq_l: float = 24.0


def _gfr_category(egfr: float) -> str:
    if egfr >= 90:
        return "G1"
    if egfr >= 60:
        return "G2"
    if egfr >= 45:
        return "G3a"
    if egfr >= 30:
        return "G3b"
    if egfr >= 15:
        return "G4"
    return "G5"


def assess_ckd_mbd(params: CKDMBDParameters) -> Dict[str, Any]:
    if params.egfr < 0:
        raise ValueError("eGFR must be non-negative")
    if params.calcium_mg_dl <= 0 or params.phosphate_mg_dl <= 0:
        raise ValueError("calcium and phosphate must be positive")

    product = params.calcium_mg_dl * params.phosphate_mg_dl
    return {
        "gfr_category": _gfr_category(params.egfr),
        "egfr": params.egfr,
        "calcium_mg_dl": params.calcium_mg_dl,
        "phosphate_mg_dl": params.phosphate_mg_dl,
        "caPO4_product": round(product, 2),
        "pth_pg_ml": params.pth_pg_ml,
        "vitamin_d_ng_ml": params.vitamin_d_ng_ml,
        "management_recommendations": [],
        "interpretation_note": (
            "GFR category is descriptive and does not establish CKD without chronicity. "
            "KDIGO CKD-MBD decisions use serial calcium, phosphate, and PTH assessments "
            "considered together rather than Ca x P as a treatment target."
        ),
    }


class CKDMBDIntegrationAgent:
    def __init__(self) -> None:
        self.agent_name = "CKDMBDIntegrationAgent"

    def evaluate(self, params: CKDMBDParameters) -> Dict[str, Any]:
        return {"ckd_mbd_result": assess_ckd_mbd(params), "alerts": []}
