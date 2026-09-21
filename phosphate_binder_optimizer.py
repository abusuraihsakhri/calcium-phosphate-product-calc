#!/usr/bin/env python3
"""Phosphate-binder context helper.

Kept for API compatibility. Automated binder selection and dosing are
intentionally not performed because KDIGO 2017 does not support deriving a
patient-specific prescription from a Ca x P threshold.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class BinderContext:
    serum_phosphate_mg_dl: float
    corrected_calcium_mg_dl: float
    albumin_g_dl: float = 4.0
    vascular_calcification: bool = False
    low_turnover_bone: bool = False
    intact_pth_pg_ml: float = 300.0
    hypercalcemic_episodes_per_year: int = 0
    pill_burden_sensitive: bool = False


def phosphate_severity(p_mg_dl: float) -> str:
    """Return a neutral numeric band for display; not a treatment category."""
    if p_mg_dl < 0:
        raise ValueError("serum phosphate must be non-negative")
    if p_mg_dl < 4.5:
        return "below_4_5"
    if p_mg_dl < 5.5:
        return "4_5_to_5_49"
    return "5_5_or_higher"


def restrict_calcium_binders(ctx: BinderContext) -> List[str]:
    """Return contextual factors relevant to clinician review."""
    reasons: List[str] = []
    if ctx.vascular_calcification:
        reasons.append("known vascular calcification")
    if ctx.low_turnover_bone:
        reasons.append("known low-turnover/adynamic bone disease")
    if ctx.hypercalcemic_episodes_per_year > 0:
        reasons.append("history of hypercalcemic episodes")
    return reasons


def select_binder(ctx: BinderContext) -> Dict[str, Any]:
    """Compatibility function: no medication is automatically selected."""
    if ctx.serum_phosphate_mg_dl < 0 or ctx.corrected_calcium_mg_dl <= 0:
        raise ValueError("invalid calcium or phosphate value")

    considerations = restrict_calcium_binders(ctx)
    return {
        "phosphate_band": phosphate_severity(ctx.serum_phosphate_mg_dl),
        "selected_binder": None,
        "tablets_with_meals": None,
        "daily_tablets": None,
        "daily_elemental_calcium_mg": None,
        "within_ca_budget": None,
        "kdigo_restrictions": considerations,
        "titration_note": None,
        "notes": [
            "No automated binder selection or dose is provided.",
            (
                "KDIGO 2017 bases phosphate-lowering treatment on progressively or "
                "persistently elevated serum phosphate and recommends restricting the "
                "dose of calcium-based phosphate binders in adults receiving treatment."
            ),
        ],
    }


if __name__ == "__main__":
    print(select_binder(BinderContext(6.2, 9.4)))
