# Beverage Quality Analysis System (BQAS)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![Pytest](https://img.shields.io/badge/Tests-189%20Passed-brightgreen.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

The **Beverage Quality Analysis System (BQAS)** is an evidence-based beverage analysis platform that evaluates the nutritional profile, health impacts, benchmark percentiles, and sensory quality of five beverage categories:
- **Soft Drinks**
- **Beer**
- **Wine**
- **Spirits / Alcohol**
- **Energy Drinks**

BQAS provides transparent, evidence-grounded reports comparing beverage composition against published health limits (WHO, EFSA, FDA, JECFA/Codex) and empirical reference distributions ($n \ge 100$) from Open Food Facts, USDA FoodData Central, and UCI Wine Quality.

---

## Key Capabilities

1. **Deterministic PRD Section 12 Scoring Engine**:
   - **Guideline Ratios & 5-Band Piecewise Curve:**
     - $r \le 0.5 \implies 100$ (*Favourable*)
     - $0.5 < r \le 1.0 \implies 100 - (r - 0.5) \times 80$ (*Moderate*)
     - $1.0 < r \le 2.0 \implies 60 - (r - 1.0) \times 40$ (*Caution*)
     - $2.0 < r \le 3.0 \implies 20 - (r - 2.0) \times 20$ (*High*)
     - $r > 3.0 \implies 0$ (*High*)
   - **Score Separation:** Strictly isolates **Health Impact Score** (guideline-weighted subscores) and **Composition Score** (empirical benchmark credits matrix).
   - **Critical Overrides:** Automatically caps Health Impact Score at $40$ with structured red banner metadata if methanol exceeds category thresholds or single-dose caffeine boundaries are breached, while preserving underlying raw scores for clinical auditability.
   - **Personalization Scaling:** Tailors guideline limits for adults, minors (under 18: $3\text{ mg/kg}$ caffeine, alcohol avoid warnings), pregnancy ($200\text{ mg}$ caffeine cap, alcohol avoid warnings), and weight-dependent limits ($\text{mg/kg/day}$ for sodium benzoate and sulphites).
   - **Confidence & Partial Analysis:** Computes confidence rating (High $\ge 80\%$, Medium $60\%..79\%$, Low $< 60\%$) and labels sparse inputs as `'Partial analysis'`.
   - **Null Value Safety:** Preserves missing and blank inputs as `null`. Values are **never** zero-imputed.

2. **External Nutritional Providers & Data Quality**:
   - Asynchronous providers for **Open Food Facts** and **USDA FoodData Central**.
   - Plausibility bound checks and explicit missing-nutrient warning generation.

3. **Wine Quality Machine Learning Engine**:
   - Separate scikit-learn regressors for Portuguese Vinho Verde red and white wines.
   - Strict 11 physicochemical feature validation: predictions are only evaluated when all 11 attributes are provided; clear diagnostic reasons are returned if incomplete.
   - Complete isolation from health and composition scoring.

4. **Comprehensive Automated Verification**:
   - **189 tests passing with 0 failures**.
   - Automated test fixtures for all ten PRD Section 18.1 acceptance criteria (**T1–T10**).
   - 48 boundary, percentile, risk direction, and API integration tests.

---

## Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── engine/
│   │   │   ├── scoring_engine.py       # PRD Section 12 deterministic scoring engine
│   │   │   ├── normalization.py        # Input normalization and unit conversion
│   │   │   ├── composition.py          # Physical and chemical calculations
│   │   │   ├── health_impact.py        # Health impact evaluation rules
│   │   │   ├── analysis.py             # Composition analysis orchestrator
│   │   │   ├── composition_scoring.py  # Reference dataset benchmark comparator
│   │   │   ├── evidence_registry.py    # Scientific literature citations registry
│   │   │   ├── data_quality.py         # Provider data quality & plausible bounds
│   │   │   ├── wine_quality.py         # UCI Vinho Verde ML inference service
│   │   │   └── wine_models/            # Trained Joblib model pipelines & model card
│   │   ├── providers/
│   │   │   ├── open_food_facts.py      # Open Food Facts API provider
│   │   │   └── usda_food_data.py       # USDA FoodData Central API provider
│   │   ├── routes/
│   │   │   ├── health.py               # GET /api/health
│   │   │   ├── beverages.py            # GET /api/beverage-types, POST /api/analyze
│   │   │   ├── scoring.py              # POST /api/scoring/evaluate, GET rules/benchmarks
│   │   │   ├── products.py             # GET /api/products/search, /api/products/{id}
│   │   │   └── wine.py                 # POST /api/wine/predict, GET /api/wine/model-card
│   │   ├── schemas/                    # Pydantic v2 data contracts
│   │   └── main.py                     # FastAPI application entry point
│   ├── data/
│   │   ├── rules.json                  # Centralized guideline limits, weights, critical rules
│   │   └── reference_ranges.json       # Benchmark percentiles (P5, P25, P50, P75, P95, n >= 100)
│   ├── tests/                          # 189 Pytest unit and acceptance test suites
│   └── requirements.txt
├── docs/
│   ├── SCORING_ENGINE_SPEC.md          # Technical and mathematical engine specification
│   ├── T1_T10_ACCEPTANCE_REPORT.md     # Acceptance report for all 10 PRD criteria
│   ├── STEP_6_IMPLEMENTATION_REPORT.md # Step 6 delivery report and verification summary
│   └── IMPLEMENTATION_STATUS.md        # Architecture audit and implementation status
├── .gitignore
└── README.md
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.11, 3.12, or newer

### 2. Environment Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`
- ReDoc Alternative: `http://localhost:8000/redoc`

### 4. Run the Test Suite
```bash
pytest -v
```
All 189 tests will run, including unit tests, API integration tests, and the T1–T10 acceptance fixtures.

---

## API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health check and runtime status |
| `GET` | `/api/beverage-types` | Returns supported beverage categories |
| `POST` | `/api/scoring/evaluate` | Deterministic PRD Section 12 scoring pipeline |
| `GET` | `/api/scoring/rules` | Returns centralized rules, limits, and sources |
| `GET` | `/api/scoring/benchmarks` | Returns reference percentile distributions ($n \ge 100$) |
| `POST` | `/api/analyze` | Multi-category composition analysis |
| `GET` | `/api/products/search` | Search non-alcoholic beverages via Open Food Facts / USDA |
| `GET` | `/api/products/{id}` | Detailed product lookup |
| `GET` | `/api/data-sources` | External data provider provenance |
| `POST` | `/api/wine/predict` | UCI Portuguese Vinho Verde wine sensory quality estimation |
| `GET` | `/api/wine/model-card` | Model card with MAE, RMSE, $R^2$, and training provenance |

---

## Documentation

- [Scoring Engine Specification](docs/SCORING_ENGINE_SPEC.md)
- [T1–T10 Acceptance Test Fixtures Report](docs/T1_T10_ACCEPTANCE_REPORT.md)
- [Step 6 Implementation Report](docs/STEP_6_IMPLEMENTATION_REPORT.md)
- [Architecture & Status](docs/IMPLEMENTATION_STATUS.md)

---

## License

This project is licensed under the MIT License.
