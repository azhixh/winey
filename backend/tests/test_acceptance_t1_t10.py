"""
Acceptance Test Fixtures T1 to T10 (PRD Section 18.1).

Verifies:
- T1: Soft drink sugar (330 ml, 35 g sugar -> 140% of ideal, 70% of cap, Caution band, subscore 44)
- T2: Adult caffeine (250 ml, 160 mg caffeine -> 80% of single dose, 40% of daily, Moderate band, subscore 76)
- T3: Under-18 caffeine (250 ml, 160 mg caffeine, 40 kg -> limit 120 mg, ratio ~1.33, Caution band, subscore ~47)
- T4: Wine alcohol (150 ml, 13% ABV -> 15.4 g alcohol, ~1.5 standard drinks, WHO statement, no safe label)
- T5: Beer alcohol (330 ml, 5% ABV -> 13.0 g alcohol, ~1.3 standard drinks)
- T6: Pregnancy caffeine (150 mg caffeine, pregnant -> 75% of daily, Moderate band, subscore 80)
- T7: Sparse input (2 of 7 weighted fields filled -> Low confidence, 'Partial analysis')
- T8: Critical methanol (methanol exceeds limit -> critical flag, red banner, Health Impact capped at 40)
- T9: Incomplete wine model (only Basic fields -> no quality prediction, explanation message)
- T10: Null caffeine from Open Food Facts (caffeine remains blank, not scored as zero)
"""

import pytest
from app.engine.scoring_engine import (
    BQASScoringEngine,
    UserProfile,
    calculate_guideline_ratio,
    calculate_subscore_from_ratio,
    calculate_alcohol_grams,
    calculate_standard_drinks,
)
from app.engine.wine_quality import WineQualityModelService, WineModelUnavailableError
from app.engine.data_quality import assess_product_data_quality


@pytest.fixture
def scoring_engine():
    return BQASScoringEngine()


# =====================================================================
# T1: Soft drink sugar
# =====================================================================
def test_t1_soft_drink_sugar(scoring_engine):
    """
    T1: Soft drink, 330 ml, 35 g sugar.
    Expected:
    - 140% of the 25 g ideal target
    - 70% of the 50 g cap
    - Band: Caution
    - Subscore: 44.0
    """
    result = scoring_engine.evaluate_beverage(
        beverage_type="Soft drink",
        serving_size_ml=330.0,
        inputs={"sugars": 35.0, "sugars_unit": "g"},
    )

    sugar_eval = next((g for g in result.guideline_evaluations if g.ingredient_key == "sugars"), None)
    assert sugar_eval is not None, "Sugars evaluation must be present."

    # 35 / 25 = 1.40 (140% of ideal)
    assert pytest.approx(sugar_eval.guideline_ratio, 0.01) == 1.40
    # 35 / 50 = 0.70 (70% of cap)
    assert pytest.approx(sugar_eval.daily_share, 0.01) == 0.70

    assert sugar_eval.band == "Caution"
    assert pytest.approx(sugar_eval.subscore, 0.1) == 44.0
    assert pytest.approx(result.health_impact_score, 0.1) == 44.0


# =====================================================================
# T2: Adult caffeine
# =====================================================================
def test_t2_adult_caffeine(scoring_engine):
    """
    T2: Energy drink, 250 ml, 160 mg caffeine, adult profile.
    Expected:
    - 80% of 200 mg single-dose figure (ratio 0.80)
    - 40% of 400 mg daily figure
    - Band: Moderate
    - Subscore: 76.0
    """
    profile = UserProfile(age_group="adult", weight_kg=70.0)
    result = scoring_engine.evaluate_beverage(
        beverage_type="Energy drink",
        serving_size_ml=250.0,
        inputs={"caffeine": 160.0, "caffeine_unit": "mg"},
        profile=profile,
    )

    caffeine_eval = next((g for g in result.guideline_evaluations if g.ingredient_key == "caffeine"), None)
    assert caffeine_eval is not None

    # 160 / 200 = 0.80 (80% of single dose)
    assert pytest.approx(caffeine_eval.guideline_ratio, 0.01) == 0.80
    # 160 / 400 = 0.40 (40% of daily)
    assert pytest.approx(caffeine_eval.daily_share, 0.01) == 0.40

    assert caffeine_eval.band == "Moderate"
    # 100 - (0.80 - 0.5) * 80 = 76.0
    assert pytest.approx(caffeine_eval.subscore, 0.1) == 76.0
    assert pytest.approx(result.health_impact_score, 0.1) == 76.0


# =====================================================================
# T3: Under-18 caffeine
# =====================================================================
def test_t3_under_18_caffeine(scoring_engine):
    """
    T3: Same drink (250 ml, 160 mg caffeine), 40 kg under-18 user.
    Expected:
    - Limit 120 mg (from 3 mg/kg * 40 kg)
    - Ratio approximately 1.33 (160 / 120)
    - Band: Caution
    - Subscore: approximately 47 (46.67)
    """
    profile = UserProfile(age_group="under_18", weight_kg=40.0)
    result = scoring_engine.evaluate_beverage(
        beverage_type="Energy drink",
        serving_size_ml=250.0,
        inputs={"caffeine": 160.0, "caffeine_unit": "mg"},
        profile=profile,
    )

    caffeine_eval = next((g for g in result.guideline_evaluations if g.ingredient_key == "caffeine"), None)
    assert caffeine_eval is not None

    assert caffeine_eval.guideline_limit == 120.0
    # 160 / 120 = 1.3333
    assert pytest.approx(caffeine_eval.guideline_ratio, 0.01) == 1.33
    assert caffeine_eval.band == "Caution"

    # 60 - (1.3333 - 1.0) * 40 = 60 - 13.33 = 46.67 -> rounds to 47
    assert round(caffeine_eval.subscore) == 47
    assert pytest.approx(caffeine_eval.subscore, 0.5) == 46.7


# =====================================================================
# T4: Wine alcohol
# =====================================================================
def test_t4_wine_alcohol(scoring_engine):
    """
    T4: Wine, 150 ml at 13% ABV.
    Expected:
    - 15.4 g alcohol (150 * 0.13 * 0.789 = 15.3855 g)
    - About 1.5 WHO standard drinks (15.3855 / 10 = 1.54)
    - WHO note shown
    - No 'safe' label
    """
    result = scoring_engine.evaluate_beverage(
        beverage_type="Wine",
        serving_size_ml=150.0,
        inputs={"alcohol": 13.0},
    )

    assert result.alcohol_grams is not None
    assert pytest.approx(result.alcohol_grams, 0.1) == 15.4

    assert result.standard_drinks is not None
    assert pytest.approx(result.standard_drinks, 0.1) == 1.5

    assert result.alcohol_advisory is not None
    assert "no level of alcohol consumption is completely safe" in result.alcohol_advisory.lower()
    assert "safe" not in result.disclaimer.lower() or "not" in result.disclaimer.lower()


# =====================================================================
# T5: Beer alcohol
# =====================================================================
def test_t5_beer_alcohol(scoring_engine):
    """
    T5: Beer, 330 ml at 5% ABV.
    Expected:
    - 13.0 g alcohol (330 * 0.05 * 0.789 = 13.0185 g)
    - About 1.3 WHO standard drinks (13.0185 / 10 = 1.3)
    """
    result = scoring_engine.evaluate_beverage(
        beverage_type="Beer",
        serving_size_ml=330.0,
        inputs={"alcohol": 5.0},
    )

    assert result.alcohol_grams is not None
    assert pytest.approx(result.alcohol_grams, 0.1) == 13.0

    assert result.standard_drinks is not None
    assert pytest.approx(result.standard_drinks, 0.1) == 1.3


# =====================================================================
# T6: Pregnancy caffeine
# =====================================================================
def test_t6_pregnancy_caffeine(scoring_engine):
    """
    T6: Pregnant user, 150 mg caffeine.
    Expected:
    - 75% of 200 mg daily figure (150 / 200 = 0.75)
    - Band: Moderate
    - Subscore: 80.0
    """
    profile = UserProfile(is_pregnant_or_breastfeeding=True)
    result = scoring_engine.evaluate_beverage(
        beverage_type="Energy drink",
        serving_size_ml=250.0,
        inputs={"caffeine": 150.0, "caffeine_unit": "mg"},
        profile=profile,
    )

    caffeine_eval = next((g for g in result.guideline_evaluations if g.ingredient_key == "caffeine"), None)
    assert caffeine_eval is not None

    # 150 / 200 = 0.75
    assert pytest.approx(caffeine_eval.guideline_ratio, 0.01) == 0.75
    assert caffeine_eval.band == "Moderate"
    # 100 - (0.75 - 0.5) * 80 = 80.0
    assert pytest.approx(caffeine_eval.subscore, 0.1) == 80.0
    assert pytest.approx(result.health_impact_score, 0.1) == 80.0


# =====================================================================
# T7: Sparse input
# =====================================================================
def test_t7_sparse_input(scoring_engine):
    """
    T7: 2 of 7 weighted fields filled (e.g. only sugar in soft drink).
    Expected:
    - Missing fields excluded from score calculation
    - Confidence: Low
    - Labelled 'Partial analysis'
    """
    result = scoring_engine.evaluate_beverage(
        beverage_type="Soft drink",
        serving_size_ml=330.0,
        inputs={"sugars": 20.0},  # only 1 field out of category fields
    )

    assert result.confidence_level == "Low"
    assert result.is_partial_analysis is True
    assert "sugars" not in result.missing_fields
    assert len(result.missing_fields) >= 2


# =====================================================================
# T8: Critical methanol
# =====================================================================
def test_t8_critical_methanol(scoring_engine):
    """
    T8: Methanol exceeds category limit (e.g. 15.0 g/L pure alcohol vs 10.0 limit).
    Expected:
    - Red critical banner metadata
    - Health Impact Score capped at 40
    """
    result = scoring_engine.evaluate_beverage(
        beverage_type="Spirits",
        serving_size_ml=50.0,
        inputs={"methanol": 15.0, "alcohol": 40.0},
    )

    assert result.critical_override.is_critical is True
    assert result.critical_override.banner_color == "red"
    assert any("Methanol level" in r for r in result.critical_override.critical_reasons)
    assert result.health_impact_score is not None
    assert result.health_impact_score <= 40.0


# =====================================================================
# T9: Incomplete wine model inputs
# =====================================================================
def test_t9_incomplete_wine_model_inputs(scoring_engine):
    """
    T9: Wine with only Basic fields (missing remaining physicochemical fields).
    Expected:
    - No quality prediction
    - Message explains why (missing required model inputs)
    """
    service = WineQualityModelService()
    basic_inputs = {
        "alcohol": 12.0,
        "residual_sugar": 2.0,
        "pH": 3.2,
        "total_sulfur_dioxide": 50.0,
        # Omitted: fixed_acidity, volatile_acidity, citric_acid, chlorides, free_sulfur_dioxide, density, sulphates
    }

    # Calling predict without the 11 required fields raises KeyError or clear ValueError
    with pytest.raises((KeyError, ValueError)) as excinfo:
        service.predict("red", basic_inputs)

    assert any(k in str(excinfo.value) for k in ["fixed_acidity", "volatile_acidity", "density"])

    # Calling scoring engine with basic inputs returns wine_model with is_available=False and clear explanation
    engine_res = scoring_engine.evaluate_beverage(
        beverage_type="Wine",
        serving_size_ml=150.0,
        inputs=basic_inputs,
    )
    assert engine_res.wine_model is not None
    assert engine_res.wine_model["is_available"] is False
    assert engine_res.wine_model["predicted_quality"] is None
    assert "fixed_acidity" in engine_res.wine_model["reason_if_unavailable"]
    assert "Portuguese Vinho Verde" in engine_res.wine_model["model_limitations"]



# =====================================================================
# T10: Null caffeine from Open Food Facts
# =====================================================================
def test_t10_null_caffeine_from_open_food_facts(scoring_engine):
    """
    T10: Open Food Facts product returns null for caffeine.
    Expected:
    - Caffeine field remains blank / null
    - Data quality flag notes missing nutrient
    - Caffeine is never scored or interpreted as zero
    """
    from app.providers.open_food_facts import OpenFoodFactsProvider

    provider = OpenFoodFactsProvider()
    mock_off_payload = {
        "code": "1234567890123",
        "product_name": "Test Energy Zero Caffeine Field",
        "categories_tags": ["en:energy-drinks"],
        "serving_size": "250 ml",
        "nutriments": {
            "sugars_100g": 11.0,
            "sugars_serving": 27.5,
            "energy-kcal_100g": 45.0,
            "sodium_100g": 0.05,
            # Notice: 'caffeine_100g' and 'caffeine_serving' are absent / null
        },
        "ingredients_text": "Carbonated water, sugar, taurine, vitamins",
    }

    product = provider._parse_product_record(mock_off_payload)
    assert product is not None, "Product record should be parsed successfully"

    # 1. Caffeine field remains blank / null
    assert product.nutritional_values.caffeine_per_100ml is None, "Caffeine per 100ml must remain None"
    assert product.nutritional_values.caffeine_per_serving is None, "Caffeine per serving must remain None"

    # 2. Data quality flag notes missing quantitative caffeine
    assert any("caffeine" in w.lower() for w in product.data_quality_warnings), (
        "Missing caffeine must produce an explicit warning."
    )

    # 3. When evaluated in scoring engine, caffeine is never treated or scored as zero
    result = scoring_engine.evaluate_beverage(
        beverage_type="Energy drink",
        serving_size_ml=250.0,
        inputs={
            "sugars": product.nutritional_values.sugar_per_serving,
            "caffeine": product.nutritional_values.caffeine_per_serving,
        },
    )

    assert "caffeine" in result.missing_fields
    caffeine_eval = next((g for g in result.guideline_evaluations if g.ingredient_key == "caffeine"), None)
    assert caffeine_eval is None, "Caffeine must NOT be evaluated when value is null (never imputed as 0)"

