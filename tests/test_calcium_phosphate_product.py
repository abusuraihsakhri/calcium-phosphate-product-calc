"""Regression tests for the calcium-phosphate product calculator."""

import csv
import json
import os
import tempfile
import unittest

import cli
from calcium_phosphate_product import (
    BinderClass,
    CalciumPhosphateCalculator,
    PatientBiomarkersInput,
    RiskCategory,
    UnitSystem,
    format_ckd_mbd_report,
)
from calciphylaxis_risk import CalciphylaxisInputs, predict_calciphylaxis_risk
from phosphate_binder_optimizer import BinderContext, select_binder
from trend_analysis import CaPO4Measurement, analyze_caPO4_trend


class TestChemistry(unittest.TestCase):
    def test_us_albumin_adjustment(self):
        bio = PatientBiomarkersInput("P1", 8.0, 4.5, 2.5)
        result = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertAlmostEqual(result.corrected_calcium_mg_dl, 9.2, places=2)

    def test_si_albumin_adjustment(self):
        bio = PatientBiomarkersInput(
            "P2", 2.1, 1.5, 30.0, unit_system=UnitSystem.SI_METRIC
        )
        result = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertAlmostEqual(result.corrected_calcium_mmol_l, 2.3, places=2)

    def test_measured_and_adjusted_products_are_both_reported(self):
        bio = PatientBiomarkersInput("P3", 8.0, 5.0, 2.5)
        result = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertAlmostEqual(result.measured_product_mg2_dl2, 40.0, places=2)
        self.assertAlmostEqual(result.product_mg2_dl2, 46.0, places=2)

    def test_product_unit_conversion(self):
        bio = PatientBiomarkersInput("P4", 10.0, 5.0, 4.0)
        result = CalciumPhosphateCalculator.calculate_product(bio)
        self.assertAlmostEqual(result.product_mmol2_l2, 4.03, places=2)

    def test_historical_threshold_context_below(self):
        result = CalciumPhosphateCalculator.calculate_product(
            PatientBiomarkersInput("P5", 9.0, 5.0, 4.0)
        )
        self.assertTrue(result.historical_kdoqi_below_55)
        self.assertEqual(
            result.risk_category,
            RiskCategory.BELOW_HISTORICAL_KDOQI_THRESHOLD,
        )
        self.assertTrue(result.kdigo_target_achieved)  # compatibility alias only

    def test_historical_threshold_context_above(self):
        result = CalciumPhosphateCalculator.calculate_product(
            PatientBiomarkersInput("P6", 10.0, 6.0, 4.0)
        )
        self.assertFalse(result.historical_kdoqi_below_55)
        self.assertEqual(
            result.risk_category,
            RiskCategory.AT_OR_ABOVE_HISTORICAL_KDOQI_THRESHOLD,
        )

    def test_non_finite_input_rejected(self):
        with self.assertRaises(ValueError):
            CalciumPhosphateCalculator.calculate_product(
                PatientBiomarkersInput("BAD", float("nan"), 4.0, 4.0)
            )

    def test_negative_input_rejected(self):
        with self.assertRaises(ValueError):
            CalciumPhosphateCalculator.calculate_product(
                PatientBiomarkersInput("BAD", -1.0, 4.0, 4.0)
            )


class TestClinicalBoundaries(unittest.TestCase):
    def test_no_calciphylaxis_probability_is_generated(self):
        report = CalciumPhosphateCalculator.evaluate_case(
            PatientBiomarkersInput(
                "P7", 10.0, 7.0, 3.0, on_warfarin=True, diabetes=True
            )
        )
        self.assertIsNone(report.calciphylaxis_risk.hazard_score)
        self.assertEqual(report.calciphylaxis_risk.estimated_risk_tier, "Not estimated")
        self.assertIn("Warfarin exposure", report.calciphylaxis_risk.active_risk_factors)
        self.assertFalse(report.calciphylaxis_risk.warfarin_contraindication_alert)

    def test_no_automated_binder_or_calcimimetic_selection(self):
        report = CalciumPhosphateCalculator.evaluate_case(
            PatientBiomarkersInput("P8", 10.0, 7.0, 4.0, intact_pth_pg_ml=700)
        )
        recommendation = report.pharmacotherapy
        self.assertEqual(
            recommendation.recommended_binder_class,
            BinderClass.NO_AUTOMATED_RECOMMENDATION,
        )
        self.assertIsNone(recommendation.calcium_binder_permitted)
        self.assertIsNone(recommendation.calcimimetic_indicated)

    def test_report_states_current_kdigo_context(self):
        report = CalciumPhosphateCalculator.evaluate_case(
            PatientBiomarkersInput("P9", 9.8, 6.5, 3.6)
        )
        text = format_ckd_mbd_report(report)
        self.assertIn("KDIGO 2017", text)
        self.assertIn("individual serum calcium and phosphate", text)
        self.assertNotIn("CRITICAL NEPHROLOGY ALERTS", text)

    def test_json_serialization(self):
        report = CalciumPhosphateCalculator.evaluate_case(
            PatientBiomarkersInput("JSON", 9.0, 4.5, 4.0)
        )
        data = json.loads(report.to_json())
        self.assertEqual(data["patient_id"], "JSON")
        self.assertIn("measured_product_mg2_dl2", data["product_data"])


class TestAuxiliaryCompatibility(unittest.TestCase):
    def test_calciphylaxis_helper_does_not_emit_probability(self):
        result = predict_calciphylaxis_risk(
            CalciphylaxisInputs(10.0, 7.0, 3.0, warfarin_use=True)
        )
        self.assertIsNone(result["probability_1y"])
        self.assertEqual(result["risk_tier"], "not_estimated")

    def test_binder_helper_does_not_select_medication(self):
        result = select_binder(BinderContext(7.0, 9.5))
        self.assertIsNone(result["selected_binder"])
        self.assertIn("No automated binder selection", result["notes"][0])

    def test_trend_helper_is_descriptive(self):
        result = analyze_caPO4_trend(
            [
                CaPO4Measurement("2026-01-01", 9.0, 4.0),
                CaPO4Measurement("2026-02-01", 9.0, 5.0),
            ]
        )
        self.assertEqual(result["risk_level"], "not_estimated")
        self.assertIsNone(result["calcification_risk_pct"])


class TestCLI(unittest.TestCase):
    def test_direct_json(self):
        self.assertEqual(
            cli.main(
                [
                    "--patient-id",
                    "CLI",
                    "--calcium",
                    "9.5",
                    "--phosphate",
                    "6.0",
                    "--albumin",
                    "3.6",
                    "--json",
                ]
            ),
            0,
        )

    def test_legacy_demo_aliases_still_run(self):
        self.assertEqual(cli.main(["--demo", "target_controlled"]), 0)
        self.assertEqual(cli.main(["--demo", "elevated_high_risk"]), 0)
        self.assertEqual(cli.main(["--demo", "critical_calciphylaxis"]), 0)

    def test_batch_subcommand(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "in.csv")
            output_path = os.path.join(tmpdir, "out.csv")
            with open(input_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "patient_id",
                        "serum_calcium",
                        "serum_phosphate",
                        "serum_albumin",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "patient_id": "ROW1",
                        "serum_calcium": "9.2",
                        "serum_phosphate": "4.8",
                        "serum_albumin": "3.8",
                    }
                )
            self.assertEqual(
                cli.main(["batch", "-i", input_path, "-o", output_path]), 0
            )
            with open(output_path, encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertIn("measured_ca_po4_mg2_dl2", rows[0])
            self.assertIn("historical_kdoqi_below_55", rows[0])

    def test_empty_batch_is_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "empty.csv")
            with open(input_path, "w", encoding="utf-8") as handle:
                handle.write("serum_calcium,serum_phosphate\n")
            self.assertEqual(cli.process_batch_csv(input_path), 1)


if __name__ == "__main__":
    unittest.main()
