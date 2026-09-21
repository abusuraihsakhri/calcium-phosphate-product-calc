"""
Calcium-phosphate product calculator.

This module intentionally separates arithmetic from clinical interpretation.
KDIGO 2017 recommendation 3.1.5 advises using individual serum calcium and
phosphate values together rather than the mathematical Ca x P product to guide
clinical practice. The historical KDOQI 2003 Ca x P threshold of 55 mg^2/dL^2
is retained only as historical context, not as a current treatment target.

The albumin-adjusted calcium formula is a legacy estimate and may be inaccurate
in CKD, critical illness, and marked hypoalbuminemia. Use ionized calcium when
clinically indicated.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


CA_MG_TO_MMOL = 0.2495
PO4_MG_TO_MMOL = 0.3229
PRODUCT_CONV_FACTOR = 0.08056
HISTORICAL_KDOQI_PRODUCT_LIMIT = 55.0


class UnitSystem(str, Enum):
    US_CONVENTIONAL = "US_Conventional"
    SI_METRIC = "SI_Metric"


class RiskCategory(str, Enum):
    """Historical Ca x P context only; not a current KDIGO risk classification."""

    BELOW_HISTORICAL_KDOQI_THRESHOLD = (
        "Below historical KDOQI 2003 Ca x P threshold (<55 mg2/dL2)"
    )
    AT_OR_ABOVE_HISTORICAL_KDOQI_THRESHOLD = (
        "At or above historical KDOQI 2003 Ca x P threshold (>=55 mg2/dL2)"
    )

    # Backward-compatible aliases for callers of earlier releases.
    TARGET_OPTIMAL = BELOW_HISTORICAL_KDOQI_THRESHOLD
    ELEVATED_RISK = AT_OR_ABOVE_HISTORICAL_KDOQI_THRESHOLD
    CRITICAL_RISK = AT_OR_ABOVE_HISTORICAL_KDOQI_THRESHOLD


class BinderClass(str, Enum):
    NO_AUTOMATED_RECOMMENDATION = "No automated medication recommendation"
    NON_CALCIUM_BASED = "Non-calcium-based binder"
    CALCIUM_BASED = "Calcium-based binder"
    CALCIMIMETIC_ADJUNCT = "Calcimimetic therapy"
    DIALYSIS_OPTIMIZATION = "Dialysis optimization"


@dataclass
class PatientBiomarkersInput:
    patient_id: str
    serum_calcium: float
    serum_phosphate: float
    serum_albumin: float = 4.0
    intact_pth_pg_ml: Optional[float] = None
    unit_system: UnitSystem = UnitSystem.US_CONVENTIONAL
    on_warfarin: bool = False
    ckd_stage_5_or_dialysis: bool = True
    dialysis_vintage_years: float = 0.0
    bmi: float = 24.0
    diabetes: bool = False
    female_sex: bool = False
    has_vascular_calcification: bool = False

    def validate(self) -> None:
        values = {
            "serum_calcium": self.serum_calcium,
            "serum_phosphate": self.serum_phosphate,
            "serum_albumin": self.serum_albumin,
        }
        for name, value in values.items():
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(f"{name} must be a finite number")
            if float(value) <= 0:
                raise ValueError(f"{name} must be positive")

        if self.intact_pth_pg_ml is not None:
            if not math.isfinite(float(self.intact_pth_pg_ml)) or self.intact_pth_pg_ml < 0:
                raise ValueError("intact_pth_pg_ml must be a finite non-negative number")
        if not math.isfinite(float(self.dialysis_vintage_years)) or self.dialysis_vintage_years < 0:
            raise ValueError("dialysis_vintage_years must be a finite non-negative number")
        if not math.isfinite(float(self.bmi)) or self.bmi <= 0:
            raise ValueError("bmi must be a finite positive number")


@dataclass
class ProductCalculationResult:
    measured_calcium_mg_dl: float
    measured_calcium_mmol_l: float
    corrected_calcium_mg_dl: float
    corrected_calcium_mmol_l: float
    phosphate_mg_dl: float
    phosphate_mmol_l: float
    measured_product_mg2_dl2: float
    measured_product_mmol2_l2: float
    product_mg2_dl2: float
    product_mmol2_l2: float
    albumin_g_dl: float
    historical_kdoqi_below_55: bool
    risk_category: RiskCategory
    correction_note: str

    @property
    def kdigo_target_achieved(self) -> bool:
        """Deprecated compatibility alias; this is not a KDIGO treatment target."""
        return self.historical_kdoqi_below_55


@dataclass
class CalciphylaxisRiskAssessment:
    hazard_score: Optional[float]
    estimated_risk_tier: str
    active_risk_factors: List[str]
    warfarin_exposure_present: bool
    model_note: str

    @property
    def warfarin_contraindication_alert(self) -> bool:
        """Deprecated alias. This calculator does not declare warfarin contraindicated."""
        return False


@dataclass
class BinderRecommendation:
    recommended_binder_class: BinderClass
    clinical_rationale: str
    calcium_binder_permitted: Optional[bool]
    calcimimetic_indicated: Optional[bool]


@dataclass
class CkdMbdReport:
    patient_id: str
    product_data: ProductCalculationResult
    calciphylaxis_risk: CalciphylaxisRiskAssessment
    pharmacotherapy: BinderRecommendation
    critical_alerts: List[str]
    clinical_advisories: List[str]
    summary_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["product_data"]["risk_category"] = self.product_data.risk_category.value
        data["pharmacotherapy"]["recommended_binder_class"] = (
            self.pharmacotherapy.recommended_binder_class.value
        )
        return data

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class CalciumPhosphateCalculator:
    HISTORICAL_KDOQI_PRODUCT_LIMIT = HISTORICAL_KDOQI_PRODUCT_LIMIT

    @classmethod
    def calculate_product(cls, biomarkers: PatientBiomarkersInput) -> ProductCalculationResult:
        biomarkers.validate()

        if biomarkers.unit_system == UnitSystem.US_CONVENTIONAL:
            ca_mg = float(biomarkers.serum_calcium)
            po4_mg = float(biomarkers.serum_phosphate)
            alb_g_dl = float(biomarkers.serum_albumin)

            ca_mmol = ca_mg * CA_MG_TO_MMOL
            po4_mmol = po4_mg * PO4_MG_TO_MMOL
            corr_ca_mg = ca_mg + 0.8 * (4.0 - alb_g_dl)
            corr_ca_mmol = corr_ca_mg * CA_MG_TO_MMOL
        else:
            ca_mmol = float(biomarkers.serum_calcium)
            po4_mmol = float(biomarkers.serum_phosphate)
            alb_g_l = float(biomarkers.serum_albumin)
            alb_g_dl = alb_g_l / 10.0

            ca_mg = ca_mmol / CA_MG_TO_MMOL
            po4_mg = po4_mmol / PO4_MG_TO_MMOL
            corr_ca_mmol = ca_mmol + 0.02 * (40.0 - alb_g_l)
            corr_ca_mg = corr_ca_mmol / CA_MG_TO_MMOL

        if corr_ca_mg <= 0:
            raise ValueError("albumin-adjusted calcium is non-positive; check units and inputs")

        measured_product_mg2 = ca_mg * po4_mg
        measured_product_mmol2 = ca_mmol * po4_mmol
        corrected_product_mg2 = corr_ca_mg * po4_mg
        corrected_product_mmol2 = corr_ca_mmol * po4_mmol

        below_historical = corrected_product_mg2 < cls.HISTORICAL_KDOQI_PRODUCT_LIMIT
        context = (
            RiskCategory.BELOW_HISTORICAL_KDOQI_THRESHOLD
            if below_historical
            else RiskCategory.AT_OR_ABOVE_HISTORICAL_KDOQI_THRESHOLD
        )

        return ProductCalculationResult(
            measured_calcium_mg_dl=round(ca_mg, 3),
            measured_calcium_mmol_l=round(ca_mmol, 3),
            corrected_calcium_mg_dl=round(corr_ca_mg, 3),
            corrected_calcium_mmol_l=round(corr_ca_mmol, 3),
            phosphate_mg_dl=round(po4_mg, 3),
            phosphate_mmol_l=round(po4_mmol, 3),
            measured_product_mg2_dl2=round(measured_product_mg2, 3),
            measured_product_mmol2_l2=round(measured_product_mmol2, 3),
            product_mg2_dl2=round(corrected_product_mg2, 3),
            product_mmol2_l2=round(corrected_product_mmol2, 3),
            albumin_g_dl=round(alb_g_dl, 3),
            historical_kdoqi_below_55=below_historical,
            risk_category=context,
            correction_note=(
                "Albumin-adjusted calcium is a legacy estimate; ionized calcium is preferred "
                "when an accurate physiologic calcium assessment is clinically important."
            ),
        )

    @classmethod
    def evaluate_calciphylaxis_risk(
        cls,
        biomarkers: PatientBiomarkersInput,
        calc_result: ProductCalculationResult,
    ) -> CalciphylaxisRiskAssessment:
        """List known associations without inventing an individual probability or tier."""
        factors: List[str] = []
        if biomarkers.on_warfarin:
            factors.append("Warfarin exposure")
        if calc_result.albumin_g_dl < 3.5:
            factors.append("Hypoalbuminemia")
        if biomarkers.dialysis_vintage_years >= 3:
            factors.append("Dialysis vintage >=3 years")
        if biomarkers.bmi >= 30:
            factors.append("Obesity")
        if biomarkers.diabetes:
            factors.append("Diabetes mellitus")
        if biomarkers.female_sex:
            factors.append("Female sex")
        if biomarkers.has_vascular_calcification:
            factors.append("Known vascular or valvular calcification")

        return CalciphylaxisRiskAssessment(
            hazard_score=None,
            estimated_risk_tier="Not estimated",
            active_risk_factors=factors,
            warfarin_exposure_present=biomarkers.on_warfarin,
            model_note=(
                "No validated individual calciphylaxis probability is calculated. "
                "Listed factors are contextual associations only."
            ),
        )

    @classmethod
    def optimize_phosphate_binder(
        cls,
        biomarkers: PatientBiomarkersInput,
        calc_result: ProductCalculationResult,
    ) -> BinderRecommendation:
        """Return guideline context without automated medication selection."""
        return BinderRecommendation(
            recommended_binder_class=BinderClass.NO_AUTOMATED_RECOMMENDATION,
            clinical_rationale=(
                "KDIGO 2017 bases CKD-MBD treatment on serial phosphate, calcium, and PTH "
                "assessments considered together. This calculator does not select or dose "
                "phosphate binders or calcimimetics."
            ),
            calcium_binder_permitted=None,
            calcimimetic_indicated=None,
        )

    @classmethod
    def evaluate_case(cls, biomarkers: PatientBiomarkersInput) -> CkdMbdReport:
        calc_res = cls.calculate_product(biomarkers)
        risk_context = cls.evaluate_calciphylaxis_risk(biomarkers, calc_res)
        medication_context = cls.optimize_phosphate_binder(biomarkers, calc_res)

        advisories = [
            (
                "Current KDIGO guidance recommends interpreting serum calcium and phosphate "
                "values together and following serial trends rather than using Ca x P as a "
                "treatment target."
            ),
            calc_res.correction_note,
        ]
        if not calc_res.historical_kdoqi_below_55:
            advisories.append(
                "The albumin-adjusted Ca x P is at or above the historical KDOQI 2003 "
                "threshold of 55 mg2/dL2; this historical threshold is not a current KDIGO target."
            )

        summary = (
            f"Case {biomarkers.patient_id}: measured Ca x P "
            f"{calc_res.measured_product_mg2_dl2:.2f} mg2/dL2; "
            f"albumin-adjusted Ca x P {calc_res.product_mg2_dl2:.2f} mg2/dL2. "
            "Use the individual calcium and phosphate values, clinical context, and serial "
            "measurements for clinical decisions."
        )

        return CkdMbdReport(
            patient_id=biomarkers.patient_id,
            product_data=calc_res,
            calciphylaxis_risk=risk_context,
            pharmacotherapy=medication_context,
            critical_alerts=[],
            clinical_advisories=advisories,
            summary_interpretation=summary,
        )


def format_ckd_mbd_report(report: CkdMbdReport) -> str:
    p = report.product_data
    c = report.calciphylaxis_risk

    lines = [
        "=" * 72,
        f"CALCIUM-PHOSPHATE PRODUCT REPORT : {report.patient_id}",
        "=" * 72,
        f"Measured total calcium: {p.measured_calcium_mg_dl:.3f} mg/dL "
        f"({p.measured_calcium_mmol_l:.3f} mmol/L)",
        f"Albumin-adjusted calcium: {p.corrected_calcium_mg_dl:.3f} mg/dL "
        f"({p.corrected_calcium_mmol_l:.3f} mmol/L)",
        f"Phosphate: {p.phosphate_mg_dl:.3f} mg/dL ({p.phosphate_mmol_l:.3f} mmol/L)",
        f"Measured Ca x P: {p.measured_product_mg2_dl2:.3f} mg2/dL2 "
        f"({p.measured_product_mmol2_l2:.3f} mmol2/L2)",
        f"Albumin-adjusted Ca x P: {p.product_mg2_dl2:.3f} mg2/dL2 "
        f"({p.product_mmol2_l2:.3f} mmol2/L2)",
        f"Historical context: {p.risk_category.value}",
        "-" * 72,
        "KDIGO 2017: use individual serum calcium and phosphate values together",
        "and follow serial trends rather than treating Ca x P as a target.",
        "Albumin-adjusted calcium is an estimate and can be inaccurate in CKD.",
    ]

    if c.active_risk_factors:
        lines.extend(["-" * 72, "Contextual calciphylaxis associations supplied:"])
        lines.extend(f"  - {item}" for item in c.active_risk_factors)
        lines.append("No individual calciphylaxis probability or risk tier is calculated.")

    lines.extend(["=" * 72, report.summary_interpretation])
    return "\n".join(lines)
