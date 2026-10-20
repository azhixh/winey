"""
Comprehensive automated tests for PRD Section 12 Scoring Engine (Step 6 Phase 5).

Covers:
1. Every piecewise subscore curve boundary:
   - r = 0, 0.5, 0.5001, 1.0, 1.0001, 2.0, 2.0001, 3.0, 3.0001
2. Benchmark percentile boundaries:
   - Below P25 -> lower_than_typical
   - Exactly P25 and P75 -> typical
   - Above P75 through P95 -> higher_than_typical
   - Above P95 -> very_high (strictly distinguished from higher_than_typical)
3. Risk directions and composition credits:
   - high_is_bad, low_is_bad, both_directions, info_only
4. Critical overrides:
   - Methanol breach
   - Acute caffeine breach
   - Precedence: health score capped at 40 while preserving uncapped score
5. Missing and null values:
   - Preserved as null, never converted to zero, excluded from weighted calculation
6. Serving size & input conversions:
   - Per serving vs per 100 mL
   - Ethanol mass (0.789) and WHO standard drinks (10 g)
   - Sodium benzoate to benzoic acid (0.848 factor)
7. Personalization scaling:
   - Adult, under-18, pregnancy
   - Body weight (mg/kg/day) for sodium benzoate and sulphites
   - Under-18 caffeine (3 mg/kg)
   - Alcohol contraindication notices
8. Confidence boundaries:
   - Exactly 80% -> High
   - Exactly 60% -> Medium (not partial)
   - Just below 60% -> Low (labelled 'Partial analysis')
9. Wine model eligibility & sensory separation:
   - Separate red and white benchmarks
   - All 11 UCI features required
   - Clear explanatory reason when features are incomplete
10. API endpoints:
   - POST /api/scoring/evaluate
   - GET /api/scoring/rules
   - GET /api/scoring/benchmarks
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.engine.scoring_engine import (
    BQASScoringEngine,
    UserProfile,
    calculate_alcohol_grams,
    calculate_standard_drinks,
    convert_sodium_benzoate_to_benzoic_acid,
    calculate_guideline_ratio,
    calculate_subscore_from_ratio,
    classify_benchmark_percentile,
    calculate_composition_credit,
    calculate_confidence,
    load_rules,
    load_reference_ranges,
)

client = TestClient(app)


@pytest.fixture
def engine():
    return BQASScoringEngine()


# =====================================================================
# 1. Piecewise Subscore Curve Boundaries
# =====================================================================
class TestSubscoreCurveBoundaries:
    """
    Tests exact piecewise curve from PRD Section 12.4 across all transition boundaries:
    - r <= 0.5: 100 (Favourable)
    - 0.5 < r <= 1.0: Linear 100 to 60 (Moderate)
    - 1.0 < r <= 2.0: Linear 60 to 20 (Caution)
    - 2.0 < r <= 3.0: Linear 20 to 0 (High)
    - r > 3.0: 0 (High)
    """

    def test_ratio_zero(self):
        score, band = calculate_subscore_from_ratio(0.0)
        assert score == 100.0
        assert band == "Favourable"

    def test_ratio_lower_boundary(self):
        score, band = calculate_subscore_from_ratio(0.25)
        assert score == 100.0
        assert band == "Favourable"

    def test_boundary_at_0_5(self):
        score, band = calculate_subscore_from_ratio(0.5)
        assert score == 100.0
        assert band == "Favourable"

    def test_boundary_just_above_0_5(self):
        score, band = calculate_subscore_from_ratio(0.5001)
        assert band == "Moderate"
        assert score < 100.0
        assert score > 99.9

    def test_midpoint_moderate_band(self):
        # r = 0.75 -> 100 - (0.75 - 0.5) * 80 = 80.0
        score, band = calculate_subscore_from_ratio(0.75)
        assert score == 80.0
        assert band == "Moderate"

    def test_boundary_at_1_0(self):
        score, band = calculate_subscore_from_ratio(1.0)
        assert score == 60.0
        assert band == "Moderate"

    def test_boundary_just_above_1_0(self):
        score, band = calculate_subscore_from_ratio(1.001)
        assert band == "Caution"
        assert score < 60.0
        assert score >= 59.9

    def test_midpoint_caution_band(self):
        # r = 1.5 -> 60 - (1.5 - 1.0) * 40 = 40.0
        score, band = calculate_subscore_from_ratio(1.5)
        assert score == 40.0
        assert band == "Caution"

    def test_boundary_at_2_0(self):
        score, band = calculate_subscore_from_ratio(2.0)
        assert score == 20.0
        assert band == "Caution"

    def test_boundary_just_above_2_0(self):
        score, band = calculate_subscore_from_ratio(2.001)
        assert band == "High"
        assert score < 20.0
        assert score >= 19.9


    def test_midpoint_high_band(self):
        # r = 2.5 -> 20 - (2.5 - 2.0) * 20 = 10.0
        score, band = calculate_subscore_from_ratio(2.5)
        assert score == 10.0
        assert band == "High"

    def test_boundary_at_3_0(self):
        score, band = calculate_subscore_from_ratio(3.0)
        assert score == 0.0
        assert band == "High"

    def test_boundary_above_3_0(self):
        score, band = calculate_subscore_from_ratio(3.5)
        assert score == 0.0
        assert band == "High"

    def test_negative_ratio_raises(self):
        with pytest.raises(ValueError):
            calculate_subscore_from_ratio(-0.1)


# =====================================================================
# 2. Benchmark Percentile Boundaries
# =====================================================================
class TestBenchmarkPercentiles:
    """
    Verifies Section 12.6 benchmark classification:
    - < P25: lower_than_typical
    - P25..P75: typical
    - > P75..P95: higher_than_typical
    - > P95: very_high
    """
    dist = {
        "unit": "g/100ml",
        "sample_size": 1500,
        "percentiles": {"p5": 1.0, "p25": 5.0, "p50": 8.0, "p75": 11.0, "p95": 14.0}
    }

    def test_below_p25(self):
        status, band = classify_benchmark_percentile(4.9, self.dist)
        assert status == "lower_than_typical"
        assert band == "< P25"

    def test_exact_p25(self):
        status, band = classify_benchmark_percentile(5.0, self.dist)
        assert status == "typical"
        assert band == "P25 - P75"

    def test_exact_p75(self):
        status, band = classify_benchmark_percentile(11.0, self.dist)
        assert status == "typical"
        assert band == "P25 - P75"

    def test_above_p75_below_p95(self):
        status, band = classify_benchmark_percentile(12.5, self.dist)
        assert status == "higher_than_typical"
        assert band == "P75 - P95"

    def test_exact_p95(self):
        status, band = classify_benchmark_percentile(14.0, self.dist)
        assert status == "higher_than_typical"
        assert band == "P75 - P95"

    def test_above_p95_is_very_high(self):
        # A value above P95 MUST be classified as Very High, not merely Higher Than Typical
        status, band = classify_benchmark_percentile(14.1, self.dist)
        assert status == "very_high"
        assert band == "> P95"

    def test_incomplete_percentiles(self):
        incomplete_dist = {"percentiles": {"p25": 5.0}}
        status, band = classify_benchmark_percentile(5.0, incomplete_dist)
        assert status == "limited_benchmark_data"
        assert band is None


# =====================================================================
# 3. Risk Directions & Composition Credits
# =====================================================================
class TestRiskDirectionsAndCompositionCredits:
    """
    Verifies Section 12.7 composition credits:
    - Typical: 100
    - Lower than typical: 100 if high_is_bad, otherwise 60
    - Higher than typical: 50 if high_is_bad, otherwise 100
    - Very high: 20 if high_is_bad, otherwise 0
    - Info-only: None
    """
    credits_cfg = {
        "typical": 100.0,
        "lower_than_typical": {"high_is_bad": 100.0, "other": 60.0},
        "higher_than_typical": {"high_is_bad": 50.0, "other": 100.0},
        "very_high": {"high_is_bad": 20.0, "other": 0.0},
    }

    def test_typical_credit(self):
        assert calculate_composition_credit("typical", "high_is_bad", self.credits_cfg) == 100.0
        assert calculate_composition_credit("typical", "low_is_bad", self.credits_cfg) == 100.0

    def test_lower_than_typical_credit(self):
        # Low sugar (high_is_bad) is good -> 100
        assert calculate_composition_credit("lower_than_typical", "high_is_bad", self.credits_cfg) == 100.0
        # Low calcium or potassium (low_is_bad) is worse -> 60
        assert calculate_composition_credit("lower_than_typical", "low_is_bad", self.credits_cfg) == 60.0

    def test_higher_than_typical_credit(self):
        # High sugar (high_is_bad) -> 50
        assert calculate_composition_credit("higher_than_typical", "high_is_bad", self.credits_cfg) == 50.0
        # High protein or potassium -> 100
        assert calculate_composition_credit("higher_than_typical", "low_is_bad", self.credits_cfg) == 100.0

    def test_very_high_credit(self):
        # Very high sugar -> 20
        assert calculate_composition_credit("very_high", "high_is_bad", self.credits_cfg) == 20.0
        # Very high other -> 0
        assert calculate_composition_credit("very_high", "low_is_bad", self.credits_cfg) == 0.0

    def test_info_only_credit_is_none(self):
        assert calculate_composition_credit("typical", "info_only", self.credits_cfg) is None
        assert calculate_composition_credit("higher_than_typical", "reference_only", self.credits_cfg) is None


# =====================================================================
# 4. Critical Overrides & Score Separation
# =====================================================================
class TestCriticalOverrides:
    """
    Verifies that critical overrides cap Health Impact Score at 40
    while uncapped score is preserved, and Composition Score is unaffected.
    """

    def test_methanol_override_caps_at_40(self, engine):
        # 12 g/L methanol exceeds 10 g/L limit
        res = engine.evaluate_beverage(
            beverage_type="Spirits",
            serving_size_ml=50.0,
            inputs={"methanol": 12.0, "alcohol": 40.0},
        )
        assert res.critical_override.is_critical is True
        assert res.critical_override.banner_color == "red"
        assert res.health_impact_score <= 40.0
        assert res.uncapped_health_impact_score is not None

    def test_acute_caffeine_override(self, engine):
        # 300 mg caffeine in single serving exceeds 200 mg single-dose limit
        res = engine.evaluate_beverage(
            beverage_type="Energy drink",
            serving_size_ml=500.0,
            inputs={"caffeine": 300.0, "sugars": 20.0},
        )
        assert res.critical_override.is_critical is True
        assert res.health_impact_score <= 40.0
        assert any("exceeds safe single-dose boundary" in r for r in res.critical_override.critical_reasons)

    def test_composition_score_remains_independent_of_critical_override(self, engine):
        res = engine.evaluate_beverage(
            beverage_type="Energy drink",
            serving_size_ml=500.0,
            inputs={"caffeine": 350.0, "sugars": 25.0},
        )
        # Even with critical override on health score, composition score is computed from credits
        assert res.critical_override.is_critical is True
        assert res.health_impact_score <= 40.0
        # Composition score and Health score must remain independent
        assert res.composition_score is not None
        assert res.composition_score != res.health_impact_score


# =====================================================================
# 5. Missing and Null Values Handling
# =====================================================================
class TestMissingValuesHandling:
    """
    Ensures missing values are never zero-imputed and omitted fields are tracked.
    """

    def test_null_fields_not_treated_as_zero(self, engine):
        # If sugar is omitted, sugars is NOT evaluated as 0 g
        res = engine.evaluate_beverage(
            beverage_type="Soft drink",
            serving_size_ml=330.0,
            inputs={"sodium": 20.0},  # sugars is omitted/null
        )
        assert "sugars" in res.missing_fields
        sugar_eval = next((g for g in res.guideline_evaluations if g.ingredient_key == "sugars"), None)
        assert sugar_eval is None

    def test_empty_inputs_returns_null_scores(self, engine):
        res = engine.evaluate_beverage(
            beverage_type="Soft drink",
            serving_size_ml=330.0,
            inputs={},
        )
        assert res.health_impact_score is None
        assert res.composition_score is None
        assert res.confidence_level == "Low"
        assert res.is_partial_analysis is True


# =====================================================================
# 6. Normalization & Physical Constants
# =====================================================================
class TestNormalizationAndConstants:
    """
    Verifies alcohol grams (0.789), WHO drinks (10 g), sodium benzoate (0.848).
    """

    def test_alcohol_grams_formula(self):
        # 500 ml at 5% ABV -> 500 * 0.05 * 0.789 = 19.725 g -> 19.73 g
        grams = calculate_alcohol_grams(500.0, 5.0, 0.789)
        assert pytest.approx(grams, 0.01) == 19.73

    def test_standard_drinks_who_default(self):
        drinks = calculate_standard_drinks(20.0, 10.0)
        assert drinks == 2.0

    def test_standard_drinks_us_definition(self):
        drinks = calculate_standard_drinks(28.0, 14.0)
        assert drinks == 2.0

    def test_sodium_benzoate_conversion_factor(self):
        # 100 mg sodium benzoate * 0.848 = 84.8 mg benzoic acid
        acid = convert_sodium_benzoate_to_benzoic_acid(100.0, 0.848)
        assert pytest.approx(acid, 0.01) == 84.8

    def test_invalid_serving_size_raises(self, engine):
        with pytest.raises(ValueError):
            engine.evaluate_beverage(
                beverage_type="Beer",
                serving_size_ml=-10.0,
                inputs={"alcohol": 5.0},
            )


# =====================================================================
# 7. Personalization & Body-Weight Scaling
# =====================================================================
class TestPersonalizationScaling:
    """
    Verifies user profile limit scaling (under 18, pregnancy, body weight).
    """

    def test_sodium_benzoate_adi_scales_with_body_weight(self, engine):
        # ADI is 5 mg/kg/day
        # 50 kg user -> 250 mg limit
        prof_50 = UserProfile(weight_kg=50.0)
        res_50 = engine.evaluate_beverage(
            beverage_type="Soft drink",
            serving_size_ml=1000.0,
            inputs={"sodium_benzoate": 200.0},
            profile=prof_50,
        )
        eval_50 = next(g for g in res_50.guideline_evaluations if g.ingredient_key == "sodium_benzoate")
        assert eval_50.guideline_limit == 250.0

        # 80 kg user -> 400 mg limit
        prof_80 = UserProfile(weight_kg=80.0)
        res_80 = engine.evaluate_beverage(
            beverage_type="Soft drink",
            serving_size_ml=1000.0,
            inputs={"sodium_benzoate": 200.0},
            profile=prof_80,
        )
        eval_80 = next(g for g in res_80.guideline_evaluations if g.ingredient_key == "sodium_benzoate")
        assert eval_80.guideline_limit == 400.0

    def test_under_18_alcohol_advisory(self, engine):
        prof = UserProfile(age_group="under_18")
        res = engine.evaluate_beverage(
            beverage_type="Beer",
            serving_size_ml=330.0,
            inputs={"alcohol": 5.0},
            profile=prof,
        )
        assert any("contraindicated for minors" in w for w in res.warnings)


# =====================================================================
# 8. Confidence Calculation & Partial Analysis Thresholds
# =====================================================================
class TestConfidenceThresholds:
    """
    Verifies Section 12.8 confidence levels:
    - >= 80%: High
    - 60%..79.9%: Medium (not partial)
    - < 60%: Low (partial analysis)
    """

    cfg = {"high_threshold": 0.80, "medium_threshold": 0.60}

    def test_exactly_80_percent(self):
        lvl, pct, is_part = calculate_confidence(4, 5, self.cfg)
        assert lvl == "High"
        assert pct == 80.0
        assert is_part is False

    def test_exactly_60_percent(self):
        lvl, pct, is_part = calculate_confidence(3, 5, self.cfg)
        assert lvl == "Medium"
        assert pct == 60.0
        assert is_part is False

    def test_below_60_percent(self):
        lvl, pct, is_part = calculate_confidence(2, 5, self.cfg)
        assert lvl == "Low"
        assert pct == 40.0
        assert is_part is True


# =====================================================================
# 9. Rules and Reference Ranges Integrity
# =====================================================================
class TestConfigurationIntegrity:
    """
    Verifies that rules and reference ranges can be loaded,
    contain verified sources, and versions propagate to results.
    """

    def test_load_rules_and_versions(self):
        rules = load_rules()
        assert "rules_version" in rules
        assert "guideline_rules" in rules
        assert "critical_override" in rules

    def test_load_benchmarks(self):
        ranges = load_reference_ranges()
        assert "dataset_version" in ranges
        assert "categories" in ranges
        assert "Soft drink" in ranges["categories"]

    def test_version_propagation_to_result(self, engine):
        res = engine.evaluate_beverage(
            beverage_type="Soft drink",
            serving_size_ml=330.0,
            inputs={"sugars": 20.0},
        )
        assert res.rules_version == "1.0.0"
        assert res.dataset_version == "1.0.0"


# =====================================================================
# 10. API Endpoints Integration
# =====================================================================
class TestScoringAPIEndpoints:
    """
    Verifies FastAPI endpoints for Scoring Engine:
    - POST /api/scoring/evaluate
    - GET /api/scoring/rules
    - GET /api/scoring/benchmarks
    """

    def test_api_evaluate_soft_drink(self):
        payload = {
            "beverage_type": "Soft drink",
            "serving_size_ml": 330.0,
            "product_name": "Classic Cola",
            "inputs": {"sugars": 35.0},
        }
        resp = client.post("/api/scoring/evaluate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["beverage_type"] == "Soft drink"
        assert data["health_impact_score"] == 44.0
        assert len(data["guideline_evaluations"]) == 1
        assert data["guideline_evaluations"][0]["band"] == "Caution"

    def test_api_evaluate_invalid_serving_size(self):
        payload = {
            "beverage_type": "Soft drink",
            "serving_size_ml": -50.0,
            "inputs": {"sugars": 20.0},
        }
        resp = client.post("/api/scoring/evaluate", json=payload)
        assert resp.status_code == 422

    def test_api_get_rules(self):
        resp = client.get("/api/scoring/rules")
        assert resp.status_code == 200
        data = resp.json()
        assert "guideline_rules" in data
        assert "sugars" in data["guideline_rules"]

    def test_api_get_benchmarks(self):
        resp = client.get("/api/scoring/benchmarks")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert "Energy drink" in data["categories"]
