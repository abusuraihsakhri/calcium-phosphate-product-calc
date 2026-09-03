# Calcium-Phosphate Product & CKD-MBD Clinical Risk Engine

> **Domain:** Clinical Nephrology, Chronic Kidney Disease-Mineral and Bone Disorder (CKD-MBD), and Calciphylaxis Risk Stratification  
> **Reference Guidelines & Standards:** KDIGO 2017 Clinical Practice Guideline Update for CKD-MBD, KDOQI Guidelines for Bone Metabolism, European Calciphylaxis Network (EuCalNet) Consensus Framework

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-24%20Passed-brightgreen.svg)
![Guideline](https://img.shields.io/badge/KDIGO-2017%20CKD--MBD-darkblue.svg)

</div>

---

## 📖 Overview

In patients with chronic kidney disease (CKD Stages 3–5 and 5D on hemodialysis or peritoneal dialysis), progressive loss of functional nephrons disrupts calcium, phosphate, and parathyroid hormone (PTH) homeostasis. 

Elevated serum calcium and inorganic phosphate concentrations promote passive supersaturation and active hydroxyapatite precipitation in vascular smooth muscle and soft tissue microvasculature. The **calcium-phosphate product ($Ca \times P$)** provides a vital biophysical measure of systemic calcification propensity, vascular mineral stress, and risk of **calcific uremic arteriolopathy (CUA / calciphylaxis)**.

This repository provides an automated, medically validated evaluation engine and command-line interface for:
1. **Payne (1973) Albumin-Corrected Calcium** derivation in US Conventional ($mg/dL$) and SI Metric ($mmol/L$) systems.
2. **Calcium-Phosphate Product ($Ca \times P$)** computation in $(mg/dL)^2$ and $(mmol/L)^2$.
3. **KDIGO / KDOQI Risk Stratification** ($<55\,mg^2/dL^2$ target, $55–69.9\,mg^2/dL^2$ elevated, $\ge 70\,mg^2/dL^2$ critical precipitation risk).
4. **Multivariable Calciphylaxis (CUA) Hazard Scoring**, incorporating warfarin / vitamin K antagonist antagonism (uncarboxylated Matrix Gla Protein), dialysis vintage, hypoalbuminemia, obesity, and diabetes.
5. **Guideline-Directed Pharmacotherapy Optimization**, evaluating calcium-based vs. non-calcium-based phosphate binders (sevelamer carbonate, lanthanum carbonate, sucroferric oxyhydroxide) and calcimimetic titration (cinacalcet, etelcalcetide).

---

## 📐 Clinical Formulations & Biophysical Principles

### 1. Albumin-Corrected Calcium (Payne Formula, 1973)
Because approximately 40–45% of total serum calcium is non-diffusible and bound to serum albumin, hypoalbuminemia artificially lowers measured total calcium despite normal or elevated physiologically active ionized calcium ($Ca^{2+}$).

* **US Conventional Units** (Total Calcium in $mg/dL$, Albumin in $g/dL$):
  $$\text{Corrected } Ca\,(mg/dL) = \text{Total } Ca\,(mg/dL) + 0.8 \times (4.0 - \text{Albumin}\,[g/dL])$$

* **SI Metric Units** (Total Calcium in $mmol/L$, Albumin in $g/L$):
  $$\text{Corrected } Ca\,(mmol/L) = \text{Total } Ca\,(mmol/L) + 0.02 \times (40.0 - \text{Albumin}\,[g/L])$$

### 2. Calcium-Phosphate Product ($Ca \times P$)
$$\text{Product}\,(mg^2/dL^2) = \text{Corrected } Ca\,(mg/dL) \times \text{Phosphate}\,(mg/dL)$$
$$\text{Product}\,(mmol^2/L^2) = \text{Corrected } Ca\,(mmol/L) \times \text{Phosphate}\,(mmol/L)$$
$$\text{Conversion Factor: } 1.0\,(mg/dL)^2 \approx 0.08056\,(mmol/L)^2$$

### 3. KDIGO / KDOQI Clinical Thresholds & Risk Stratification

| Stratum | $Ca \times P$ Threshold | Clinical Implication & Pathophysiology | Recommended Action |
|:---|:---|:---|:---|
| **Target / Controlled** | $< 55.0\,mg^2/dL^2$ ($< 4.43\,mmol^2/L^2$) | Below solubility limit for hydroxyapatite crystallization. | Continue maintenance monitoring, diet counseling, and stable binder therapy. |
| **Elevated Risk** | $55.0 - 69.9\,mg^2/dL^2$ ($4.43 - 5.63\,mmol^2/L^2$) | Accelerated arterial stiffness, medial vascular calcification (Mönckeberg sclerosis), and cardiac valvular calcification. | Restrict calcium-based binders; initiate or titrate non-calcium-based binders; review dialysis prescription. |
| **Critical Hazard** | $\ge 70.0\,mg^2/dL^2$ ($\ge 5.64\,mmol^2/L^2$) | Extreme precipitation potential. Markedly heightened calciphylaxis (calcific uremic arteriolopathy) hazard and thrombotic microvascular occlusion. | Urgent nephrology review: stop calcium binders and active vitamin D; optimize hemodialysis duration/dialysate calcium; screen for cutaneous ischemic lesions. |

### 4. Calcific Uremic Arteriolopathy (Calciphylaxis) Hazard Model
Calciphylaxis is a life-threatening syndrome characterized by calcification of small cutaneous and subcutaneous arterioles leading to painful ischemic necrosis and ulceration. Key risk factors synthesized by the engine include:
* **Elevated $Ca \times P$ Product ($\ge 55$ or $\ge 70\,mg^2/dL^2$)**
* **Severe Hyperphosphatemia ($> 6.5\,mg/dL$)**
* **Warfarin / Coumadin Use:** Antagonizes Vitamin K, preventing carboxylation of **Matrix Gla Protein (MGP)**, the potent vascular calcification inhibitor.
* **Hypoalbuminemia ($< 3.5\,g/dL$):** Marker of chronic systemic inflammation (MIA syndrome).
* **Dialysis Vintage ($\ge 3$ years):** Cumulative exposure to uremic toxins and bioincompatible dialyzers.
* **Female Sex, Obesity (BMI $\ge 30$), and Diabetes Mellitus.**

---

## 💻 CLI Quickstart & Usage

### 1. Batch CSV Processing
Process patient cohort records containing lab values and clinical indicators:

```bash
# Using the batch subcommand:
python cli.py batch -i sample.csv -o results.csv

# Or using the top-level batch flag:
python cli.py --batch-csv sample.csv --output results.csv
```

### 2. Single-Patient Parameterized Evaluation
Directly evaluate a patient from the command line:

```bash
python cli.py \
  --patient-id "PT-CKD5D-101" \
  --calcium 9.8 \
  --phosphate 6.5 \
  --albumin 3.2 \
  --pth 480 \
  --dialysis-vintage 4.0 \
  --warfarin \
  --calcification
```

Output format options include rich text terminal summary or structured JSON:
```bash
python cli.py --patient-id "PT-101" --calcium 10.2 --phosphate 7.2 --albumin 3.0 --json
```

### 3. Pre-Configured Clinical Demo Scenarios
Run benchmark clinical scenarios matching KDIGO archetypes:

```bash
# Run all benchmark scenarios:
python cli.py --demo all

# Specific scenario:
python cli.py --demo critical_calciphylaxis
python cli.py --demo target_controlled
python cli.py --demo si_metric_case
```

### 4. Interactive Clinical Entry Mode
```bash
python cli.py -i
```

---

## 🐍 Python Library Quickstart

```python
from calcium_phosphate_product import (
    CalciumPhosphateCalculator,
    PatientBiomarkersInput,
    UnitSystem,
    format_ckd_mbd_report,
)

# Initialize patient biomarkers
patient = PatientBiomarkersInput(
    patient_id="CKD-HD-409",
    serum_calcium=9.6,          # mg/dL
    serum_phosphate=6.8,        # mg/dL
    serum_albumin=3.4,          # g/dL
    intact_pth_pg_ml=520.0,     # pg/mL
    on_warfarin=True,
    dialysis_vintage_years=4.5,
    bmi=31.2,
    diabetes=True,
    female_sex=True,
    has_vascular_calcification=True,
)

# Compute CKD-MBD case synthesis
report = CalciumPhosphateCalculator.evaluate_case(patient)

print(f"Corrected Calcium: {report.product_data.corrected_calcium_mg_dl:.2f} mg/dL")
print(f"Ca x PO4 Product:  {report.product_data.product_mg2_dl2:.2f} (mg/dL)^2")
print(f"KDIGO Target Met:  {report.product_data.kdigo_target_achieved}")
print(f"Risk Tier:         {report.calciphylaxis_risk.estimated_risk_tier}")
print(f"Hazard Score:      {report.calciphylaxis_risk.hazard_score}/100")
print(f"Rx Binder Class:   {report.pharmacotherapy.recommended_binder_class.name}")
print(f"Rx Rationale:      {report.pharmacotherapy.clinical_rationale}")

# Render complete consultation dossier
print(format_ckd_mbd_report(report))
```

---

## 📊 CSV Input Schema (`sample.csv`)

The batch processor accepts standard clinical CSV headers with flexible column aliases:

| Column Header | Type | Description / Units |
|:---|:---|:---|
| `patient_id` | string | Unique patient medical record number or accession ID |
| `ckd_stage` | string | CKD Stage (`Stage 1` through `Stage 5D`) |
| `serum_calcium` | float | Measured total calcium ($mg/dL$ or $mmol/L$) |
| `serum_albumin` | float | Serum albumin ($g/dL$ or $g/L$) |
| `serum_phosphate` | float | Serum inorganic phosphate ($mg/dL$ or $mmol/L$) |
| `intact_pth` | float | Intact parathyroid hormone ($pg/mL$) |
| `on_warfarin` | boolean | Patient receiving warfarin/coumadin (`true`/`false`) |
| `dialysis_vintage_years` | float | Years on maintenance renal replacement therapy |
| `bmi` | float | Body Mass Index ($kg/m^2$) |
| `diabetes` | boolean | Diabetes mellitus diagnosis (`true`/`false`) |
| `female_sex` | boolean | Female biologic sex (`true`/`false`) |
| `has_vascular_calcification`| boolean | Imaging-confirmed vascular or valvular calcification |

---

## 🧪 Testing & Verification

Run the comprehensive unit test suite:

```bash
python -m pytest -p no:zarr -v
```

Execute CLI batch smoke test:

```powershell
python cli.py batch -i sample.csv -o out_smoke.csv; Remove-Item -Path "out_smoke.csv" -Force -ErrorAction SilentlyContinue
```

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
