"""
Calcium-Phosphate Product & CKD-MBD Clinical Risk Engine
========================================================
Comprehensive nephrology and mineral-bone disorder (CKD-MBD) engine implementing:
- Albumin-corrected calcium derivation (Payne's formula in US conventional and SI units)
- Calcium-Phosphate product (Ca x PO4) computation in (mg/dL)^2 and (mmol/L)^2
- KDIGO / KDOQI clinical guideline threshold stratification (<55 target, 55-70 high, >=70 critical)
- Multivariable Calciphylaxis (Calcific Uremic Arteriolopathy) hazard index model
- Guideline-directed phosphate binder selection and calcimimetic optimization

Standards:
- KDIGO 2017 Clinical Practice Guideline Update for CKD-MBD
- KDOQI Clinical Practice Guidelines for Bone Metabolism and Disease in CKD
- European Calciphylaxis Network (EuCalNet) Consensus Framework
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Union


# Unit conversion factors
CA_MG_TO_MMOL = 0.2495       # 1 mg/dL Ca = 0.2495 mmol/L
PO4_MG_TO_MMOL = 0.3229      # 1 mg/dL PO4 = 0.3229 mmol/L
PRODUCT_CONV_FACTOR = 0.08056 # (mg/dL)^2 to (mmol/L)^2


class UnitSystem(str, Enum):
    US_CONVENTIONAL = "US_Conventional"  # Ca: mg/dL, PO4: mg/dL, Albumin: g/dL
    SI_METRIC = "SI_Metric"              # Ca: mmol/L, PO4: mmol/L, Albumin: g/L


class RiskCategory(str, Enum):
    TARGET_OPTIMAL = "Target / Optimal Range (Product < 55.0 mg2/dL2)"
    ELEVATED_RISK = "Elevated Risk / Metastatic Calcification (Product 55.0 - 69.9 mg2/dL2)"
    CRITICAL_RISK = "Critical Risk / High Calciphylaxis Propensity (Product >= 70.0 mg2/dL2)"


class BinderClass(str, Enum):
    NON_CALCIUM_BASED = "Non-Calcium-Based Binder (Sevelamer, Lanthanum, Sucroferric Oxyhydroxide)"
    CALCIUM_BASED = "Calcium-Based Binder (Calcium Acetate / Calcium Carbonate)"
    CALCIMIMETIC_ADJUNCT = "Calcimimetic Therapy (Cinacalcet / Etelcalcetide)"
    DIALYSIS_OPTIMIZATION = "Dialysate Calcium & Clearance Optimization"


@dataclass
class PatientBiomarkersInput:
    """Clinical laboratory input for CKD-MBD and Ca x PO4 evaluation."""
    patient_id: str
    serum_calcium: float            # Measured total calcium (mg/dL or mmol/L)
    serum_phosphate: float          # Inorganic phosphate (mg/dL or mmol/L)
    serum_albumin: float = 4.0      # Albumin (g/dL or g/L)
    intact_pth_pg_ml: Optional[float] = None  # Intact PTH (pg/mL or ng/L)
    unit_system: UnitSystem = UnitSystem.US_CONVENTIONAL

    # Clinical risk factors for calciphylaxis
    on_warfarin: bool = False
    ckd_stage_5_or_dialysis: bool = True
    dialysis_vintage_years: float = 0.0
    bmi: float = 24.0
    diabetes: bool = False
    female_sex: bool = False
    has_vascular_calcification: bool = False

    def validate(self) -> None:
        if self.serum_calcium <= 0:
            raise ValueError(f"Serum calcium must be positive, got {self.serum_calcium}")
        if self.serum_phosphate <= 0:
            raise ValueError(f"Serum phosphate must be positive, got {self.serum_phosphate}")
        if self.serum_albumin <= 0:
            raise ValueError(f"Serum albumin must be positive, got {self.serum_albumin}")


@dataclass
class ProductCalculationResult:
    """Derived chemistry, albumin correction, and unit conversions."""
    measured_calcium_mg_dl: float
    measured_calcium_mmol_l: float
    corrected_calcium_mg_dl: float
    corrected_calcium_mmol_l: float
    phosphate_mg_dl: float
    phosphate_mmol_l: float
    product_mg2_dl2: float
    product_mmol2_l2: float
    albumin_g_dl: float
    kdigo_target_achieved: bool
    risk_category: RiskCategory


@dataclass
class CalciphylaxisRiskAssessment:
    """Multivariable hazard model evaluation for calciphylaxis."""
    hazard_score: float              # 0.0 to 100.0 index
    estimated_risk_tier: str         # Low, Intermediate, High, Very High
    active_risk_factors: List[str]
    warfarin_contraindication_alert: bool


@dataclass
class BinderRecommendation:
    """Pharmacotherapeutic recommendation for phosphate management."""
    recommended_binder_class: BinderClass
    clinical_rationale: str
    calcium_binder_permitted: bool
    calcimimetic_indicated: bool


@dataclass
class CkdMbdReport:
    """Comprehensive clinical evaluation dossier."""
    patient_id: str
    product_data: ProductCalculationResult
    calciphylaxis_risk: CalciphylaxisRiskAssessment
    pharmacotherapy: BinderRecommendation
    critical_alerts: List[str]
    clinical_advisories: List[str]
    summary_interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["product_data"]["risk_category"] = self.product_data.risk_category.value
        d["pharmacotherapy"]["recommended_binder_class"] = self.pharmacotherapy.recommended_binder_class.value
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class CalciumPhosphateCalculator:
    """
    Expert nephrology engine for CKD-MBD, calcium-phosphate product kinetics,
    and calciphylaxis risk prediction.
    """

    KDIGO_PRODUCT_TARGET_MG2DL2 = 55.0
    CRITICAL_PRODUCT_THRESHOLD = 70.0

    @classmethod
    def calculate_product(cls, biomarkers: PatientBiomarkersInput) -> ProductCalculationResult:
        """Computes albumin-corrected calcium and Ca x PO4 product across unit systems."""
        biomarkers.validate()

        if biomarkers.unit_system == UnitSystem.US_CONVENTIONAL:
            ca_mg = biomarkers.serum_calcium
            po4_mg = biomarkers.serum_phosphate
            alb_g_dl = biomarkers.serum_albumin

            # Payne's formula: Corrected Ca = Measured Ca + 0.8 * (4.0 - Albumin)
            corr_ca_mg = ca_mg + 0.8 * (4.0 - alb_g_dl)
            corr_ca_mg = max(1.0, corr_ca_mg)

            corr_ca_mmol = corr_ca_mg * CA_MG_TO_MMOL
            ca_mmol = ca_mg * CA_MG_TO_MMOL
            po4_mmol = po4_mg * PO4_MG_TO_MMOL
        else:
            # SI Metric: Ca in mmol/L, PO4 in mmol/L, Albumin in g/L
            ca_mmol = biomarkers.serum_calcium
            po4_mmol = biomarkers.serum_phosphate
            alb_g_l = biomarkers.serum_albumin
            alb_g_dl = alb_g_l / 10.0

            # Payne's formula in SI: Corrected Ca (mmol/L) = Measured Ca + 0.02 * (40.0 - Albumin g/L)
            corr_ca_mmol = ca_mmol + 0.02 * (40.0 - alb_g_l)
            corr_ca_mmol = max(0.25, corr_ca_mmol)

            ca_mg = ca_mmol / CA_MG_TO_MMOL
            corr_ca_mg = corr_ca_mmol / CA_MG_TO_MMOL
            po4_mg = po4_mmol / PO4_MG_TO_MMOL

        # Compute Products
        product_mg2 = corr_ca_mg * po4_mg
        product_mmol2 = corr_ca_mmol * po4_mmol

        target_met = product_mg2 < cls.KDIGO_PRODUCT_TARGET_MG2DL2

        if product_mg2 < cls.KDIGO_PRODUCT_TARGET_MG2DL2:
            cat = RiskCategory.TARGET_OPTIMAL
        elif product_mg2 < cls.CRITICAL_PRODUCT_THRESHOLD:
            cat = RiskCategory.ELEVATED_RISK
        else:
            cat = RiskCategory.CRITICAL_RISK

        return ProductCalculationResult(
            measured_calcium_mg_dl=round(ca_mg, 2),
            measured_calcium_mmol_l=round(ca_mmol, 2),
            corrected_calcium_mg_dl=round(corr_ca_mg, 2),
            corrected_calcium_mmol_l=round(corr_ca_mmol, 2),
            phosphate_mg_dl=round(po4_mg, 2),
            phosphate_mmol_l=round(po4_mmol, 2),
            product_mg2_dl2=round(product_mg2, 2),
            product_mmol2_l2=round(product_mmol2, 2),
            albumin_g_dl=round(alb_g_dl, 2),
            kdigo_target_achieved=target_met,
            risk_category=cat
        )

    @classmethod
    def evaluate_calciphylaxis_risk(
        cls,
        biomarkers: PatientBiomarkersInput,
        calc_result: ProductCalculationResult
    ) -> CalciphylaxisRiskAssessment:
        """Calculates multivariable Calciphylaxis Hazard Index."""
        hazard = 5.0  # Baseline population risk
        factors = []
        warfarin_alert = False

        # 1. Product contribution
        if calc_result.product_mg2_dl2 >= 70.0:
            hazard += 35.0
            factors.append(f"Critical Ca x PO4 product ({calc_result.product_mg2_dl2:.1f} >= 70 mg2/dL2)")
        elif calc_result.product_mg2_dl2 >= 55.0:
            hazard += 18.0
            factors.append(f"Elevated Ca x PO4 product ({calc_result.product_mg2_dl2:.1f} >= 55 mg2/dL2)")

        # 2. Hyperphosphatemia
        if calc_result.phosphate_mg_dl >= 6.5:
            hazard += 15.0
            factors.append(f"Severe hyperphosphatemia ({calc_result.phosphate_mg_dl:.1f} mg/dL)")

        # 3. Warfarin / Vitamin K Antagonist (MGP inhibition)
        if biomarkers.on_warfarin:
            hazard += 25.0
            warfarin_alert = True
            factors.append("Active Warfarin therapy (inhibits Matrix Gla Protein carboxylation)")

        # 4. Hypoalbuminemia
        if calc_result.albumin_g_dl < 3.5:
            hazard += 10.0
            factors.append(f"Hypoalbuminemia ({calc_result.albumin_g_dl:.1f} g/dL, systemic inflammation marker)")

        # 5. Dialysis vintage & CKD
        if biomarkers.dialysis_vintage_years >= 3.0:
            hazard += 8.0
            factors.append(f"Extended dialysis vintage ({biomarkers.dialysis_vintage_years:.1f} years)")

        # 6. Obesity & Diabetes
        if biomarkers.bmi >= 30.0:
            hazard += 6.0
            factors.append(f"Obesity (BMI {biomarkers.bmi:.1f} kg/m2)")
        if biomarkers.diabetes:
            hazard += 6.0
            factors.append("Diabetes mellitus (microvascular disease)")
        if biomarkers.female_sex:
            hazard += 4.0
            factors.append("Female sex (increased calciphylaxis predisposition)")

        hazard_score = min(100.0, round(hazard, 1))

        if hazard_score < 25.0:
            tier = "Low Calciphylaxis Risk"
        elif hazard_score < 50.0:
            tier = "Moderate Calciphylaxis Risk"
        elif hazard_score < 75.0:
            tier = "High Calciphylaxis Risk"
        else:
            tier = "Very High / Critical Calciphylaxis Risk"

        return CalciphylaxisRiskAssessment(
            hazard_score=hazard_score,
            estimated_risk_tier=tier,
            active_risk_factors=factors,
            warfarin_contraindication_alert=warfarin_alert
        )

    @classmethod
    def optimize_phosphate_binder(
        cls,
        biomarkers: PatientBiomarkersInput,
        calc_result: ProductCalculationResult
    ) -> BinderRecommendation:
        """Determines optimal phosphate binder class and calcimimetic indications per KDIGO."""
        corr_ca = calc_result.corrected_calcium_mg_dl
        po4 = calc_result.phosphate_mg_dl
        prod = calc_result.product_mg2_dl2
        pth = biomarkers.intact_pth_pg_ml

        calcium_permitted = (corr_ca < 9.5) and (prod < 55.0) and not biomarkers.has_vascular_calcification
        calcimimetic_needed = (pth is not None and pth > 300.0) and (corr_ca >= 8.4)

        if prod >= 55.0 or corr_ca >= 9.5 or biomarkers.has_vascular_calcification:
            binder = BinderClass.NON_CALCIUM_BASED
            rationale = (
                "Non-calcium-based binder strongly recommended (Sevelamer carbonate, Lanthanum, "
                "or Sucroferric oxyhydroxide). Calcium-based binders contraindicated due to elevated "
                f"Ca x PO4 product ({prod:.1f}) or corrected calcium ({corr_ca:.2f} mg/dL)."
            )
        elif po4 > 4.5 and calcium_permitted:
            binder = BinderClass.CALCIUM_BASED
            rationale = (
                "Calcium-based phosphate binder (Calcium Acetate) acceptable as first-line: "
                f"Corrected calcium is normal/low ({corr_ca:.2f} mg/dL) and Ca x PO4 product is controlled ({prod:.1f})."
            )
        elif po4 > 5.5:
            binder = BinderClass.NON_CALCIUM_BASED
            rationale = "Severe hyperphosphatemia requires potent non-calcium binding to prevent calcium loading."
        else:
            binder = BinderClass.DIALYSIS_OPTIMIZATION
            rationale = "Phosphate within target range. Maintain dietary counseling and standard dialysis clearance."

        return BinderRecommendation(
            recommended_binder_class=binder,
            clinical_rationale=rationale,
            calcium_binder_permitted=calcium_permitted,
            calcimimetic_indicated=calcimimetic_needed
        )

    @classmethod
    def evaluate_case(cls, biomarkers: PatientBiomarkersInput) -> CkdMbdReport:
        """Full diagnostic and therapeutic CKD-MBD case synthesis."""
        calc_res = cls.calculate_product(biomarkers)
        calciphylaxis = cls.evaluate_calciphylaxis_risk(biomarkers, calc_res)
        pharmacotherapy = cls.optimize_phosphate_binder(biomarkers, calc_res)

        critical_alerts = []
        advisories = []

        if calc_res.product_mg2_dl2 >= cls.CRITICAL_PRODUCT_THRESHOLD:
            critical_alerts.append(
                f"CRITICAL: Ca x PO4 product ({calc_res.product_mg2_dl2:.1f} mg2/dL2) exceeds severe risk threshold (>= 70). "
                "High precipitation propensity for calcific uremic arteriolopathy."
            )

        if calciphylaxis.warfarin_contraindication_alert and calc_res.product_mg2_dl2 >= 55.0:
            critical_alerts.append(
                "CRITICAL WARNING: Concurrent Warfarin use with elevated Ca x PO4 product. "
                "Strongly consider transitioning to alternative anticoagulation to prevent uncarboxylated MGP vascular calcification."
            )

        if calc_res.corrected_calcium_mg_dl >= 10.5:
            critical_alerts.append(f"Hypercalcemia detected (Corrected Ca: {calc_res.corrected_calcium_mg_dl:.2f} mg/dL). Hold calcium binders and active vitamin D.")
        elif calc_res.corrected_calcium_mg_dl < 8.4:
            advisories.append(f"Hypocalcemia noted (Corrected Ca: {calc_res.corrected_calcium_mg_dl:.2f} mg/dL). Monitor for neuromuscular symptoms and cardiac QTc prolongation.")

        if not calc_res.kdigo_target_achieved:
            advisories.append("KDIGO Safety Target Exceeded (Ca x PO4 >= 55 mg2/dL2). Intensify phosphate restriction and dialytic removal.")

        summary = (
            f"Patient {biomarkers.patient_id}: Corrected Ca = {calc_res.corrected_calcium_mg_dl:.2f} mg/dL, "
            f"PO4 = {calc_res.phosphate_mg_dl:.2f} mg/dL. "
            f"Ca x PO4 Product = {calc_res.product_mg2_dl2:.1f} mg2/dL2 ({calc_res.product_mmol2_l2:.2f} mmol2/L2) -> {calc_res.risk_category.value}. "
            f"Calciphylaxis Hazard: {calciphylaxis.hazard_score:.1f}/100 ({calciphylaxis.estimated_risk_tier}). "
            f"Rx: {pharmacotherapy.recommended_binder_class.name}."
        )

        return CkdMbdReport(
            patient_id=biomarkers.patient_id,
            product_data=calc_res,
            calciphylaxis_risk=calciphylaxis,
            pharmacotherapy=pharmacotherapy,
            critical_alerts=critical_alerts,
            clinical_advisories=advisories,
            summary_interpretation=summary
        )


def format_ckd_mbd_report(report: CkdMbdReport) -> str:
    """Renders formatted text clinical nephrology report."""
    p = report.product_data
    c = report.calciphylaxis_risk
    rx = report.pharmacotherapy

    lines = []
    lines.append("=" * 78)
    lines.append(f" CKD-MBD & CALCIUM-PHOSPHATE PRODUCT REPORT : {report.patient_id}")
    lines.append("=" * 78)
    lines.append(f"Measured Total Ca: {p.measured_calcium_mg_dl:.2f} mg/dL ({p.measured_calcium_mmol_l:.2f} mmol/L) | Albumin: {p.albumin_g_dl:.2f} g/dL")
    lines.append(f"Corrected Ca (Payne): {p.corrected_calcium_mg_dl:.2f} mg/dL ({p.corrected_calcium_mmol_l:.2f} mmol/L)")
    lines.append(f"Serum Phosphate: {p.phosphate_mg_dl:.2f} mg/dL ({p.phosphate_mmol_l:.2f} mmol/L)")
    lines.append("-" * 78)
    lines.append(f"CALCIUM-PHOSPHATE PRODUCT: {p.product_mg2_dl2:.2f} (mg/dL)^2 | {p.product_mmol2_l2:.2f} (mmol/L)^2")
    lines.append(f"KDIGO Target (<55.0): {'ACHIEVED [PASS]' if p.kdigo_target_achieved else 'EXCEEDED [FAIL]'}")
    lines.append(f"Clinical Risk Stratum: {p.risk_category.value}")
    lines.append("-" * 78)
    lines.append(f"CALCIPHYLAXIS (CUA) RISK EVALUATION:")
    lines.append(f"  * Hazard Score: {c.hazard_score:.1f} / 100.0 ({c.estimated_risk_tier})")
    if c.active_risk_factors:
        lines.append("  * Identified Risk Factors:")
        for rf in c.active_risk_factors:
            lines.append(f"      - {rf}")

    lines.append("-" * 78)
    lines.append(f"PHOSPHATE BINDER & THERAPEUTIC DIRECTIVE:")
    lines.append(f"  * Class: {rx.recommended_binder_class.value}")
    lines.append(f"  * Calcium-Based Binder Allowed: {'YES' if rx.calcium_binder_permitted else 'NO (Contraindicated)'}")
    lines.append(f"  * Calcimimetic Indication: {'YES (PTH elevated)' if rx.calcimimetic_indicated else 'NO / Baseline'}")
    lines.append(f"  * Rationale: {rx.clinical_rationale}")

    if report.critical_alerts:
        lines.append("-" * 78)
        lines.append("[!] CRITICAL NEPHROLOGY ALERTS:")
        for alert in report.critical_alerts:
            lines.append(f"  * {alert}")

    if report.clinical_advisories:
        lines.append("-" * 78)
        lines.append("[*] CLINICAL ADVISORIES:")
        for adv in report.clinical_advisories:
            lines.append(f"  * {adv}")

    lines.append("=" * 78)
    return "\n".join(lines)
