# BQAS Implementation Status (Step 6 Audit)

**Date**: October 21, 2026  
**Status**: Step 6 — Backend Completion and Scoring Engine Implementation  
**Auditor**: Senior Backend & Test Engineering Lead  

---

## 1. Existing Functionality & Verification Status

| Component | Modules | Status | Verification Summary |
|---|---|---|---|
| **FastAPI Core & Routing** | `app/main.py`, `app/routes/` | Verified & Operational | Server handles health (`/api/health`), beverage types (`/api/beverage-types`), analysis (`/api/analyze`), products (`/api/products/*`), and wine (`/api/wine/*`). 131 tests passing. |
| **Unit Normalization** | `app/engine/normalization.py` | Verified & Operational | Converts volume (mL, L, cL, fl oz), mass (g, mg, kg), energy (kcal, kJ), ABV. Null values are strictly preserved without zero-imputation. |
| **Physical Calculations** | `app/engine/composition.py` | Verified & Operational | Calculates alcohol grams ($0.789\text{ g/mL}$ ethanol density), energy per 100 mL, sugar concentration per 100 mL, and sugar per serving. |
| **Nutritional Providers** | `app/providers/open_food_facts.py`, `usda_food_data.py`, `cache.py` | Verified & Operational | Asynchronous HTTP clients with TTL caching and rate limit ($429$) fallback. Alcoholic search is restricted. |
| **Wine Quality ML Engine** | `app/engine/wine_quality.py`, `scripts/train_wine_model.py` | Verified & Operational | Scikit-learn Random Forest regression pipelines for red and white wine evaluated on official UCI held-out data. Validates 11 physicochemical features. |
| **Evidence Registry** | `app/engine/evidence_registry.py` | Verified & Operational | Authoritative rule structure with review gates for WHO Alcohol (2023), WHO Sugars (2015), and EFSA Caffeine (2015). |

---

## 2. Identified Gaps & PRD Inconsistencies

### Gap 1: Centralized `rules.json` & `reference_ranges.json` Configuration
- **Current State**: Rule definitions are hardcoded as Python classes/instances in `evidence_registry.py` and `health_impact.py`.
- **PRD Requirement (Sections 12 & 13)**: All thresholds, guideline limits, weights, risk directions, critical rules, and personalization parameters must reside in a centralized, versioned `rules.json` and `reference_ranges.json`.

### Gap 2: Exact PRD Section 12 Scoring Engine Formula
- **Current State**: In Steps 2–4, `health_impact_score` was maintained strictly as `null` pending consensus scoring calibration.
- **PRD Requirement (Section 12.3 & 12.4)**:
  - Ratio: $r = \text{amount per serving} \div \text{applicable limit}$.
  - Piecewise 5-band subscore curve:
    - $r \le 0.5 \implies 100$ (Favourable)
    - $0.5 < r \le 1.0 \implies 100 - (r - 0.5) \times 80$ (Moderate: $100 \to 60$)
    - $1.0 < r \le 2.0 \implies 60 - (r - 1.0) \times 40$ (Caution: $60 \to 20$)
    - $2.0 < r \le 3.0 \implies 20 - (r - 2.0) \times 20$ (High: $20 \to 0$)
    - $r > 3.0 \implies 0$ (High)
  - Health Impact Score = weighted average of available guideline subscores.
  - Composition Score = credits based on benchmark status (Typical = 100; Lower = 100/60; Higher = 50/100; Very high = 20) taking risk directions into account.

### Gap 3: Critical Overrides
- **Current State**: Handled as descriptive warnings in `health_assessment.py`.
- **PRD Requirement (Section 12.6)**: Breaches of critical rules (e.g., methanol exceeding limit, caffeine exceeding group single-dose limit) must cap the Health Impact Score at **40** and set a critical flag for a prominent red banner.

### Gap 4: Personalization Engine
- **Current State**: Default evaluations assume standard adult profiles.
- **PRD Requirement (Section 12.10)**: Support profile overrides:
  - Under-18: caffeine daily limit scaled to $3\text{ mg/kg}$, alcohol avoid notice.
  - Pregnancy/breastfeeding: caffeine daily limit capped at $200\text{ mg}$, alcohol avoid notice.
  - Weight-dependent scaling ($mg/kg$) for caffeine, sodium benzoate (E211 with $0.848$ conversion factor), and sulphites.
  - Standard drink definition selection (WHO default 10 g).

### Gap 5: Confidence & Partial Analysis
- **Current State**: Confidence rating is implicit.
- **PRD Requirement (Section 12.8)**: High ($\ge 80\%$), Medium ($60\% - 79\%$), Low ($< 60\%$). When $< 60\%$ of weighted fields are filled, label result as `Partial analysis`.

### Gap 6: Automated Acceptance Tests T1–T10
- **Current State**: 131 unit and integration tests passing, but the specific T1–T10 acceptance fixtures defined in PRD Section 18.1 have not been formally implemented.

---

## 3. Investigation of PRD Acceptance Test Cases T1–T10

| Test ID | Scenario | Input & Profile | Mathematical Evaluation vs PRD Specification | Consistency Assessment |
|---|---|---|---|---|
| **T1** | Soft drink sugar | 330 mL, 35 g sugar | Ideal target: 25 g; Cap: 50 g. $r = 35 / 25 = 1.40$ (140% of ideal); $35 / 50 = 70\%$ of cap. Caution band ($1.0 < r \le 2.0$): $\text{subscore} = 60 - (1.40 - 1.0) \times 40 = 44$. | **Consistent**: Formula matches PRD expected subscore of 44. |
| **T2** | Adult caffeine | 250 mL, 160 mg caffeine | Single dose: 200 mg ($160/200 = 80\%$). Daily limit: 400 mg ($160/400 = 40\%$). $r = 0.80$ (Moderate band): $\text{subscore} = 100 - (0.80 - 0.5) \times 80 = 76$. | **Consistent**: Formula matches PRD expected subscore of 76. |
| **T3** | Under-18 caffeine | 250 mL, 160 mg caffeine, 40 kg user | Daily limit: $40 \times 3 = 120\text{ mg}$. $r = 160 / 120 = 1.333$. Caution band: $\text{subscore} = 60 - (1.333 - 1.0) \times 40 = 46.67 \approx 47$. | **Consistent**: Formula matches PRD expected subscore of ~47. |
| **T4** | Wine alcohol | 150 mL, 13% ABV | $150 \times 0.13 \times 0.789 = 15.39\text{ g}$ alcohol; $15.39 / 10 = 1.54$ standard drinks; WHO statement present; no safe label. | **Consistent**: Exact match with physical formula. |
| **T5** | Beer alcohol | 330 mL, 5% ABV | $330 \times 0.05 \times 0.789 = 13.02\text{ g}$ alcohol; $13.02 / 10 = 1.30$ standard drinks. | **Consistent**: Exact match with physical formula. |
| **T6** | Pregnancy caffeine | 150 mg caffeine, pregnant user | Daily limit: 200 mg. $r = 150 / 200 = 0.75$ (75% of daily). Moderate band: $\text{subscore} = 100 - (0.75 - 0.5) \times 80 = 80$. | **Consistent**: Formula matches PRD expected subscore of 80. |
| **T7** | Sparse input | 2 of 7 weighted fields filled | $2/7 = 28.57\% < 60\%$. Low confidence; "Partial analysis"; missing fields excluded. | **Consistent**: Matches PRD confidence rubric. |
| **T8** | Critical methanol | Methanol exceeds limit | Critical flag triggered; red banner metadata; Health Impact Score capped at 40. | **Consistent**: Matches PRD critical override rule. |
| **T9** | Incomplete wine model | Only Basic wine fields | No quality prediction; explanatory reason returned detailing missing model inputs. | **Consistent**: Matches WineQualityModelService design. |
| **T10** | Null caffeine from OFF | OFF returns null caffeine | Field remains blank/null; "not available in dataset"; never scored as zero. | **Consistent**: Matches null-preservation policy. |

---

## 4. Implementation Order

1. **Configuration**: Create `backend/data/rules.json` with complete schema-backed definitions (limits, weights, risk directions, critical rules, personalization parameters, source URLs, and version metadata).
2. **Benchmark Distribution Data**: Create `backend/data/reference_ranges.json` containing verified category distributions ($n \ge 100$, $P_5, P_{25}, P_{50}, P_{75}, P_{95}$).
3. **Core Scoring Engine (`app/engine/scoring_engine.py`)**:
   - Pure, deterministic normalization, ratio computation, 5-band subscore curve, critical overrides, composition credit scoring, confidence evaluation, and personalization.
4. **Data Models & Schemas (`app/schemas/scoring.py`)**:
   - Typed input and result contracts matching PRD Section 16.1.
5. **API Integration**: Connect `scoring_engine.py` into `POST /api/analyze` while preserving backward compatibility.
6. **Acceptance Test Suite (`tests/test_acceptance_t1_t10.py`)**:
   - Implement test fixtures T1 through T10 with exact assertions.
7. **Comprehensive Unit & Boundary Tests (`tests/test_scoring_engine.py`)**:
   - Curve boundaries, percentile classifications, risk directions, override precedence, personalization, and edge cases.
8. **Final Documentation & Reports**:
   - `docs/SCORING_ENGINE_SPEC.md`
   - `docs/T1_T10_ACCEPTANCE_REPORT.md`
   - `docs/STEP_6_IMPLEMENTATION_REPORT.md`
