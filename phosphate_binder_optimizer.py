#!/usr/bin/env python3
"""
Phosphate binder optimization engine for CKD-MBD (KDIGO-aligned rules).

Real formulary facts encoded here:
  Elemental calcium per binder class:
      calcium carbonate 40%, calcium acetate 25%
  Daily elemental calcium budget: <=1500 mg as binder,
      <=2000 mg including dietary intake
  Non-calcium binders: sevelamer carbonate (800 mg tabs),
      lanthanum carbonate (1000 mg), ferric citrate (210 mg elemental Fe),
      sucroferric oxyhydroxide (500 mg)

Selection rules (KDIGO 2017):
  - Restrict calcium-based binders when corrected Ca is high, arterial
    calcification is present, adynamic bone disease, or PTH persistently low
  - Titration ladder by serum phosphate severity sets the tablet count

Stdlib only.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class BinderContext:
    serum_phosphate_mg_dl: float
    corrected_calcium_mg_dl: float
    albumin_g_dl: float = 4.0
    vascular_calcification: bool = False
    low_turnover_bone: bool = False          # adynamic bone disease
    intact_pth_pg_ml: float = 300.0
    hypercalcemic_episodes_per_year: int = 0
    pill_burden_sensitive: bool = False


BINDER_TABLETS_PER_MEAL = {           # starting tablets with each large meal
    "calcium_acetate_667mg": {"mild": 1, "moderate": 2, "severe": 2},
    "sevelamer_carbonate_800mg": {"mild": 1, "moderate": 2, "severe": 3},
    "lanthanum_carbonate_1000mg": {"mild": 1, "moderate": 1, "severe": 2},
    "ferric_citrate_210mgFe": {"mild": 1, "moderate": 2, "severe": 3},
}

CALCIUM_BASIS = {
    "calcium_acetate_667mg": 0.25 * 667,   # ~167 mg elemental Ca per tab
    "calcium_carbonate_1250mg": 0.40 * 1250,
}


def phosphate_severity(p_mg_dl: float) -> str:
    if p_mg_dl > 9.0:
        return "severe"
    if p_mg_dl >= 7.0:
        return "moderate"
    return "mild"


def restrict_calcium_binders(ctx: BinderContext) -> List[str]:
    """KDIGO reasons to limit calcium-based binder dose."""
    reasons = []
    ca_corr = ctx.corrected_calcium_mg_dl + 0.8 * max(0.0, 4.0 - ctx.albumin_g_dl)
    if ca_corr > 10.2:
        reasons.append(f"corrected Ca {ca_corr:.1f} > 10.2 mg/dL")
    if ctx.hypercalcemic_episodes_per_year > 0:
        reasons.append(f"{ctx.hypercalcemic_episodes_per_year} hypercalcemic episode(s)/yr")
    if ctx.vascular_calcification:
        reasons.append("arterial calcification present")
    if ctx.low_turnover_bone:
        reasons.append("adynamic bone disease")
    if ctx.intact_pth_pg_ml < 120:
        reasons.append(f"persistently low PTH ({ctx.intact_pth_pg_ml} pg/mL)")
    return reasons


def select_binder(ctx: BinderContext) -> Dict[str, Any]:
    sev = phosphate_severity(ctx.serum_phosphate_mg_dl)
    restrictions = restrict_calcium_binders(ctx)
    calcium_ok = not restrictions

    if calcium_ok:
        primary = "calcium_acetate_667mg"
        rationale = ("No KDIGO restriction triggers; calcium acetate preferred "
                     "(effective, lowest cost)")
    elif ctx.pill_burden_sensitive:
        primary = "lanthanum_carbonate_1000mg"
        rationale = ("Calcium binders restricted; lanthanum chosen for lowest "
                     "tablet burden among non-calcium agents")
    else:
        primary = "ferric_citrate_210mgFe" if ctx.serum_phosphate_mg_dl < 8.5 \
            else "sevelamer_carbonate_800mg"
        rationale = ("Calcium binders restricted; iron-based binder also corrects "
                     "iron stores" if primary.startswith("ferric") else
                     "Calcium binders restricted; sevelamer also lowers LDL")

    tablets_per_meal = BINDER_TABLETS_PER_MEAL[primary][sev]
    meals = 3
    daily_tablets = tablets_per_meal * meals

    elemental_ca_daily = 0
    if primary in CALCIUM_BASIS:
        elemental_ca_daily = round(CALCIUM_BASIS[primary] * daily_tablets)
        over_budget = elemental_ca_daily > 1500
    else:
        over_budget = False

    notes: List[str] = [rationale]
    if restrictions:
        notes.append("Restrictions active: " + "; ".join(restrictions))
    if over_budget:
        notes.append(f"Elemental Ca load {elemental_ca_daily} mg/day exceeds 1500 mg "
                     "binder budget - switch to non-calcium agent")
    if sev == "severe":
        notes.append("Severe hyperphosphatemia: verify dialysis adequacy and dietary "
                     "phosphorus counseling alongside binder titration")

    return {
        "phosphate_severity": sev,
        "selected_binder": primary,
        "tablets_with_meals": tablets_per_meal,
        "daily_tablets": daily_tablets,
        "daily_elemental_calcium_mg": elemental_ca_daily,
        "within_ca_budget": not over_budget,
        "kdigo_restrictions": restrictions,
        "titration_note": "recheck phosphate in 2-4 weeks; step up one tablet/meal if >5.5",
        "notes": notes,
    }


if __name__ == "__main__":
    contexts = [
        ("unrestricted", BinderContext(6.2, 9.4)),
        ("vascular calcification + high Ca",
         BinderContext(7.8, 10.6, vascular_calcification=True)),
        ("adynamic bone, pill-sensitive",
         BinderContext(9.4, 9.0, low_turnover_bone=True, pill_burden_sensitive=True)),
        ("recurring hypercalcemia",
         BinderContext(5.9, 10.9, 3.9, False, False, 90, 3)),
    ]
    for name, ctx in contexts:
        r = select_binder(ctx)
        print(f"\n=== {name} === PO4 {ctx.serum_phosphate_mg_dl} mg/dL [{r['phosphate_severity']}]")
        print(f"binder : {r['selected_binder']}  "
              f"{r['tablets_with_meals']} tabs with each of 3 large meals")
        print(f"daily elemental Ca: {r['daily_elemental_calcium_mg']} mg "
              f"(budget ok={r['within_ca_budget']})")
        for n in r["notes"]:
            print(f"  - {n}")
