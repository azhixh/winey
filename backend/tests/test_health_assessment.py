"""
Unit and API integration tests for app.engine.health_assessment and Step 4 API specifications.

Verifies:
- Separation between health assessment and composition scoring.
- Health impact scores remain strictly None.
- Non-alcoholic beverages produce evidence-supported observations only.
- Incomplete nutritional data produces explicit missing-data notices and refuses healthy/safe classifications.
- Status is 'insufficient_data' when core macronutrients are missing.
- Alcoholic beverage categories strictly provide factual health-risk warnings (citing WHO 2023),
  with explicit prohibitions against product rankings, quality recommendations, or consumption optimization.
- Authoritative source citations include organization, exact URL, publication year, and jurisdiction.
- Full API POST /api/analyze integration testing for Step 4 schemas and statuses ('available', 'insufficient_data', 'not_evaluated').
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.engine.health_assessment import (
    HealthAssessmentEngine,
    HealthAssessmentResult,
)
from app.engine.normalization import normalize_beverage_input
from app.schemas import BeverageType

client = TestClient(app)


def test_health_impact_score_strictly_none():
    """Health impact score must remain strictly None across all evaluations."""
    engine = HealthAssessmentEngine()

    # Soft drink
    norm_soft = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=250.0,
        sugar=20.0,
        calories=80.0,
    )
    res_soft = engine.evaluate(norm_soft)
    assert res_soft.health_impact_score is None

    # Beer
    norm_beer = normalize_beverage_input(
        beverage_type=BeverageType.BEER,
        serving_size=500.0,
        alcohol_percentage=5.0,
    )
    res_beer = engine.evaluate(norm_beer)
    assert res_beer.health_impact_score is None


def test_health_assessment_separated_from_composition():
    """Health assessment must not fabricate composition percentiles or rankings."""
    engine = HealthAssessmentEngine()
    norm = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=330.0,
        sugar=35.0,
        calories=140.0,
    )
    result = engine.evaluate(norm)

    assert result.health_impact_score is None
    # Findings must only be evidence-backed observations
    for obs in result.observations:
        assert "rule_id" in obs
        assert "source_url" in obs
        assert "percentile" not in obs
        assert "score" not in obs


def test_missing_nutrients_generate_explicit_notices():
    """Missing nutrients must trigger explicit notices and guard against safe/healthy classification."""
    engine = HealthAssessmentEngine()
    norm = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=330.0,
        sugar=30.0,
        # calories, sodium, caffeine, alcohol_percentage omitted
    )
    result = engine.evaluate(norm)

    assert len(result.missing_data_notices) >= 1
    notice = result.missing_data_notices[0]
    assert "calories" in notice
    assert "sodium" in notice
    assert "caffeine" in notice
    assert "cannot be classified as healthy, unhealthy, or safe" in notice


def test_insufficient_data_status_when_nutrients_omitted():
    """When both sugar and calories are missing, health assessment status is 'insufficient_data'."""
    engine = HealthAssessmentEngine()
    norm = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=330.0,
        # No sugar, calories, or concentration
    )
    result = engine.evaluate(norm)

    assert result.status == "insufficient_data"
    assert result.health_impact_score is None
    assert len(result.observations) == 0
    assert len(result.missing_data_notices) >= 1
    assert any("Insufficient data" in w for w in result.warnings)


def test_alcoholic_beverages_factual_warnings_only_no_rankings():
    """Alcoholic beverages must strictly provide factual health-risk warnings with no rankings or advice."""
    engine = HealthAssessmentEngine()
    for alc_type in [BeverageType.BEER, BeverageType.WINE, BeverageType.SPIRITS]:
        norm = normalize_beverage_input(
            beverage_type=alc_type,
            serving_size=150.0,
            alcohol_percentage=12.0,
        )
        result = engine.evaluate(norm)

        assert result.status == "available"
        assert result.health_impact_score is None

        # Check explicit policy statements
        assert any("Quality rankings and consumption recommendations are disabled" in w for w in result.warnings)
        assert any("strictly excludes quality rankings" in lim for lim in result.limitations)

        # Check WHO 2023 carcinogen finding
        assert len(result.observations) >= 1
        obs = result.observations[0]
        assert obs["rule_id"] == "WHO_ALCOHOL_RISK_2023"
        assert obs["publication_year"] == 2023
        assert "no level of alcohol consumption is risk-free" in obs["observation_text"]
        assert "who.int" in obs["source_url"]


def test_non_alcoholic_energy_drink_observations():
    """Energy drink with sugar and caffeine produces both WHO sugar and EFSA caffeine observations."""
    engine = HealthAssessmentEngine()
    norm = normalize_beverage_input(
        beverage_type=BeverageType.ENERGY_DRINK,
        serving_size=250.0,
        sugar=27.0,
        calories=110.0,
        caffeine=80.0,
    )
    result = engine.evaluate(norm)

    assert result.status == "available"
    assert result.health_impact_score is None

    rule_ids = [obs["rule_id"] for obs in result.observations]
    assert "WHO_SUGARS_GUIDELINE_2015" in rule_ids
    assert "EFSA_CAFFEINE_SAFETY_2015" in rule_ids

    # Verify sources
    source_orgs = [s["source_organization"] for s in result.sources]
    assert any("World Health Organization" in org for org in source_orgs)
    assert any("European Food Safety Authority" in org for org in source_orgs)


# =====================================================================
# API POST /api/analyze Integration Tests for Step 4
# =====================================================================

def test_api_analyze_soft_drink_with_valid_benchmark():
    """POST /api/analyze for Soft drink with sugar compares against USDA benchmark."""
    payload = {
        "beverage_type": "Soft drink",
        "serving_size_ml": 250.0,
        "sugar_g": 25.0,
        "calories": 105.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"

    # Composition comparison
    comp = data["composition_comparison"]
    assert comp["status"] == "available"
    assert comp["score"] is not None
    assert comp["sample_size"] == 120
    assert comp["sample_size"] >= 100
    assert comp["benchmark_name"] == "USDA FoodData Central Foundation & SR Legacy Soft Drink Benchmark"
    assert comp["dataset_version"] == "2024.1"
    assert comp["calculation_method"] == "empirical_percentile"
    assert len(comp["limitations"]) >= 3

    # Health assessment
    health = data["health_assessment"]
    assert health["status"] == "available"
    assert health["health_impact_score"] is None
    assert len(health["observations"]) >= 1
    assert any(obs["rule_id"] == "WHO_SUGARS_GUIDELINE_2015" for obs in health["observations"])
    assert len(health["missing_data_notices"]) >= 1

    # Sources
    sources = data["sources"]
    assert any(s.get("benchmark_name") == comp["benchmark_name"] for s in sources)
    assert any("who.int" in str(s.get("source_url", "")) for s in sources)


def test_api_analyze_energy_drink_insufficient_sample_size():
    """POST /api/analyze for Energy drink returns insufficient_data for composition score (< 100 records)."""
    payload = {
        "beverage_type": "Energy drink",
        "serving_size_ml": 250.0,
        "sugar_g": 28.0,
        "calories": 120.0,
        "caffeine_mg": 80.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Composition comparison
    comp = data["composition_comparison"]
    assert comp["status"] == "insufficient_data"
    assert comp["score"] is None
    assert comp["sample_size"] == 40
    assert comp["sample_size"] < 100
    assert "minimum 100 required" in comp["explanation"]

    # Health assessment should still be available based on WHO & EFSA rules
    health = data["health_assessment"]
    assert health["status"] == "available"
    assert health["health_impact_score"] is None
    rule_ids = [obs["rule_id"] for obs in health["observations"]]
    assert "EFSA_CAFFEINE_SAFETY_2015" in rule_ids
    assert "WHO_SUGARS_GUIDELINE_2015" in rule_ids


def test_api_analyze_alcoholic_drink_not_evaluated_composition():
    """POST /api/analyze for Beer returns not_evaluated for composition and strictly factual health warnings."""
    payload = {
        "beverage_type": "Beer",
        "serving_size_ml": 500.0,
        "alcohol_percentage": 5.0,
        "calories": 215.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Composition comparison
    comp = data["composition_comparison"]
    assert comp["status"] == "not_evaluated"
    assert comp["score"] is None
    assert "scoped strictly to non-alcoholic categories" in comp["explanation"]

    # Health assessment
    health = data["health_assessment"]
    assert health["status"] == "available"
    assert health["health_impact_score"] is None
    assert any("Quality rankings and consumption recommendations are disabled" in w for w in health["warnings"])
    assert any(obs["rule_id"] == "WHO_ALCOHOL_RISK_2023" for obs in health["observations"])


def test_api_analyze_missing_all_nutrients():
    """POST /api/analyze with omitted nutrients yields explicit insufficient_data statuses."""
    payload = {
        "beverage_type": "Soft drink",
        "serving_size_ml": 330.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Composition comparison
    comp = data["composition_comparison"]
    assert comp["status"] == "insufficient_data"
    assert comp["score"] is None

    # Health assessment
    health = data["health_assessment"]
    assert health["status"] == "insufficient_data"
    assert health["health_impact_score"] is None
    assert len(health["missing_data_notices"]) >= 1
    assert any("cannot be classified as healthy, unhealthy, or safe" in n for n in health["missing_data_notices"])
