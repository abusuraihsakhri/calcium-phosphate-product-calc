# Calcium-Phosphate Product Calculator

### [Open the Live Application →](https://abusuraihsakhri.github.io/calcium-phosphate-product-calc/)

A small browser and Python utility for calculating the calcium-phosphate product (Ca × P), converting between US conventional and SI units, and optionally showing an albumin-adjusted calcium estimate.

## Clinical scope

This repository performs arithmetic and unit conversion. It does **not** diagnose CKD-MBD, estimate an individual calciphylaxis probability, or select/dose phosphate binders or calcimimetics.

KDIGO 2017 recommends using the individual serum calcium and phosphate values together, with serial trends and the broader CKD-MBD assessment, rather than using the mathematical Ca × P product as a treatment target. The older KDOQI 2003 Ca × P threshold of 55 mg²/dL² is retained only as historical context.

Albumin-adjusted calcium is a legacy estimate and can be inaccurate in CKD, critical illness, and marked hypoalbuminemia. Ionized calcium should be used when an accurate physiologic calcium assessment is clinically important.

## Features

- Static browser calculator with no backend
- Light theme with dark-mode option
- US conventional and SI unit systems
- Measured and albumin-adjusted Ca × P values shown separately
- Python API and command-line interface
- CSV batch processing
- Standard-library runtime with no third-party Python dependencies
- Automated tests on Python 3.10–3.13

## Browser use

The application is a single static `index.html` file. All calculations run locally in the browser. Enter total calcium, phosphate, and albumin, then select **Calculate**.

The browser application does not transmit or persist clinical input values. Only the theme preference may be stored locally by the browser.

## Command line

Direct calculation:

```bash
python cli.py --calcium 9.2 --phosphate 4.8 --albumin 3.6
```

JSON output:

```bash
python cli.py --calcium 9.2 --phosphate 4.8 --albumin 3.6 --json
```

SI input:

```bash
python cli.py --si-units --calcium 2.30 --phosphate 1.45 --albumin 40
```

Batch CSV:

```bash
python cli.py batch -i sample.csv -o results.csv
```

The batch processor accepts common aliases such as `serum_calcium`, `calcium`, `serum_phosphate`, `phosphate`, `serum_albumin`, and `albumin`.

## Python API

```python
from calcium_phosphate_product import (
    CalciumPhosphateCalculator,
    PatientBiomarkersInput,
)

case = PatientBiomarkersInput(
    patient_id="CASE",
    serum_calcium=9.2,
    serum_phosphate=4.8,
    serum_albumin=3.6,
)

report = CalciumPhosphateCalculator.evaluate_case(case)

print(report.product_data.measured_product_mg2_dl2)
print(report.product_data.product_mg2_dl2)
```

## Development

Runtime code uses the Python standard library only. Tests use `pytest`.

```bash
python -m pip install pytest
python -m compileall -q .
python -m pytest -q
python cli.py batch -i sample.csv -o out_smoke.csv
```

GitHub Actions runs the test suite on Python 3.10, 3.11, 3.12, and 3.13. A separate workflow deploys `index.html` to GitHub Pages from `master`.

## Technology and browser compatibility

- Python 3.10+
- HTML5, CSS, and vanilla JavaScript
- No JavaScript framework or WebAssembly runtime
- Current versions of Chrome, Edge, Firefox, and Safari

Pyodide/PyScript is unnecessary here because the browser calculation is small and can be reproduced directly in JavaScript without downloading a Python runtime.

## References

- [KDIGO CKD-MBD guideline resources](https://kdigo.org/guidelines/ckd-mbd/)
- KDIGO 2017 recommendation 3.1.5: use individual serum calcium and phosphate values together rather than Ca × P to guide clinical practice.
- KDIGO 2017 recommendations 4.1.1–4.1.6: base treatment on serial calcium, phosphate, and PTH assessments; lower elevated phosphate toward normal; avoid hypercalcemia; and restrict calcium-based binder dose in adults receiving phosphate-lowering treatment.

## License

MIT License. See [LICENSE](LICENSE).
