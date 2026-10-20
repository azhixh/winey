# Beverage Quality Analysis System (BQAS) - Backend (Step 5)

FastAPI-powered backend service for the **Beverage Quality Analysis System (BQAS)**. 

**Step 5** implements a rigorously trained, properly evaluated machine-learning model predicting wine sensory quality ratings from 11 physicochemical laboratory metrics:
- **Official UCI Dataset**: Trained on the official UCI Wine Quality dataset (Cortez et al., 2009).
- **Separate Red & White Pipelines**: Distinguishes red and white wine chemistry (phenolic profiles, sulfur dioxide dynamics, and volatile acidity baselines).
- **Leakage-Free Preprocessing**: 80/20 train/test split with `StandardScaler` fitted exclusively on training folds inside scikit-learn pipelines.
- **Empirical Evaluation**: Evaluates actual MAE, RMSE, and $R^2$ on held-out test data, outperforming dummy mean baselines and linear ridge models.
- **Model Card & Artifacts**: Serialized via Joblib and JSON model card with full provenance, training parameters, and known limitations.
- **Strict Input Validation**: Rejects missing, non-finite, and physically impossible inputs. Never imputes missing values with zero.
- **Explicit Disclaimers**: Clarifies regional specificity to Portuguese *Vinho Verde* wines and strictly separates sensory quality estimation from composition and health assessments.

---

## 📋 Table of Contents

- [Overview & Architecture](#overview--architecture)
- [Directory Structure](#directory-structure)
- [Step 5 Wine Quality Machine Learning Model](#step-5-wine-quality-machine-learning-model)
  - [1. Dataset & Provenance](#1-dataset--provenance)
  - [2. Model Architecture & Preprocessing Pipeline](#2-model-architecture--preprocessing-pipeline)
  - [3. Evaluation Results (Held-Out Test Data)](#3-evaluation-results-held-out-test-data)
  - [4. Model Card Artifacts & Storage](#4-model-card-artifacts--storage)
  - [5. Disclaimers & Known Limitations](#5-disclaimers--known-limitations)
- [Step 4 Evidence-Based Scoring Framework](#step-4-evidence-based-scoring-framework)
- [Step 3 Nutritional Data Providers & Scope](#step-3-nutritional-data-providers--scope)
- [Installation & Setup (Windows PowerShell)](#installation--setup-windows-powershell)
- [Reproducing Model Training](#reproducing-model-training)
- [Running Tests](#running-tests)
- [API Documentation & Examples](#api-documentation--examples)
  - [1. Server Health Check (`GET /api/health`)](#1-server-health-check-get-apihealth)
  - [2. Supported Beverage Types (`GET /api/beverage-types`)](#2-supported-beverage-types-get-apibeverage-types)
  - [3. Evidence-Grounded Analysis (`POST /api/analyze`)](#3-evidence-grounded-analysis-post-apianalyze)
  - [4. Wine Quality Prediction (`POST /api/wine/predict`)](#4-wine-quality-prediction-post-apiwinepredict)
  - [5. Wine Model Card (`GET /api/wine/model-card`)](#5-wine-model-card-get-apiwinemodel-card)
  - [6. Product Search & Data Sources (`GET /api/products/...`)](#6-product-search--data-sources-get-apiproducts)
- [Scientific Scoring Safeguards](#scientific-scoring-safeguards)

---

## 🏛️ Overview & Architecture

BQAS provides a decoupled, scientifically grounded platform for analyzing beverage composition and nutritional profiles:
- **FastAPI**: Asynchronous web framework with automatic OpenAPI documentation and interactive Swagger UI.
- **Pydantic v2**: High-performance validation, field aliases, and unified response contracts.
- **Scikit-learn & Joblib**: Machine learning pipelines, preprocessing, model serialization, and evaluation.
- **Providers Layer (`app/providers/`)**: Modular asynchronous integration with Open Food Facts and USDA FoodData Central.
- **Engine Layer (`app/engine/`)**: Unit normalization, physical calculations, empirical benchmark comparisons, authoritative evidence rules, data quality validation, and wine ML inference.
- **Score Integrity**: Maintains `health_impact_score` strictly as `null`. Wine sensory ratings do not predict health benefits, toxicity, or safety.

---

## 📂 Directory Structure

```text
backend/
├── data/
│   └── wine/                         # Official UCI Wine Quality CSV files
│       ├── winequality-red.csv       # 1,599 red wine analytical records
│       └── winequality-white.csv     # 4,898 white wine analytical records
├── scripts/
│   └── train_wine_model.py           # Reproducible training and evaluation script
├── app/
│   ├── __init__.py                   # Application package marker & version (0.5.0)
│   ├── main.py                       # FastAPI app, CORS, error handling, route registration
│   ├── schemas/                      # Pydantic schemas package
│   │   ├── __init__.py               # Re-exports baseline, Step 4 DTOs, and wine schemas
│   │   ├── products.py               # Product records, nutritional values, data source models
│   │   └── wine.py                   # WinePredictionRequest, WinePredictionResponse DTOs
│   ├── routes/
│   │   ├── __init__.py               # Route module exports
│   │   ├── health.py                 # GET /api/health endpoint
│   │   ├── beverages.py              # GET /api/beverage-types and POST /api/analyze endpoints
│   │   ├── products.py               # GET /api/products/search, details, and data-sources
│   │   └── wine.py                   # POST /api/wine/predict and GET /api/wine/model-card
│   ├── providers/
│   │   ├── __init__.py               # ProductProviderManager coordinator
│   │   ├── cache.py                  # In-memory TTL cache with documented expiration policy
│   │   ├── open_food_facts.py        # Asynchronous Open Food Facts API client
│   │   └── usda_food_data.py         # Asynchronous USDA FoodData Central client
│   └── engine/
│       ├── __init__.py               # Engine module exports
│       ├── normalization.py          # Unit conversion, input validation, null preservation
│       ├── composition.py            # Physical calculations & legacy comparison interface
│       ├── reference_data.py         # Benchmark repository enforcing >= 100 sample threshold
│       ├── composition_scoring.py    # Non-alcoholic empirical percentile scoring engine
│       ├── evidence_registry.py      # Authoritative scientific & regulatory evidence registry
│       ├── health_assessment.py      # Non-clinical, evidence-grounded health assessment engine
│       ├── health_impact.py          # Baseline health rules
│       ├── data_quality.py           # Scope validation and product data quality assessment
│       ├── analysis.py               # BeverageAnalysisService orchestrator
│       ├── wine_quality.py           # WineQualityModelService inference & validation
│       └── wine_models/              # Trained models and model card
│           ├── wine_model_red.joblib # Red wine RandomForestRegressor pipeline
│           ├── wine_model_white.joblib# White wine RandomForestRegressor pipeline
│           └── model_card.json       # Structured JSON model card
├── tests/
│   ├── __init__.py                   # Test suite package marker
│   ├── test_health.py                # Health, root, and Step 1 baseline endpoint tests
│   ├── test_normalization.py         # Unit conversions, null preservation, input boundaries
│   ├── test_composition.py           # Composition formulas, missing input notes, legacy scorer
│   ├── test_analysis.py              # Full service integration, WHO rules, and API endpoints
│   ├── test_data_quality.py          # Scope validation and product data quality warnings
│   ├── test_providers.py             # Mocked offline tests for OFF, USDA, caching, timeouts, 429
│   ├── test_products_api.py          # API integration tests for /api/products and /api/data-sources
│   ├── test_composition_scoring.py   # Empirical percentile scoring, alcoholic exclusion, null guards
│   ├── test_health_assessment.py     # Health observations, missing data notices, alcoholic warnings
│   ├── test_evidence_registry.py     # Rule verification gate, exact URLs, category filtering
│   └── test_wine_model.py            # Wine model validation, inference, unavailable assets, disclaimers
├── requirements.txt                  # Project dependencies
└── README.md                         # System documentation and instructions
```

---

## 🍇 Step 5 Wine Quality Machine Learning Model

### 1. Dataset & Provenance
- **Source**: Official [UCI Machine Learning Repository - Wine Quality Dataset](https://archive.ics.uci.edu/dataset/186/wine+quality).
- **Citation**: P. Cortez, A. Cerdeira, F. Almeida, T. Matos and J. Reis. *Modeling wine preferences by data mining from physicochemical properties*. In Decision Support Systems, Elsevier, 47(4):547-553, 2009.
- **Geographic Origin**: Vinho Verde region, Minho, Northwest Portugal.
- **Features (11 Physicochemical Attributes)**:
  1. `fixed acidity`: tartaric acid concentration ($g/dm^3$)
  2. `volatile acidity`: acetic acid concentration ($g/dm^3$)
  3. `citric acid`: citric acid concentration ($g/dm^3$)
  4. `residual sugar`: residual sugar post-fermentation ($g/dm^3$)
  5. `chlorides`: sodium chloride content ($g/dm^3$)
  6. `free sulfur dioxide`: unbound $SO_2$ preventing microbial growth ($mg/dm^3$)
  7. `total sulfur dioxide`: bound + free $SO_2$ ($mg/dm^3$)
  8. `density`: mass per unit volume ($g/cm^3$)
  9. `pH`: wine acidity/alkalinity scale ($0-14$)
  10. `sulphates`: potassium sulphate antimicrobial additive ($g/dm^3$)
  11. `alcohol`: ethanol volume percentage ($\%$ vol.)
- **Target**: Sensory quality score (median of ratings between 0 and 10 awarded by at least 3 certified wine experts).

### 2. Model Architecture & Preprocessing Pipeline
- **Separate Models Justification**: Red and white Vinho Verde wines have fundamentally distinct chemical distributions (e.g., higher volatile acidity and tannin phenolics in reds; higher residual sugars and total $SO_2$ in whites). Training separate models reflects enological reality and matches Cortez et al. (2009).
- **Data Leakage Protection**: Data is partitioned into **80% training** and **20% held-out test** sets using a fixed random seed (`random_state=42`). `StandardScaler` is encapsulated inside a `Pipeline` and fitted strictly on `X_train`.

### 3. Evaluation Results (Held-Out Test Data)

Metrics calculated on actual held-out test data (320 red wine test samples, 980 white wine test samples):

| Wine Type | Model Algorithm | MAE | RMSE | $R^2$ Score | Status |
|---|---|---|---|---|---|
| **Red Wine** | Dummy Mean Baseline | 0.6853 | 0.8107 | -0.0056 | Baseline |
| **Red Wine** | Ridge Regression ($\alpha=1.0$) | 0.5036 | 0.6245 | 0.4032 | Linear candidate |
| **Red Wine** | **Random Forest Regressor** | **0.4220** | **0.5483** | **0.5399** | **Selected** |
| **White Wine** | Dummy Mean Baseline | 0.6750 | 0.8806 | -0.0014 | Baseline |
| **White Wine** | Ridge Regression ($\alpha=1.0$) | 0.5863 | 0.7544 | 0.2652 | Linear candidate |
| **White Wine** | **Random Forest Regressor** | **0.4195** | **0.5901** | **0.5504** | **Selected** |

### 4. Model Card Artifacts & Storage
Trained assets are stored under `app/engine/wine_models/`:
- `wine_model_red.joblib`: Serialized scikit-learn pipeline for red wine.
- `wine_model_white.joblib`: Serialized scikit-learn pipeline for white wine.
- `model_card.json`: Machine-readable model card containing dataset lineage, training parameters, evaluation metrics, and limitations.

### 5. Disclaimers & Known Limitations
1. **Regional Specificity**: The model was trained exclusively on Portuguese *Vinho Verde* wines. It reflects high-acidity, low-alcohol cool-climate characteristics and may not generalize to warm-climate wines, distinct grape varietals (e.g., Napa Cabernet, Barolo), or fortified wines.
2. **Non-Clinical Nature**: Sensory ratings represent hedonic expert taste preferences. They **do not** reflect healthiness, safety, or nutritional superiority.
3. **Missing Sensory Variables**: Key aromatic compounds (esters, monoterpenes), oak maturation compounds (vanillin, lactones), and visual chromatic attributes were not measured in the UCI dataset.
4. **Separation**: Kept completely decoupled from Composition Scoring and Health Impact Assessment.

---

## 💻 Installation & Setup (Windows PowerShell)

```powershell
# 1. Navigate to backend directory
cd "d:\wine qualt\backend"

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Verify dependencies
pip install -r requirements.txt
```

---

## 🔄 Reproducing Model Training

The training workflow is completely reproducible and downloads dataset files from the official UCI repository if not already present:

```powershell
.\.venv\Scripts\python.exe scripts/train_wine_model.py
```

---

## 🧪 Running Tests

To run the complete test suite (131 tests across all 12 modules):

```powershell
.\.venv\Scripts\pytest.exe -v
```

To run Step 5 wine quality model tests specifically (13 tests):

```powershell
.\.venv\Scripts\pytest.exe -v tests/test_wine_model.py
```

---

## 📡 API Documentation & Examples

### Wine Quality Prediction (`POST /api/wine/predict`)

**Request**:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/wine/predict" -Method POST -ContentType "application/json" -Body '{
  "wine_type": "red",
  "fixed_acidity": 7.4,
  "volatile_acidity": 0.70,
  "citric_acid": 0.0,
  "residual_sugar": 1.9,
  "chlorides": 0.076,
  "free_sulfur_dioxide": 11.0,
  "total_sulfur_dioxide": 34.0,
  "density": 0.9978,
  "pH": 3.51,
  "sulphates": 0.56,
  "alcohol": 9.4
}'
```

**Response (`200 OK`)**:
```json
{
  "status": "success",
  "wine_type": "red",
  "estimated_quality_score": 5.12,
  "rounded_quality_rating": 5,
  "model_version": "1.0.0",
  "model_algorithm": "random_forest_regressor",
  "evaluation_metrics": {
    "mae": 0.422,
    "rmse": 0.5483,
    "r2_score": 0.5399
  },
  "model_card_reference": {
    "model_name": "BQAS Wine Quality Sensory Predictor",
    "model_version": "1.0.0",
    "dataset_name": "UCI Wine Quality Dataset",
    "dataset_url": "https://archive.ics.uci.edu/dataset/186/wine+quality",
    "geographic_origin": "Vinho Verde region, Minho, Northwest Portugal",
    "citation": "Cortez et al., 2009",
    "train_test_split": "80% Train, 20% Held-Out Test",
    "random_seed": 42,
    "train_samples": 1279,
    "test_samples": 320
  },
  "disclaimer": "This estimated sensory quality rating is an empirical machine-learning estimate based on expert panel scores and is strictly non-clinical. It does NOT represent a health claim, a toxicological assessment, a safety guarantee, or an accredited laboratory certification. Sensory ratings must not be used to infer health benefits or justify consumption.",
  "regional_applicability": "Trained exclusively on physicochemical data representing Portuguese Vinho Verde wines from Northwest Portugal (Cortez et al., 2009). This model reflects the unique high-acidity, low-alcohol profile of Vinho Verde and may not generalize to other wine regions, styles, grape varieties, vintages, or production methods.",
  "input_features": {
    "fixed_acidity": 7.4,
    "volatile_acidity": 0.7,
    "citric_acid": 0.0,
    "residual_sugar": 1.9,
    "chlorides": 0.076,
    "free_sulfur_dioxide": 11.0,
    "total_sulfur_dioxide": 34.0,
    "density": 0.9978,
    "pH": 3.51,
    "sulphates": 0.56,
    "alcohol": 9.4
  }
}
```

---

### Wine Model Card (`GET /api/wine/model-card`)

**Request**:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/wine/model-card" -Method GET
```

---

## 🔒 Scientific Scoring Safeguards

- **Zero-Imputation Prohibition**: Missing or non-finite features are strictly rejected with HTTP 422; missing inputs are never assumed to be zero.
- **Physical Boundary Validation**: Enforces valid physical and chemical ranges (e.g., $pH \in (2.0, 5.0)$, alcohol $\le 25\%$, free $SO_2 \le$ total $SO_2$).
- **No Health Claims from Sensory Ratings**: Wine prediction does not generate health scores, rankings, or safety claims.
- **Unfabricated Metrics**: All reported evaluation metrics stem from actual execution on held-out test sets.
