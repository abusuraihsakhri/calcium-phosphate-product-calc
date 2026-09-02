# Calcium Phosphate Product Calc

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Calciphylaxis risk model integrating the calcium-phosphate product with
published clinical risk factors.

Core chemistry:
    Ca x PO4 product (mg^2/dL^2) = serum calcium x serum phosphate
    Corrected calcium = measured Ca + 0.8 x (4.0 - albumin g/dL)
    KDIGO safety target: product < 55.5 mg^2/dL^2 (~4.52 mmol^2/L^2);
    historical ectopic-calcification risk rises above ~70 mg^2/dL^2

The logistic risk model combines the product with factors repeatedly
associated with calciphylaxis in dialysis cohorts (warfarin exposure,
hypoalbuminemia, obesity, diabetes, female sex, long dialysis vintage,
hypotensive episodes). Weights are heuristic syntheses of published odds
ratios, not a validated instrument; output supports triage, not diagnosis.

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

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`CalciphylaxisInputs`** — dedicated module for calciphylaxis inputs evaluation and state verification.
- **`UnitSystem`** — dedicated module for unit system evaluation and state verification.
- **`RiskCategory`** — dedicated module for risk category evaluation and state verification.
- **`BinderClass`** — dedicated module for binder class evaluation and state verification.
- **`PatientBiomarkersInput`**: Clinical laboratory input for CKD-MBD and Ca x PO4 evaluation.
- **`ProductCalculationResult`**: Derived chemistry, albumin correction, and unit conversions.

---

## 📐 Mathematical Formulation & Logic

```text
  Payne's formula: Corrected Ca = Measured Ca + 0.8 * (4.0 - Albumin)
  """Calculates multivariable Calciphylaxis Hazard Index."""
  hazard_score = min(100.0, round(hazard, 1))
  calc_res = cls.calculate_product(biomarkers)
  vascular_calcification_risk = caPO4_product * (1 + (params.egfr < 30) * 0.5)
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --interactive <value> --demo <value> --patient-id <value> --calcium <value>
```

### Parameter Reference
- `--interactive`: Specifies input measurement or parameter value.
- `--demo`: Specifies input measurement or parameter value.
- `--patient-id`: Specifies input measurement or parameter value.
- `--calcium`: Specifies input measurement or parameter value.
- `--phosphate`: Specifies input measurement or parameter value.
- `--albumin`: Specifies input measurement or parameter value.
- `--pth`: Specifies input measurement or parameter value.
- `--si-units`: Specifies input measurement or parameter value.
- `--warfarin`: Specifies input measurement or parameter value.
- `--dialysis-vintage`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t calcium-phosphate-product-calc .
docker run -p 8000:8000 calcium-phosphate-product-calc
```
