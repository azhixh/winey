"""
Integration and service tests for app.engine.analysis and API endpoints:
- BeverageAnalysisService end-to-end pipeline
- HealthImpactEngine rules evaluation:
  - WHO statement on alcohol (URL, year 2023, units, rationale)
  - Unsupported rule guard (never generates health classification)
  - Incomplete data guard (refuses to mark beverage as safe/healthy)
  - health_impact_score strictly None
- FastAPI POST /api/analyze endpoint with Step 2 structured schema
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.engine.analysis import BeverageAnalysisService
from app.engine.health_impact import HealthImpactEngine, HealthRule, WHO_ALCOHOL_RULE
from app.engine.normalization import normalize_beverage_input
from app.schemas import BeverageType

client = TestClient(app)


# =====================================================================
# Health Impact Engine & Rules Tests
# =====================================================================

def test_who_alcohol_rule_attributes():
    """
    Verify required attributes on the active WHO alcohol rule:
    source URL, publication year (2023), applicable beverage types, units, rationale.
    """
    assert WHO_ALCOHOL_RULE.publication_year == 2023
    assert "who.int" in WHO_ALCOHOL_RULE.source_url
    assert "no level of alcohol consumption is risk-free" in WHO_ALCOHOL_RULE.rationale.lower()
    assert "% ABV" in WHO_ALCOHOL_RULE.units
    assert "Beer" in WHO_ALCOHOL_RULE.applicable_beverage_types
    assert "Wine" in WHO_ALCOHOL_RULE.applicable_beverage_types
    assert "Spirits" in WHO_ALCOHOL_RULE.applicable_beverage_types


def test_who_alcohol_rule_triggers_for_alcoholic_beverages():
    """
    Test that WHO alcohol rule triggers advisory and attaches source citation for alcoholic beverages.
    """
    engine = HealthImpactEngine()
    norm_beer = normalize_beverage_input(
        beverage_type=BeverageType.BEER,
        serving_size=500.0,
        alcohol_percentage=5.0,
    )
    result = engine.evaluate(norm_beer)

    assert result.health_impact_score is None
    assert result.status == "unavailable"
    assert len(result.advisories) == 1
    advisory = result.advisories[0]
    assert advisory.rule_id == "WHO_ALCOHOL_2023"
    assert "who 2023" in advisory.advisory_message.lower()
    assert len(result.sources) >= 1
    assert result.sources[0]["publication_year"] == 2023


def test_unsupported_health_rule_never_produces_health_classification():
    """
    Test that an unsupported health rule (e.g., non-applicable beverage type)
    never triggers an advisory or creates a health classification.
    """
    # Create a rule applicable only to Kombucha
    custom_rule = HealthRule(
        rule_id="KOMBUCHA_SPECIFIC_RULE",
        title="Kombucha Acidity Rule",
        source_name="Example Microbial Institute",
        source_url="https://example.org/kombucha",
        publication_year=2021,
        applicable_beverage_types=["Kombucha"],
        units="pH",
        rationale="Specific to fermented tea drinks.",
        active=True,
    )
    engine = HealthImpactEngine(rules=[custom_rule])

    # Evaluate against a Beer (unsupported for this rule)
    norm_beer = normalize_beverage_input(
        beverage_type=BeverageType.BEER,
        serving_size=330.0,
        alcohol_percentage=5.0,
    )
    result = engine.evaluate(norm_beer)

    assert result.health_impact_score is None
    assert len(result.advisories) == 0  # Not triggered!
    assert result.status == "unavailable"


def test_incomplete_data_guard_refuses_safe_healthy_classification():
    """
    Incomplete nutritional data must explicitly warn that the beverage
    cannot be classified as safe or healthy.
    """
    engine = HealthImpactEngine()
    norm_soft_drink = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=330.0,
        # Omitted sugar, calories, sodium, caffeine
    )
    result = engine.evaluate(norm_soft_drink)

    assert result.health_impact_score is None
    assert any("cannot be classified as safe or healthy" in w for w in result.warnings)


# =====================================================================
# BeverageAnalysisService Tests
# =====================================================================

def test_analysis_service_full_workflow():
    service = BeverageAnalysisService()
    result = service.analyze(
        beverage_type="Wine",
        serving_size=150.0,
        serving_size_unit="ml",
        alcohol_percentage=12.5,
        alcohol_unit="%",
        sugar=2.5,
        sugar_unit="g",
        calories=125.0,
        calories_unit="kcal",
    )
    assert result.status == "success"
    assert result.normalized_input.beverage_type == BeverageType.WINE
    assert result.normalized_input.serving_size_ml == 150.0

    # 150 * 0.125 * 0.789 = 14.79375 -> 14.79 g
    assert result.calculations.alcohol_grams == 14.79
    assert result.calculations.alcohol_grams_unit == "g"

    # Energy per 100 mL: (125 / 150) * 100 = 83.3333 kcal/100 mL
    assert pytest.approx(result.calculations.energy_per_100ml_kcal, 0.01) == 83.33
    assert result.calculations.energy_per_100ml_unit == "kcal/100 mL"

    # Sugar concentration per 100 mL: (2.5 / 150) * 100 = 1.6667 g/100 mL
    assert pytest.approx(result.calculations.sugar_concentration_g_per_100ml, 0.01) == 1.67

    # Scores must be None
    assert result.composition_comparison.score is None
    assert result.health_assessment.health_impact_score is None

    # Sources should contain WHO citation
    assert any(s.get("publication_year") == 2023 for s in result.sources)


# =====================================================================
# API POST /api/analyze Integration Tests with Step 2 Fields
# =====================================================================

def test_api_analyze_with_unit_conversions():
    """
    Test POST /api/analyze handling unit conversion parameters (e.g. fl_oz, kJ).
    """
    payload = {
        "beverage_type": "Beer",
        "serving_size_ml": 12.0,
        "serving_size_unit": "fl_oz",  # 12 fl oz ~ 354.88 mL
        "sugar_g": 10000.0,
        "sugar_unit": "mg",            # 10000 mg -> 10 g
        "calories": 627.6,
        "calories_unit": "kj",         # 627.6 kJ -> 150 kcal
        "alcohol_percentage": 5.0,
        "alcohol_unit": "%",
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    # Serving size normalized to ~354.88 mL
    assert pytest.approx(data["input_data"]["serving_size_ml"], 0.1) == 354.88
    assert data["input_data"]["sugar_g"] == 10.0
    assert pytest.approx(data["input_data"]["calories"], 0.1) == 150.0

    # Conversions documented in input_data
    assert "conversions_applied" in data["input_data"]

    # Step 2 calculations schema
    calcs = data["calculations"]
    assert calcs["alcohol_grams"] is not None
    assert calcs["alcohol_grams_unit"] == "g"
    assert calcs["energy_per_100ml_kcal"] is not None
    assert calcs["energy_per_100ml_unit"] == "kcal/100 mL"

    # Step 2 structured comparison & health schemas
    assert "composition_comparison" in data
    assert data["composition_comparison"]["status"] in ["benchmark_unavailable", "not_evaluated"]
    assert data["composition_comparison"]["score"] is None

    assert "health_assessment" in data
    assert data["health_assessment"]["health_impact_score"] is None
    assert len(data["health_assessment"]["advisories"]) >= 1

    # Authoritative sources present
    assert len(data["sources"]) >= 1
    assert any("who.int" in str(s.get("source_url", "")) for s in data["sources"])


def test_api_analyze_preserves_omitted_units_and_fields():
    """
    Test POST /api/analyze with minimal fields preserving nulls.
    """
    payload = {
        "beverage_type": "Energy drink",
        "serving_size_ml": 250.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["input_data"]["sugar_g"] is None
    assert data["input_data"]["calories"] is None
    assert data["input_data"]["sodium_mg"] is None
    assert data["input_data"]["caffeine_mg"] is None
    assert data["input_data"]["alcohol_percentage"] is None

    assert data["calculations"]["alcohol_grams"] is None
    assert data["composition_score"] is None
    assert data["health_impact_score"] is None
    assert any("incomplete nutritional profile" in w for w in data["warnings"])
