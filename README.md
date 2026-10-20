# Beverage Quality Analysis System (BQAS)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg)](https://vitejs.dev/)
[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-189%20Passed-brightgreen.svg)](https://docs.pytest.org/)
[![Frontend Tests](https://img.shields.io/badge/Frontend%20Tests-12%20Passed-brightgreen.svg)](https://nodejs.org/api/test.html)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

The **Beverage Quality Analysis System (BQAS)** is an evidence-based beverage intelligence platform that evaluates the nutritional density, guideline compliance, benchmark distributions, and sensory quality of five beverage categories:
- **Soft Drinks**
- **Beer & Ales**
- **Wine (Red & White)**
- **Spirits / Alcohol**
- **Energy Drinks**

BQAS provides transparent, evidence-grounded reports comparing beverage composition against published health boundaries (WHO, EFSA, FDA, JECFA/Codex) and empirical reference distributions ($n \ge 100$) from Open Food Facts, USDA FoodData Central, and UCI Wine Quality.

---

## Key System Architecture

### 1. Deterministic PRD Section 12 Scoring Engine
- **Strict Score Separation**: Health Impact Score (clinical guideline evaluation) and Composition Score (empirical category percentiles) remain completely separate. They are never combined into a single score.
- **Guideline Piecewise 5-Band Penalties**:
  - $r \le 0.5 \implies 100$ (*Favourable*)
  - $0.5 < r \le 1.0 \implies 100 - (r - 0.5) \times 80$ (*Moderate*)
  - $1.0 < r \le 2.0 \implies 60 - (r - 1.0) \times 40$ (*Caution*)
  - $2.0 < r \le 3.0 \implies 20 - (r - 2.0) \times 20$ (*High*)
  - $r > 3.0 \implies 0$ (*High*)
- **Critical Overrides**: Capped at $40$ with explicit reasons when toxic methanol exceeds $10.0\text{ g/L pure alcohol}$ or acute single-dose caffeine exceeds $200\text{ mg}$ (or $3\text{ mg/kg}$ in minors).
- **Zero Null Imputation**: Unentered, missing, or omitted fields remain `null`. Values are **never** assumed or imputed as zero.
- **Personalization Rules**: Scales limits for minors (under 18: $3\text{ mg/kg}$ caffeine cap, alcohol avoid warnings), pregnancy ($200\text{ mg}$ caffeine cap, alcohol contraindication), and body weight (sodium benzoate ADI $5\text{ mg/kg}$, sulphites ADI $0.7\text{ mg/kg}$).
- **Standard Drink Equivalents**: Computes pure alcohol mass via ethanol density ($0.789\text{ g/mL}$) and WHO standard drink units ($10.0\text{ g}$).

### 2. Modern Health-Tech Web Application
- **Luminescent Precision Design System**: Tailored CSS tokens, squircle curves, subtle frosted-glass overlays, and light, dark, and system themes.
- **Collapsible Responsive Shell**: Desktop navigation rail (auto-open $\ge 1024\text{ px}$) and mobile drawer with focus locking and accessibility scrim.
- **Interactive Lab Wizard**:
  - Beverage category selection with default canonical serving sizes.
  - Quick product catalog & barcode importer from Open Food Facts / USDA FoodData with editable imported fields.
  - Non-blocking plausibility warnings and back-navigation persistence.
- **Scientific Result Dashboard**:
  - Radial SVG ScoreGauges with numeric scores and qualitative bands.
  - Critical warning alert banner with specific clinical reasons.
  - Higher and Lower than Typical panels reflecting nutrient risk directions.
  - Clinical ingredient assessment table with sources and threshold links.
  - Dynamic SVG Guideline Limit & Benchmark Quartile charts.
  - Portuguese Vinho Verde sensory quality ML score with held-out test MAE.
  - One-click native PDF generation and printing.
- **Local-First Privacy**:
  - Saved reports persist in LocalStorage (`bqas_history_v1`) without transmitting personal biometric data to remote analytics.
  - Malformed or outdated stored records are handled safely without crashing.

---

## Repository Layout

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
│   │   │   ├── open_food_facts.py      # Open Food Facts API provider & barcode lookup
│   │   │   └── usda_food_data.py       # USDA FoodData Central API provider
│   │   ├── routes/
│   │   │   ├── health.py               # GET /api/health
│   │   │   ├── beverages.py            # GET /api/beverage-types, POST /api/analyze
│   │   │   ├── scoring.py              # POST /api/scoring/evaluate, GET rules/benchmarks
│   │   │   ├── products.py             # GET /api/product-search, GET /api/product/{barcode}, /api/reference/{category}
│   │   │   └── wine.py                 # POST /api/wine/predict, GET /api/wine/model-card
│   │   ├── schemas/                    # Pydantic v2 data contracts
│   │   └── main.py                     # FastAPI application entry point
│   ├── data/
│   │   ├── rules.json                  # Centralized guideline limits, weights, critical rules
│   │   └── reference_ranges.json       # Benchmark percentiles (P5, P25, P50, P75, P95, n >= 100)
│   ├── tests/                          # 189 Pytest unit and acceptance test suites (T1-T10)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── charts/                 # GuidelineChart.tsx, BenchmarkRangeChart.tsx
│   │   │   ├── common/                 # ScoreGauge.tsx
│   │   │   ├── lab/                    # IngredientForm.tsx, PersonalizationPanel.tsx
│   │   │   └── layout/                 # Navbar.tsx, Sidebar.tsx
│   │   ├── pages/
│   │   │   ├── HomePage.tsx            # Dashboard, score explainer, recent scans
│   │   │   ├── DrinksPage.tsx          # 5 category matrices, percentiles, citations
│   │   │   ├── LabPage.tsx             # Multi-step wizard, barcode import, evaluation
│   │   │   ├── ResultPage.tsx          # Clinical scientific report, SVG charts, PDF export
│   │   │   ├── HistoryPage.tsx         # Local guest history with filters and deletion
│   │   │   ├── SearchPage.tsx          # Unified category, glossary, history, and product search
│   │   │   ├── AccountPage.tsx         # Guest session overview and privacy status
│   │   │   ├── SettingsPage.tsx        # Themes, regional baselines, standard drink definitions
│   │   │   └── AboutPage.tsx           # Methodology, scoring weights, data sources, disclaimers
│   │   ├── services/
│   │   │   ├── api.ts                  # Centralized typed API client with 10s timeouts
│   │   │   ├── historyService.ts       # Local-first persistence with safe sanitization
│   │   │   ├── settingsService.ts      # Theme and regulatory preference manager
│   │   │   └── pdfService.ts           # PDF printing service
│   │   ├── styles/                     # tokens.css, global.css
│   │   ├── test/                       # 12 Node.js acceptance tests
│   │   ├── types/                      # TypeScript contracts matching backend schemas
│   │   ├── App.tsx                     # Main layout & routing shell
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── docs/                               # Architectural and acceptance reports
├── .env.example
├── .gitignore
└── README.md
```

---

## Getting Started

### 1. Prerequisites
- **Python**: 3.11 or newer
- **Node.js**: v18 or newer (v20+ recommended)

---

### 2. Backend Setup & Startup
```powershell
# Navigate to backend directory
cd "d:\wine qualt\backend"

# Activate Python virtual environment
.\.venv\Scripts\activate
# (On macOS/Linux: source .venv/bin/activate)

# Install backend dependencies
pip install -r requirements.txt

# Start FastAPI development server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- Interactive API Documentation: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/health`

---

### 3. Frontend Setup & Startup
```powershell
# Navigate to frontend directory in a new terminal
cd "d:\wine qualt\frontend"

# Install frontend dependencies (if not already installed)
npm install

# Start Vite dev server
npm run dev
```
- Frontend Web Application: **http://localhost:5173/**
- Vite proxies all `/api/*` calls directly to the FastAPI server at `http://127.0.0.1:8000`.

---

## Automated Test Suites

### Backend Tests (`pytest`)
Executes all unit tests, provider parsing tests, scoring tests, and acceptance fixtures T1 through T10:
```powershell
cd "d:\wine qualt\backend"
.\.venv\Scripts\pytest -v
```
**Result:** **189 passed** in 9.06s.

### Frontend Integration Tests (`npm test`)
Executes the automated end-to-end and integration test suite:
```powershell
cd "d:\wine qualt\frontend"
npm test
```
**Result:** **12 passed** in 235ms:
1. Category definitions & canonical serving units.
2. Sidebar sequence & Drinks dropdown hierarchy.
3. Lab preselection queries and clean state reset.
4. Input validation and non-zero blank preservation.
5. Alcohol mass and standard drink calculations.
6. Score separation (Health Impact vs. Composition).
7. Critical override capping at 40 with reasons.
8. Benchmark reliability threshold enforcement ($n \ge 100$).
9. Product search and barcode lookup response parsing.
10. Wine model 11-feature validation and unavailable state.
11. Local history corrupted data sanitization.
12. API timeout handling (10s abort).

### Frontend Production Build (`npm run build`)
```powershell
cd "d:\wine qualt\frontend"
npm run build
```
**Result:** Production bundle compiled with **0 TypeScript errors, 0 lint warnings**.

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health check and runtime status |
| `POST` | `/api/scoring/evaluate` | PRD Section 12 scoring pipeline (Scores, overrides, confidence) |
| `GET` | `/api/scoring/rules` | Centralized guideline limits, weights, and sources |
| `GET` | `/api/scoring/benchmarks` | Full reference percentile distributions ($n \ge 100$) |
| `GET` | `/api/reference/{category}` | Category-specific benchmark percentiles, sample sizes, and metadata |
| `GET` | `/api/product-search` | Search non-alcoholic beverages via Open Food Facts / USDA |
| `GET` | `/api/product/{barcode}` | Retrieve product information by numerical barcode |
| `POST` | `/api/wine/predict` | Portuguese Vinho Verde wine sensory quality estimation (11 features) |
| `GET` | `/api/wine/model-card` | Model card with MAE, RMSE, $R^2$, and training metadata |
| `GET` | `/api/data-sources` | External data provider provenance |

---

## Known Limitations

1. **Wine ML Generalizability**: The scikit-learn sensory regression model was trained on the UCI Portuguese Vinho Verde dataset. It predicts organoleptic expert panel scores and does not generalize to other wine varietals or production regions. It is explicitly separated from health assessments.
2. **Product Lookup Scope**: Packaged product lookup (Open Food Facts / USDA FoodData) is scoped to soft drinks and energy drinks. In accordance with public health guidance, automated external recommendations are not provided for alcoholic beverages.
3. **Local-First Guest Mode**: Cloud multi-user authentication is intentionally not enabled in this version. Scanned reports and preferences are stored privately in browser LocalStorage.

---

## License

This project is licensed under the MIT License.
