"""
Unit Test Suite for Calcium-Phosphate Product & CKD-MBD Calculator
===================================================================
Comprehensive verification of Payne albumin-correction formulas, Ca x PO4 products,
KDIGO clinical thresholds, calciphylaxis hazard model, phosphate binder selection, and CLI.
"""

import csv
import json
import os
import tempfile
import unittest

from calcium_phosphate_product import (
    UnitSystem,
    RiskCategory,
    BinderClass,
    PatientBiomarkersInput,
    ProductCalculationResult,
    CalciphylaxisRiskAssessment,
    BinderRecommendation,
    CkdMbdReport,
    CalciumPhosphateCalculator,
    format_ckd_mbd_report,
)
import cli


class TestPayneAlbuminCorrectionAndChemistry(unittest.TestCase):
    """Test albumin correction and unit conversions."""

    def test_corrected_calcium_normal_albumin_us(self):
        # Ca 9.2, Albumin 4.0 -> Corrected Ca = 9.2 + 0.8*(4.0 - 4.0) = 9.2
        bio = PatientBiomarkersInput("P1", serum_calcium=9.2, serum_phosphate=4.0, serum_albumin=4.0)
        res = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertAlmostEqual(res.corrected_calcium_mg_dl, 9.2, places=2)

    def test_corrected_calcium_hypoalbuminemia_us(self):
        # Ca 8.0, Albumin 2.5 -> Corrected Ca = 8.0 + 0.8*(4.0 - 2.5) = 8.0 + 1.2 = 9.2
        bio = PatientBiomarkersInput("P2", serum_calcium=8.0, serum_phosphate=4.5, serum_albumin=2.5)
        res = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertAlmostEqual(res.corrected_calcium_mg_dl, 9.2, places=2)

    def test_corrected_calcium_si_units(self):
        # Ca 2.1 mmol/L, Albumin 30 g/L -> Corrected Ca = 2.1 + 0.02*(40 - 30) = 2.1 + 0.2 = 2.3 mmol/L
        bio = PatientBiomarkersInput("P3", serum_calcium=2.1, serum_phosphate=1.5, serum_albumin=30.0, unit_system=UnitSystem.SI_METRIC)
        res = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertAlmostEqual(res.corrected_calcium_mmol_l, 2.3, places=2)

    def test_product_calculation_math(self):
        # Corrected Ca 9.0, Phosphate 5.0 -> Product = 45.0 mg2/dL2
        bio = PatientBiomarkersInput("P4", serum_calcium=9.0, serum_phosphate=5.0, serum_albumin=4.0)
        res = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertAlmostEqual(res.product_mg2_dl2, 45.0, places=2)
        self.assertTrue(res.kdigo_target_achieved)
        self.assertEqual(res.risk_category, RiskCategory.TARGET_OPTIMAL)

    def test_product_conversion_to_si(self):
        bio = PatientBiomarkersInput("P5", serum_calcium=10.0, serum_phosphate=5.0, serum_albumin=4.0)
        res = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertAlmostEqual(res.product_mg2_dl2, 50.0, places=1)
        # 50.0 * 0.08056 ~ 4.03 mmol2/L2
        self.assertAlmostEqual(res.product_mmol2_l2, 4.03, places=1)


class TestKdigoRiskStratification(unittest.TestCase):
    """Test KDIGO / KDOQI clinical thresholds."""

    def test_kdigo_target_optimal_under_55(self):
        bio = PatientBiomarkersInput("P-OPT", serum_calcium=8.8, serum_phosphate=5.2, serum_albumin=4.0)
        # 8.8 * 5.2 = 45.76 < 55.0
        res = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertTrue(res.kdigo_target_achieved)
        self.assertEqual(res.risk_category, RiskCategory.TARGET_OPTIMAL)

    def test_kdigo_elevated_risk_55_to_70(self):
        bio = PatientBiomarkersInput("P-ELEV", serum_calcium=9.6, serum_phosphate=6.5, serum_albumin=4.0)
        # 9.6 * 6.5 = 62.4
        res = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertFalse(res.kdigo_target_achieved)
        self.assertEqual(res.risk_category, RiskCategory.ELEVATED_RISK)

    def test_kdigo_critical_risk_above_70(self):
        bio = PatientBiomarkersInput("P-CRIT", serum_calcium=10.2, serum_phosphate=7.5, serum_albumin=4.0)
        # 10.2 * 7.5 = 76.5 >= 70.0
        res = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertFalse(res.kdigo_target_achieved)
        self.assertEqual(res.risk_category, RiskCategory.CRITICAL_RISK)


class TestCalciphylaxisHazardModel(unittest.TestCase):
    """Test multivariable calciphylaxis risk scoring."""

    def test_baseline_low_risk(self):
        bio = PatientBiomarkersInput("P-LOW", serum_calcium=9.0, serum_phosphate=4.5, serum_albumin=4.0)
        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        self.assertLess(rep.calciphylaxis_risk.hazard_score, 25.0)
        self.assertEqual(rep.calciphylaxis_risk.estimated_risk_tier, "Low Calciphylaxis Risk")
        self.assertFalse(rep.calciphylaxis_risk.warfarin_contraindication_alert)

    def test_warfarin_hazard_increase_and_alert(self):
        bio = PatientBiomarkersInput("P-WARF", serum_calcium=9.8, serum_phosphate=6.2, serum_albumin=3.2, on_warfarin=True)
        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        self.assertTrue(rep.calciphylaxis_risk.warfarin_contraindication_alert)
        self.assertTrue(any("Warfarin" in f for f in rep.calciphylaxis_risk.active_risk_factors))
        self.assertGreaterEqual(rep.calciphylaxis_risk.hazard_score, 50.0)

    def test_critical_composite_calciphylaxis(self):
        bio = PatientBiomarkersInput(
            patient_id="P-CUA-HIGH",
            serum_calcium=10.5,
            serum_phosphate=8.0,
            serum_albumin=2.8,
            on_warfarin=True,
            dialysis_vintage_years=5.0,
            bmi=34.0,
            diabetes=True,
            female_sex=True
        )
        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        self.assertGreaterEqual(rep.calciphylaxis_risk.hazard_score, 75.0)
        self.assertIn("Critical", rep.calciphylaxis_risk.estimated_risk_tier)
        self.assertTrue(any("CRITICAL" in a for a in rep.critical_alerts))


class TestPhosphateBinderOptimization(unittest.TestCase):
    """Test KDIGO phosphate binder selection rules."""

    def test_calcium_binder_permitted_normal_ca_low_product(self):
        bio = PatientBiomarkersInput("P-BIND-CA", serum_calcium=8.8, serum_phosphate=5.2, serum_albumin=4.0)
        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        self.assertEqual(rep.pharmacotherapy.recommended_binder_class, BinderClass.CALCIUM_BASED)
        self.assertTrue(rep.pharmacotherapy.calcium_binder_permitted)

    def test_non_calcium_binder_mandatory_for_high_product(self):
        bio = PatientBiomarkersInput("P-BIND-NONCA", serum_calcium=9.2, serum_phosphate=6.8, serum_albumin=4.0)
        # Product = 9.2 * 6.8 = 62.56 >= 55.0
        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        self.assertEqual(rep.pharmacotherapy.recommended_binder_class, BinderClass.NON_CALCIUM_BASED)
        self.assertFalse(rep.pharmacotherapy.calcium_binder_permitted)

    def test_non_calcium_binder_mandatory_for_hypercalcemia(self):
        bio = PatientBiomarkersInput("P-BIND-HYPERCA", serum_calcium=10.2, serum_phosphate=4.8, serum_albumin=4.0)
        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        self.assertEqual(rep.pharmacotherapy.recommended_binder_class, BinderClass.NON_CALCIUM_BASED)
        self.assertFalse(rep.pharmacotherapy.calcium_binder_permitted)

    def test_calcimimetic_indicated_elevated_pth(self):
        bio = PatientBiomarkersInput("P-PTH", serum_calcium=9.2, serum_phosphate=5.5, serum_albumin=4.0, intact_pth_pg_ml=550.0)
        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        self.assertTrue(rep.pharmacotherapy.calcimimetic_indicated)


class TestValidationAndReporting(unittest.TestCase):
    """Test validation errors, JSON serialization, and text report formatting."""

    def test_negative_calcium_raises_error(self):
        bio = PatientBiomarkersInput("P-ERR", serum_calcium=-2.0, serum_phosphate=4.0)
        with self.assertRaises(ValueError):
            CalciumPhosphateCalculator.calculate_product(bio)

    def test_negative_phosphate_raises_error(self):
        bio = PatientBiomarkersInput("P-ERR2", serum_calcium=9.0, serum_phosphate=-1.0)
        with self.assertRaises(ValueError):
            CalciumPhosphateCalculator.calculate_product(bio)

    def test_json_and_dict_serialization(self):
        bio = PatientBiomarkersInput("P-JSON", serum_calcium=9.0, serum_phosphate=5.0)
        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        d = rep.to_dict()
        self.assertEqual(d["patient_id"], "P-JSON")
        self.assertIn("product_mg2_dl2", d["product_data"])

        js = rep.to_json()
        parsed = json.loads(js)
        self.assertEqual(parsed["patient_id"], "P-JSON")

    def test_text_report_rendering(self):
        bio = PatientBiomarkersInput("P-RENDER", serum_calcium=9.8, serum_phosphate=6.5)
        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        txt = format_ckd_mbd_report(rep)
        self.assertIn("CKD-MBD & CALCIUM-PHOSPHATE PRODUCT REPORT", txt)
        self.assertIn("P-RENDER", txt)
        self.assertIn("CALCIUM-PHOSPHATE PRODUCT", txt)


class TestCLIExecution(unittest.TestCase):
    """Test CLI commands, demos, and batch CSV processing."""

    def test_cli_demos(self):
        self.assertEqual(cli.main(["--demo", "target_controlled"]), 0)
        self.assertEqual(cli.main(["--demo", "elevated_high_risk"]), 0)
        self.assertEqual(cli.main(["--demo", "critical_calciphylaxis"]), 0)
        self.assertEqual(cli.main(["--demo", "si_metric_case"]), 0)

    def test_cli_direct_args_json(self):
        ret = cli.main([
            "--patient-id", "CLI-PT-01",
            "--calcium", "9.5",
            "--phosphate", "6.0",
            "--albumin", "3.6",
            "--json"
        ])
        self.assertEqual(ret, 0)

    def test_cli_batch_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_in = os.path.join(tmpdir, "patients_in.csv")
            csv_out = os.path.join(tmpdir, "patients_out.csv")
            with open(csv_in, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["patient_id", "calcium", "phosphate", "albumin"])
                writer.writeheader()
                writer.writerow({"patient_id": "PT1", "calcium": "9.0", "phosphate": "4.5", "albumin": "4.0"})
                writer.writerow({"patient_id": "PT2", "calcium": "10.0", "phosphate": "6.5", "albumin": "3.5"})

            ret = cli.main(["--batch-csv", csv_in, "--output", csv_out])
            self.assertEqual(ret, 0)
            self.assertTrue(os.path.exists(csv_out))


if __name__ == "__main__":
    unittest.main()
