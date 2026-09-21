#!/usr/bin/env python3
"""Command-line interface for the calcium-phosphate product calculator."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from typing import List, Optional

from calcium_phosphate_product import (
    CalciumPhosphateCalculator,
    PatientBiomarkersInput,
    UnitSystem,
    format_ckd_mbd_report,
)


def run_demo(scenario: str = "all") -> int:
    scenarios = {
        "below_historical_threshold": PatientBiomarkersInput(
            "DEMO-BELOW-55", 9.0, 4.5, 4.0
        ),
        "above_historical_threshold": PatientBiomarkersInput(
            "DEMO-ABOVE-55", 9.8, 6.4, 3.8
        ),
        "si_metric_case": PatientBiomarkersInput(
            "DEMO-SI", 2.25, 1.7, 35.0, unit_system=UnitSystem.SI_METRIC
        ),
    }
    aliases = {
        "target_controlled": "below_historical_threshold",
        "elevated_high_risk": "above_historical_threshold",
        "critical_calciphylaxis": "above_historical_threshold",
    }

    if scenario == "all":
        selected = scenarios.items()
    else:
        key = aliases.get(scenario, scenario)
        selected = [(key, scenarios[key])]

    for name, patient in selected:
        print(f"\n--- {name} ---")
        print(format_ckd_mbd_report(CalciumPhosphateCalculator.evaluate_case(patient)))
    return 0


def interactive_mode() -> int:
    print("Calcium-Phosphate Product Calculator")
    print("Local calculation only. Do not use Ca x P as a standalone treatment target.")
    try:
        ca = float(input("Total calcium (mg/dL): ").strip())
        po4 = float(input("Phosphate (mg/dL): ").strip())
        albumin_raw = input("Albumin (g/dL) [4.0]: ").strip()
        albumin = float(albumin_raw) if albumin_raw else 4.0
        bio = PatientBiomarkersInput(
            patient_id="INTERACTIVE",
            serum_calcium=ca,
            serum_phosphate=po4,
            serum_albumin=albumin,
        )
        print(format_ckd_mbd_report(CalciumPhosphateCalculator.evaluate_case(bio)))
        return 0
    except (ValueError, EOFError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2


def _find_field(row: dict, candidates: List[str]) -> Optional[str]:
    normalized = {
        key.strip().lower().replace(" ", "_").replace("-", "_"): value
        for key, value in row.items()
        if key is not None
    }
    for candidate in candidates:
        candidate = candidate.lower().replace(" ", "_").replace("-", "_")
        if candidate in normalized:
            return normalized[candidate]
    return None


def _as_bool(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def process_batch_csv(input_csv: str, output_csv: Optional[str] = None) -> int:
    try:
        with open(input_csv, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError("input CSV contains no data rows")

        results = []
        for index, row in enumerate(rows, start=1):
            pid = _find_field(row, ["patient_id", "patient id", "id", "accession"]) or f"ROW-{index}"
            ca_raw = _find_field(row, ["total_calcium", "serum_calcium", "calcium", "ca", "v1"])
            po4_raw = _find_field(row, ["serum_phosphate", "phosphate", "phosphorus", "po4", "v3"])
            alb_raw = _find_field(row, ["serum_albumin", "albumin", "alb", "v2"])

            if ca_raw in (None, "") or po4_raw in (None, ""):
                raise ValueError(f"row {index}: calcium and phosphate are required")

            bio = PatientBiomarkersInput(
                patient_id=str(pid),
                serum_calcium=float(ca_raw),
                serum_phosphate=float(po4_raw),
                serum_albumin=float(alb_raw) if alb_raw not in (None, "") else 4.0,
                on_warfarin=_as_bool(_find_field(row, ["on_warfarin", "warfarin"])),
                dialysis_vintage_years=float(
                    _find_field(row, ["dialysis_vintage_years", "dialysis_vintage"]) or 0.0
                ),
                bmi=float(_find_field(row, ["bmi", "body_mass_index"]) or 24.0),
                diabetes=_as_bool(_find_field(row, ["diabetes", "diabetes_mellitus", "dm"])),
                female_sex=_as_bool(_find_field(row, ["female_sex", "female", "is_female"])),
                has_vascular_calcification=_as_bool(
                    _find_field(row, ["has_vascular_calcification", "vascular_calcification"])
                ),
            )
            report = CalciumPhosphateCalculator.evaluate_case(bio)
            p = report.product_data
            out = dict(row)
            out.update(
                {
                    "measured_calcium_mg_dl": p.measured_calcium_mg_dl,
                    "albumin_adjusted_calcium_mg_dl": p.corrected_calcium_mg_dl,
                    "phosphate_mg_dl": p.phosphate_mg_dl,
                    "measured_ca_po4_mg2_dl2": p.measured_product_mg2_dl2,
                    "albumin_adjusted_ca_po4_mg2_dl2": p.product_mg2_dl2,
                    "historical_kdoqi_below_55": p.historical_kdoqi_below_55,
                    "interpretation_note": (
                        "Current KDIGO guidance favors individual calcium/phosphate values "
                        "and serial trends rather than Ca x P as a treatment target."
                    ),
                }
            )
            results.append(out)

        if output_csv:
            fieldnames = list(results[0].keys())
            with open(output_csv, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            print(f"Processed {len(results)} records -> {output_csv}")
        else:
            print(json.dumps(results, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"Batch processing error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate calcium-phosphate product and unit conversions."
    )
    subparsers = parser.add_subparsers(dest="subcommand")
    batch = subparsers.add_parser("batch", help="Process a CSV file")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output")

    parser.add_argument("--interactive", "-i", action="store_true")
    parser.add_argument(
        "--demo",
        choices=[
            "below_historical_threshold",
            "above_historical_threshold",
            "target_controlled",
            "elevated_high_risk",
            "critical_calciphylaxis",
            "si_metric_case",
            "all",
        ],
    )
    parser.add_argument("--patient-id", default="CASE")
    parser.add_argument("--calcium", type=float, default=9.0)
    parser.add_argument("--phosphate", type=float, default=4.5)
    parser.add_argument("--albumin", type=float, default=4.0)
    parser.add_argument("--pth", type=float)
    parser.add_argument("--si-units", action="store_true")
    parser.add_argument("--warfarin", action="store_true")
    parser.add_argument("--dialysis-vintage", type=float, default=0.0)
    parser.add_argument("--bmi", type=float, default=24.0)
    parser.add_argument("--diabetes", action="store_true")
    parser.add_argument("--female", action="store_true")
    parser.add_argument("--calcification", action="store_true")
    parser.add_argument("--batch-csv")
    parser.add_argument("--output", "-o")
    parser.add_argument("--file", "-f")
    parser.add_argument("--json", "-j", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "batch":
        return process_batch_csv(args.input, args.output)
    if args.interactive:
        return interactive_mode()
    if args.demo:
        return run_demo(args.demo)
    if args.batch_csv:
        return process_batch_csv(args.batch_csv, args.output)

    try:
        if args.file:
            with open(args.file, encoding="utf-8") as handle:
                data = json.load(handle)
            bio = PatientBiomarkersInput(
                patient_id=str(data.get("patient_id", "CASE")),
                serum_calcium=float(data["serum_calcium"]),
                serum_phosphate=float(data["serum_phosphate"]),
                serum_albumin=float(data.get("serum_albumin", 4.0)),
                intact_pth_pg_ml=data.get("intact_pth_pg_ml"),
                unit_system=UnitSystem(data.get("unit_system", UnitSystem.US_CONVENTIONAL.value)),
                on_warfarin=bool(data.get("on_warfarin", False)),
                dialysis_vintage_years=float(data.get("dialysis_vintage_years", 0.0)),
                bmi=float(data.get("bmi", 24.0)),
                diabetes=bool(data.get("diabetes", False)),
                female_sex=bool(data.get("female_sex", False)),
                has_vascular_calcification=bool(data.get("has_vascular_calcification", False)),
            )
        else:
            bio = PatientBiomarkersInput(
                patient_id=args.patient_id,
                serum_calcium=args.calcium,
                serum_phosphate=args.phosphate,
                serum_albumin=args.albumin,
                intact_pth_pg_ml=args.pth,
                unit_system=UnitSystem.SI_METRIC if args.si_units else UnitSystem.US_CONVENTIONAL,
                on_warfarin=args.warfarin,
                dialysis_vintage_years=args.dialysis_vintage,
                bmi=args.bmi,
                diabetes=args.diabetes,
                female_sex=args.female,
                has_vascular_calcification=args.calcification,
            )

        report = CalciumPhosphateCalculator.evaluate_case(bio)
        output = report.to_json() if args.json else format_ckd_mbd_report(report)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(output)
        else:
            print(output)
        return 0
    except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
