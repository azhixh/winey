"""
Tests for app.engine.data_quality module:
- Scope validation (allows Soft drink and Energy drink, rejects Beer, Wine, Spirits)
- Data quality warnings (unverified provider claims, missing serving size, missing nutrients, implausible values)
- Null preservation without zero-defaulting
"""

import pytest
from app.engine.data_quality import (
    validate_beverage_scope,
    assess_product_data_quality,
    ScopeRestrictionError,
    SUPPORTED_NON_ALCOHOLIC_CATEGORIES,
    DISALLOWED_ALCOHOLIC_CATEGORIES,
)


# =====================================================================
# Beverage Scope Validation Tests
# =====================================================================

def test_validate_beverage_scope_allows_soft_drink_and_energy_drink():
    assert validate_beverage_scope("Soft drink") == "Soft drink"
    assert validate_beverage_scope("soft drink") == "Soft drink"
    assert validate_beverage_scope("Energy drink") == "Energy drink"
    assert validate_beverage_scope("energy drink") == "Energy drink"
    assert validate_beverage_scope(None) is None


@pytest.mark.parametrize("disallowed", DISALLOWED_ALCOHOLIC_CATEGORIES)
def test_validate_beverage_scope_rejects_alcoholic_categories(disallowed):
    """
    Step 3 scope strictly excludes alcoholic beverage product lookup.
    """
    with pytest.raises(ScopeRestrictionError, match="strictly disallowed in Step 3"):
        validate_beverage_scope(disallowed)

    # Test lowercase
    with pytest.raises(ScopeRestrictionError, match="strictly disallowed in Step 3"):
        validate_beverage_scope(disallowed.lower())


def test_validate_beverage_scope_rejects_unknown_category():
    with pytest.raises(ScopeRestrictionError, match="Only non-alcoholic beverages"):
        validate_beverage_scope("Kombucha")


# =====================================================================
# Data Quality Assessment Tests
# =====================================================================

def test_assess_data_quality_unverified_provider_notice():
    """
    Unverified provider data must always be flagged clearly to users.
    """
    warnings = assess_product_data_quality(
        product_name="Generic Cola",
        beverage_type="Soft drink",
        serving_size_value=330.0,
        serving_size_unit="ml",
        sugar_per_100ml=10.5,
        sugar_per_serving=34.65,
        calories_per_100ml=42.0,
        calories_per_serving=138.6,
        sodium_per_100ml=15.0,
        sodium_per_serving=49.5,
        caffeine_per_100ml=10.0,
        caffeine_per_serving=33.0,
        ingredients="Carbonated water, sugar, caramel color, phosphoric acid",
        is_independently_verified=False,
        source_name="Open Food Facts",
    )
    assert any("self-declared by manufacturers" in w for w in warnings)
    assert any("not been independently laboratory verified" in w for w in warnings)


def test_assess_data_quality_missing_serving_size():
    warnings = assess_product_data_quality(
        product_name="Generic Cola",
        beverage_type="Soft drink",
        serving_size_value=None,
        serving_size_unit=None,
        sugar_per_100ml=10.5,
        sugar_per_serving=None,
        calories_per_100ml=42.0,
        calories_per_serving=None,
        sodium_per_100ml=10.0,
        sodium_per_serving=None,
        caffeine_per_100ml=None,
        caffeine_per_serving=None,
        ingredients="Water, Sugar",
        is_independently_verified=False,
    )
    assert any("Serving size is missing or unparseable" in w for w in warnings)


def test_assess_data_quality_missing_nutrients_preserved_and_flagged():
    """
    Missing nutrients must trigger an incomplete data notice and never be defaulted to 0.
    """
    warnings = assess_product_data_quality(
        product_name="Sparkling Drink",
        beverage_type="Soft drink",
        serving_size_value=250.0,
        serving_size_unit="ml",
        sugar_per_100ml=None,
        sugar_per_serving=None,
        calories_per_100ml=None,
        calories_per_serving=None,
        sodium_per_100ml=None,
        sodium_per_serving=None,
        caffeine_per_100ml=None,
        caffeine_per_serving=None,
        ingredients="Water, Natural Flavors",
        is_independently_verified=False,
    )
    assert any("Missing core nutrient data for: [sugar, calories, sodium]" in w for w in warnings)
    assert any("Values preserved as null" in w for w in warnings)


def test_assess_data_quality_energy_drink_missing_caffeine():
    """
    Energy drink missing caffeine reporting must be flagged explicitly.
    """
    warnings = assess_product_data_quality(
        product_name="Power Surge",
        beverage_type="Energy drink",
        serving_size_value=500.0,
        serving_size_unit="ml",
        sugar_per_100ml=11.0,
        sugar_per_serving=55.0,
        calories_per_100ml=45.0,
        calories_per_serving=225.0,
        sodium_per_100ml=20.0,
        sodium_per_serving=100.0,
        caffeine_per_100ml=None,
        caffeine_per_serving=None,
        ingredients="Water, Sugar, Taurine, B-Vitamins",
        is_independently_verified=False,
    )
    assert any("does not report quantitative caffeine content" in w for w in warnings)


def test_assess_data_quality_implausible_physical_values():
    """
    Detects impossible values (negative values, sugar > 100 g/100 mL, calories > 400 kcal/100 mL).
    """
    warnings = assess_product_data_quality(
        product_name="Suspicious Beverage",
        beverage_type="Soft drink",
        serving_size_value=250.0,
        serving_size_unit="ml",
        sugar_per_100ml=120.0,      # > 100g/100ml is physically impossible
        sugar_per_serving=300.0,
        calories_per_100ml=-5.0,     # Negative calories
        calories_per_serving=-12.5,
        sodium_per_100ml=-1.0,       # Negative sodium
        sodium_per_serving=-2.5,
        caffeine_per_100ml=-1.0,     # Negative caffeine
        caffeine_per_serving=-2.5,
        ingredients="",              # Missing ingredients
        is_independently_verified=False,
    )
    assert any("exceeds maximum physical limit of 100 g" in w for w in warnings)
    assert any("Reported calorie content is negative" in w for w in warnings)
    assert any("Reported sodium content is negative" in w for w in warnings)
    assert any("Reported caffeine content is negative" in w for w in warnings)
    assert any("Ingredients list was not provided" in w for w in warnings)
