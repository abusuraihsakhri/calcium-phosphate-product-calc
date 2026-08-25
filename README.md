# Calcium-Phosphate Product & CKD-MBD Clinical Calculator

A clinical decision-support and computational nephrology engine for calculating the **Calcium-Phosphate Product ($\text{Ca} \times \text{PO}_4$)**, determining **KDIGO/KDOQI** clinical thresholds, modeling **Calciphylaxis (Calcific Uremic Arteriolopathy, CUA)** hazard risk, and guiding phosphate binder pharmacotherapy in Chronic Kidney Disease (CKD) and End-Stage Renal Disease (ESRD).

---

## Clinical Foundation & Mathematical Formulas

In advanced CKD and dialysis patients, dysregulated mineral and bone metabolism leads to calcium-phosphate crystal precipitation in arterial walls and soft tissues.

### 1. Albumin-Corrected Calcium (Payne's Formula)
Because approximately $40-50\%$ of serum calcium is bound to albumin, hypoalbuminemia causes total measured calcium to underestimate ionized/physiologically active calcium:
- **US Conventional Units ($\text{mg/dL}$)**:
  $$\text{Corrected Calcium (mg/dL)} = \text{Total Calcium (mg/dL)} + 0.8 \times (4.0 - \text{Albumin g/dL})$$
- **SI Metric Units ($\text{mmol/L}$)**:
  $$\text{Corrected Calcium (mmol/L)} = \text{Total Calcium (mmol/L)} + 0.02 \times (40.0 - \text{Albumin g/L})$$

### 2. Calcium-Phosphate Product ($\text{Ca} \times \text{PO}_4$)
- **US Conventional**:
  $$\text{Product (mg}^2/\text{dL}^2) = \text{Corrected Calcium (mg/dL)} \times \text{Serum Phosphate (mg/dL)}$$
- **SI Metric Conversion**:
  $$\text{Product (mmol}^2/\text{L}^2) = \text{Corrected Calcium (mmol/L)} \times \text{Serum Phosphate (mmol/L)} \approx \text{Product (mg}^2/\text{dL}^2) \times 0.08056$$

### 3. KDIGO / KDOQI Clinical Risk Strata

| Product Level | Clinical Category | Clinical Implication & Pathophysiology |
| :--- | :--- | :--- |
| **$< 55.0\text{ mg}^2/\text{dL}^2$** | **Target / Controlled** | Normal mineral equilibrium; minimal ectopic precipitation risk. |
| **$55.0 - 69.9\text{ mg}^2/\text{dL}^2$** | **Elevated Risk** | Acceleration of coronary artery and valvular calcification. Increased cardiovascular mortality. |
| **$\ge 70.0\text{ mg}^2/\text{dL}^2$** | **Critical / High Risk** | Spontaneous microvascular calcium-phosphate salt crystallization. High risk for ischemic necrosis and calciphylaxis. |

### 4. Multivariable Calciphylaxis (CUA) Hazard Model
Integrates the $\text{Ca} \times \text{PO}_4$ product with established clinical predispositions:
- **Warfarin Anticoagulation**: Inhibits $\gamma$-carboxylation of Matrix Gla Protein (MGP), a potent endogenous vascular calcification inhibitor.
- **Hyperphosphatemia ($> 5.5\text{ mg/dL}$)** and **Hypoalbuminemia ($< 3.5\text{ g/dL}$)**.
- **Extended Dialysis Vintage ($> 3\text{ years}$)**, **Obesity ($\text{BMI} \ge 30$)**, **Diabetes Mellitus**, and **Female Sex**.

### 5. Guideline-Directed Phosphate Binder Optimization
- **Non-Calcium-Based Binders (Sevelamer, Lanthanum, Sucroferric Oxyhydroxide)**: First-line when $\text{Ca} \times \text{PO}_4 \ge 55\text{ mg}^2/\text{dL}^2$, corrected calcium $\ge 9.5\text{ mg/dL}$, or vascular calcification is present.
- **Calcium-Based Binders (Calcium Acetate)**: Permitted only when corrected calcium is normal/low and $\text{Ca} \times \text{PO}_4 < 55\text{ mg}^2/\text{dL}^2$.
- **Calcimimetics (Cinacalcet, Etelcalcetide)**: Indicated for secondary hyperparathyroidism with intact $\text{PTH} > 300\text{ pg/mL}$.

---

## Installation & Setup

Requires **Python 3.9+** (zero external dependencies).

```bash
git clone https://github.com/abusuraihsakhri/calcium-phosphate-product-calc.git
cd calcium-phosphate-product-calc
```

---

## CLI Usage Examples

### 1. Pre-Configured Benchmark Scenarios

```bash
python cli.py --demo target_controlled
python cli.py --demo elevated_high_risk
python cli.py --demo critical_calciphylaxis
python cli.py --demo si_metric_case
```

### 2. Direct Patient Lab Evaluation with JSON Output

```bash
python cli.py --patient-id PT-2026-881 --calcium 9.8 --phosphate 6.5 \
  --albumin 3.4 --pth 480 --dialysis-vintage 4.0 --json
```

### 3. Batch CSV Patient Cohort Evaluation

```bash
python cli.py --batch-csv hemodialysis_cohort.csv --output evaluated_cohort.csv
```

### 4. Interactive Clinical Mode

```bash
python cli.py --interactive
```

---

## Python API Integration

```python
from calcium_phosphate_product import (
    PatientBiomarkersInput,
    UnitSystem,
    CalciumPhosphateCalculator,
    format_ckd_mbd_report,
)

patient = PatientBiomarkersInput(
    patient_id="HD-PAT-102",
    serum_calcium=10.1,
    serum_phosphate=6.8,
    serum_albumin=3.1,
    intact_pth_pg_ml=520.0,
    on_warfarin=True,
    dialysis_vintage_years=5.5,
    bmi=32.0,
    diabetes=True,
    female_sex=True
)

report = CalciumPhosphateCalculator.evaluate_case(patient)
print(format_ckd_mbd_report(report))
```

---

## Unit Testing

Run the automated test suite with 22 unit test cases:

```bash
python -m unittest test_calcium_phosphate_product.py -v
```

---

## License

MIT License. Authored and maintained by Dr. Abu Suraih Sakhri.
