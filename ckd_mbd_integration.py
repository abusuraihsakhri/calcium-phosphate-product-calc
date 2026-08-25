#!/usr/bin/env python3
"""
CKD-MBD Integration for Calcium-Phosphate Product Calculator.
Integrates Ca x PO4 product with CKD-MBD staging and bone metabolism markers.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


CKD_MBD_STAGES = {
    "early": {"gfr_range": (60, 90), "risk": "low", "management": "Monitor and optimize vitamin D"},
    "moderate": {"gfr_range": (30, 59), "risk": "moderate", "management": "Phosphate binders if PO4 elevated"},
    "severe": {"gfr_range": (15, 29), "risk": "high", "management": "Intensive phosphate management, calcimimetics"},
    "kidney_failure": {"gfr_range": (0, 14), "risk": "very_high", "management": "Dialysis optimization, transplant evaluation"},
}


@dataclass
class CKDMBDParameters:
    """CKD-MBD relevant parameters."""
    egfr: float
    calcium_mg_dl: float
    phosphate_mg_dl: float
    pth_pg_ml: float
    vitamin_d_ng_ml: float
    alkaline_phosphatase_u_l: float = 0.0
    bicarbonate_meq_l: float = 24.0


def assess_ckd_mbd(params: CKDMBDParameters) -> Dict[str, Any]:
    """Assess CKD-MBD status incorporating Ca x PO4 product."""
    caPO4_product = params.calcium_mg_dl * params.phosphate_mg_dl

    if params.egfr >= 90:
        ckd_stage = "normal"
    elif params.egfr >= 60:
        ckd_stage = "early"
    elif params.egfr >= 30:
        ckd_stage = "moderate"
    elif params.egfr >= 15:
        ckd_stage = "severe"
    else:
        ckd_stage = "kidney_failure"

    stage_info = CKD_MBD_STAGES.get(ckd_stage, CKD_MBD_STAGES["early"])

    bone_metabolism = "normal"
    if params.pth_pg_ml > 600:
        bone_metabolism = "severe_hyperparathyroidism"
    elif params.pth_pg_ml > 400:
        bone_metabolism = "moderate_hyperparathyroidism"
    elif params.pth_pg_ml > 100:
        bone_metabolism = "mild_hyperparathyroidism"

    if params.vitamin_d_ng_ml < 20:
        vitamin_d_status = "deficient"
    elif params.vitamin_d_ng_ml < 30:
        vitamin_d_status = "insufficient"
    else:
        vitamin_d_status = "sufficient"

    vascular_calcification_risk = caPO4_product * (1 + (params.egfr < 30) * 0.5)

    management = [stage_info["management"]]
    if caPO4_product > 55:
        management.append("Intensify phosphate binder therapy")
    if bone_metabolism in ("moderate_hyperparathyroidism", "severe_hyperparathyroidism"):
        management.append("Consider calcimimetics (cinacalcet)")
    if vitamin_d_status == "deficient":
        management.append("Vitamin D supplementation")
    if params.bicarbonate_meq_l < 22:
        management.append("Oral sodium bicarbonate for metabolic acidosis")

    return {
        "ckd_stage": ckd_stage,
        "ckd_stage_description": stage_info.get("risk", "unknown"),
        "caPO4_product": round(caPO4_product, 1),
        "bone_metabolism": bone_metabolism,
        "vitamin_d_status": vitamin_d_status,
        "vascular_calcification_risk": round(vascular_calcification_risk, 1),
        "management_recommendations": management,
        "egfr": params.egfr,
        "pth_pg_ml": params.pth_pg_ml,
    }


class CKDMBDIntegrationAgent:
    """Sub-agent for CKD-MBD integration."""

    def __init__(self):
        self.agent_name = "CKDMBDIntegrationAgent"

    def evaluate(self, params: CKDMBDParameters) -> Dict[str, Any]:
        """Evaluate CKD-MBD integration."""
        result = assess_ckd_mbd(params)
        alerts = []

        if result["ckd_stage"] in ("severe", "kidney_failure"):
            alerts.append({
                "type": "ADVANCED_CKD", "severity": "WARNING",
                "message": f"CKD stage: {result['ckd_stage']} (eGFR {params.egfr:.0f}).",
                "recommendation": "Nephrology referral recommended. Consider transplant evaluation."
            })

        if result["caPO4_product"] > 55 and result["ckd_stage"] in ("severe", "kidney_failure"):
            alerts.append({
                "type": "HIGH_RISK_CAPO4_CKD", "severity": "CRITICAL",
                "message": f"Elevated Ca x PO4 ({result['caPO4_product']:.1f}) in advanced CKD.",
                "recommendation": "Urgent phosphate management optimization. Cardiovascular risk assessment."
            })

        if result["bone_metabolism"] in ("moderate_hyperparathyroidism", "severe_hyperparathyroidism"):
            alerts.append({
                "type": "SECONDARY_HYPERPARATHYROIDISM", "severity": "WARNING",
                "message": f"PTH {params.pth_pg_ml:.0f} pg/mL ({result['bone_metabolism']}).",
                "recommendation": "Consider calcimimetics. Bone density assessment if fracture risk."
            })

        return {"ckd_mbd_result": result, "alerts": alerts}
