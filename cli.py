#!/usr/bin/env python3
"""
Command-Line Interface for Calcium-Phosphate Product & CKD-MBD Calculator
=========================================================================
Supports interactive clinical entry, direct parameter evaluation, batch CSV processing,
unit system conversions (US Conventional and SI Metric), and JSON output.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from typing import List, Optional

from calcium_phosphate_product import (
    UnitSystem,
    PatientBiomarkersInput,
    CalciumPhosphateCalculator,
    format_ckd_mbd_report,
)


def run_demo(scenario: str = "all") -> int:
    """Runs pre-configured clinical benchmark scenarios."""
    scenarios = {
        "target_controlled": PatientBiomarkersInput(
            patient_id="DEMO-CKD-CONTROLLED",
            serum_calcium=9.0,
            serum_phosphate=4.5,
            serum_albumin=4.0,
            intact_pth_pg_ml=180.0,
            on_warfarin=False
        ),
        "elevated_high_risk": PatientBiomarkersInput(
            patient_id="DEMO-CKD-ELEVATED",
            serum_calcium=9.8,
            serum_phosphate=6.4,
            serum_albumin=3.8,
            intact_pth_pg_ml=450.0,
            dialysis_vintage_years=4.5
        ),
        "critical_calciphylaxis": PatientBiomarkersInput(
            patient_id="DEMO-CKD-CRITICAL-CUA",
            serum_calcium=10.2,
            serum_phosphate=7.8,
            serum_albumin=2.9,
            intact_pth_pg_ml=680.0,
            on_warfarin=True,
            dialysis_vintage_years=6.0,
            bmi=33.5,
            diabetes=True,
            female_sex=True,
            has_vascular_calcification=True
        ),
        "si_metric_case": PatientBiomarkersInput(
            patient_id="DEMO-SI-METRIC",
            serum_calcium=2.35,  # mmol/L
            serum_phosphate=1.65, # mmol/L
            serum_albumin=38.0,  # g/L
            unit_system=UnitSystem.SI_METRIC
        )
    }

    selected = scenarios.items() if scenario == "all" else [(scenario, scenarios[scenario])] if scenario in scenarios else []
    if not selected:
        print(f"Unknown scenario: {scenario}. Choose from: {list(scenarios.keys())} or 'all'")
        return 1

    for name, bio in selected:
        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        print(format_ckd_mbd_report(rep))
        print("\n")
    return 0


def interactive_mode() -> int:
    """Guides user through interactive clinical biomarker entry."""
    print("=" * 60)
    print(" Calcium-Phosphate Product & CKD-MBD - Interactive Entry")
    print("=" * 60)
    try:
        pat_id = input("Enter Patient ID [PT-2026-001]: ").strip() or "PT-2026-001"
        units_opt = input("Unit system: (1) US Conventional [mg/dL, g/dL], (2) SI Metric [mmol/L, g/L] [1]: ").strip() or "1"
        unit_sys = UnitSystem.SI_METRIC if units_opt == "2" else UnitSystem.US_CONVENTIONAL

        if unit_sys == UnitSystem.US_CONVENTIONAL:
            ca_str = input("Serum Total Calcium (mg/dL) [9.2]: ").strip() or "9.2"
            po4_str = input("Serum Phosphate (mg/dL) [5.0]: ").strip() or "5.0"
            alb_str = input("Serum Albumin (g/dL) [4.0]: ").strip() or "4.0"
        else:
            ca_str = input("Serum Total Calcium (mmol/L) [2.30]: ").strip() or "2.30"
            po4_str = input("Serum Phosphate (mmol/L) [1.60]: ").strip() or "1.60"
            alb_str = input("Serum Albumin (g/L) [40.0]: ").strip() or "40.0"

        ca = float(ca_str)
        po4 = float(po4_str)
        alb = float(alb_str)

        pth_str = input("Intact PTH (pg/mL, or enter to skip): ").strip()
        pth = float(pth_str) if pth_str else None

        warf_str = input("Patient on Warfarin / Coumadin? (y/n) [n]: ").strip().lower()
        warf = warf_str in ("y", "yes", "true", "1")

        vintage_str = input("Dialysis vintage in years [0.0]: ").strip() or "0.0"
        vintage = float(vintage_str)

        bmi_str = input("BMI (kg/m2) [25.0]: ").strip() or "25.0"
        bmi = float(bmi_str)

        dm_str = input("Diabetes Mellitus? (y/n) [n]: ").strip().lower()
        dm = dm_str in ("y", "yes", "true", "1")

        fem_str = input("Female sex? (y/n) [n]: ").strip().lower()
        fem = fem_str in ("y", "yes", "true", "1")

        bio = PatientBiomarkersInput(
            patient_id=pat_id,
            serum_calcium=ca,
            serum_phosphate=po4,
            serum_albumin=alb,
            intact_pth_pg_ml=pth,
            unit_system=unit_sys,
            on_warfarin=warf,
            dialysis_vintage_years=vintage,
            bmi=bmi,
            diabetes=dm,
            female_sex=fem
        )

        rep = CalciumPhosphateCalculator.evaluate_case(bio)
        print("\n" + format_ckd_mbd_report(rep))
        return 0
    except Exception as e:
        print(f"Error during interactive calculation: {e}", file=sys.stderr)
        return 1


def process_batch_csv(input_csv: str, output_csv: Optional[str] = None) -> int:
    """Processes batch CSV file containing patient lab values."""
    try:
        with open(input_csv, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        results = []
        for r in rows:
            pid = r.get("patient_id") or r.get("id") or "PT-001"
            ca = float(r.get("calcium") or r.get("serum_calcium") or 9.0)
            po4 = float(r.get("phosphate") or r.get("serum_phosphate") or 4.5)
            alb = float(r.get("albumin") or r.get("serum_albumin") or 4.0)
            pth_raw = r.get("pth") or r.get("intact_pth")
            pth = float(pth_raw) if pth_raw else None
            warf = str(r.get("on_warfarin", "false")).lower() in ("true", "1", "yes")

            bio = PatientBiomarkersInput(
                patient_id=pid,
                serum_calcium=ca,
                serum_phosphate=po4,
                serum_albumin=alb,
                intact_pth_pg_ml=pth,
                on_warfarin=warf
            )
            rep = CalciumPhosphateCalculator.evaluate_case(bio)
            row_dict = dict(r)
            row_dict["corrected_calcium_mg_dl"] = rep.product_data.corrected_calcium_mg_dl
            row_dict["ca_po4_product_mg2_dl2"] = rep.product_data.product_mg2_dl2
            row_dict["ca_po4_product_mmol2_l2"] = rep.product_data.product_mmol2_l2
            row_dict["kdigo_target_achieved"] = rep.product_data.kdigo_target_achieved
            row_dict["calciphylaxis_hazard_score"] = rep.calciphylaxis_risk.hazard_score
            row_dict["recommended_binder_class"] = rep.pharmacotherapy.recommended_binder_class.name
            results.append(row_dict)

        if output_csv:
            with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
                writer.writeheader()
                writer.writerows(results)
            print(f"Successfully processed {len(results)} records -> {output_csv}")
        else:
            print(json.dumps(results, indent=2))
        return 0
    except Exception as e:
        print(f"Error in batch processing: {e}", file=sys.stderr)
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Calcium-Phosphate Product (Ca x PO4) & CKD-MBD Calculator (KDIGO Guidelines)"
    )
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive clinical mode")
    parser.add_argument("--demo", choices=["target_controlled", "elevated_high_risk", "critical_calciphylaxis", "si_metric_case", "all"], help="Run benchmark demo scenario")
    parser.add_argument("--patient-id", default="PT-001", help="Patient accession identifier")
    parser.add_argument("--calcium", type=float, default=9.0, help="Serum total calcium (mg/dL or mmol/L)")
    parser.add_argument("--phosphate", type=float, default=4.5, help="Serum inorganic phosphate (mg/dL or mmol/L)")
    parser.add_argument("--albumin", type=float, default=4.0, help="Serum albumin (g/dL or g/L)")
    parser.add_argument("--pth", type=float, help="Intact parathyroid hormone PTH (pg/mL)")
    parser.add_argument("--si-units", action="store_true", help="Input values are in SI Metric units (mmol/L and g/L)")
    parser.add_argument("--warfarin", action="store_true", help="Patient is currently receiving Warfarin anticoagulant therapy")
    parser.add_argument("--dialysis-vintage", type=float, default=0.0, help="Duration on chronic dialysis in years")
    parser.add_argument("--bmi", type=float, default=24.0, help="Body Mass Index in kg/m2")
    parser.add_argument("--diabetes", action="store_true", help="Diabetes mellitus present")
    parser.add_argument("--female", action="store_true", help="Female patient sex")
    parser.add_argument("--calcification", action="store_true", help="Known vascular or valvular calcification")

    parser.add_argument("--batch-csv", help="Input CSV file for batch calculation")
    parser.add_argument("--output", "-o", help="Output file path (CSV or JSON)")
    parser.add_argument("--file", "-f", help="Load patient JSON file")
    parser.add_argument("--json", "-j", action="store_true", help="Output report in JSON format")

    args = parser.parse_args(argv)

    if args.interactive:
        return interactive_mode()

    if args.demo:
        return run_demo(args.demo)

    if args.batch_csv:
        return process_batch_csv(args.batch_csv, args.output)

    if args.file:
        with open(args.file, "r") as fp:
            data = json.load(fp)
        unit_sys = UnitSystem(data.get("unit_system", UnitSystem.US_CONVENTIONAL.value))
        bio = PatientBiomarkersInput(
            patient_id=data.get("patient_id", "FILE-PT"),
            serum_calcium=data.get("serum_calcium", 9.0),
            serum_phosphate=data.get("serum_phosphate", 4.5),
            serum_albumin=data.get("serum_albumin", 4.0),
            intact_pth_pg_ml=data.get("intact_pth_pg_ml"),
            unit_system=unit_sys,
            on_warfarin=data.get("on_warfarin", False),
            dialysis_vintage_years=data.get("dialysis_vintage_years", 0.0),
            bmi=data.get("bmi", 24.0),
            diabetes=data.get("diabetes", False),
            female_sex=data.get("female_sex", False),
            has_vascular_calcification=data.get("has_vascular_calcification", False)
        )
    else:
        unit_sys = UnitSystem.SI_METRIC if args.si_units else UnitSystem.US_CONVENTIONAL
        bio = PatientBiomarkersInput(
            patient_id=args.patient_id,
            serum_calcium=args.calcium,
            serum_phosphate=args.phosphate,
            serum_albumin=args.albumin,
            intact_pth_pg_ml=args.pth,
            unit_system=unit_sys,
            on_warfarin=args.warfarin,
            dialysis_vintage_years=args.dialysis_vintage,
            bmi=args.bmi,
            diabetes=args.diabetes,
            female_sex=args.female,
            has_vascular_calcification=args.calcification
        )

    report = CalciumPhosphateCalculator.evaluate_case(bio)

    if args.json:
        out_str = report.to_json()
    else:
        out_str = format_ckd_mbd_report(report)

    if args.output:
        with open(args.output, "w") as fp:
            fp.write(out_str)
    else:
        print(out_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
