"""
Unit tests for app.engine.normalization module:
- Volume unit conversions (mL, L, cL, fl oz)
- Mass unit conversions (g, mg, kg)
- Energy conversions (kcal, kJ)
- Alcohol percentage normalization (%, fraction)
- Missing-value preservation (strictly None/null, never default to 0)
- Validation boundaries and rejection of impossible/invalid inputs
"""

import math
import pytest
from app.schemas import BeverageType
from app.engine.normalization import (
    convert_volume,
    convert_mass_to_grams,
    convert_mass_to_mg,
    convert_energy_to_kcal,
    normalize_alcohol_percentage,
    normalize_beverage_input,
    NormalizationError,
)


# =====================================================================
# Volume Unit Conversion Tests
# =====================================================================

def test_convert_volume_standard_ml():
    assert convert_volume(250.0, "ml") == 250.0
    assert convert_volume(330.0, "milliliter") == 330.0


def test_convert_volume_liters():
    assert convert_volume(1.5, "l") == 1500.0
    assert convert_volume(0.5, "liter") == 500.0


def test_convert_volume_centiliters():
    assert convert_volume(75.0, "cl") == 750.0
    assert convert_volume(33.0, "centiliters") == 330.0


def test_convert_volume_fluid_ounces():
    # 12 fl oz can ~ 354.8824 mL
    res = convert_volume(12.0, "fl_oz")
    assert pytest.approx(res, 0.01) == 354.88
    # Test alternate spellings
    assert pytest.approx(convert_volume(12.0, "floz"), 0.01) == 354.88
    assert pytest.approx(convert_volume(12.0, "fl oz"), 0.01) == 354.88


def test_convert_volume_invalid_unit():
    with pytest.raises(NormalizationError, match="Unsupported volume unit"):
        convert_volume(250.0, "gallons")


def test_convert_volume_non_positive_and_out_of_bounds():
    with pytest.raises(NormalizationError, match="strictly greater than 0"):
        convert_volume(0.0, "ml")

    with pytest.raises(NormalizationError, match="strictly greater than 0"):
        convert_volume(-250.0, "ml")

    with pytest.raises(NormalizationError, match="exceeds reasonable single serving limit"):
        convert_volume(15000.0, "ml")


def test_convert_volume_nan_and_inf():
    with pytest.raises(NormalizationError, match="cannot be NaN or infinite"):
        convert_volume(float("nan"), "ml")

    with pytest.raises(NormalizationError, match="cannot be NaN or infinite"):
        convert_volume(float("inf"), "ml")


# =====================================================================
# Mass & Energy Conversion Tests
# =====================================================================

def test_convert_mass_to_grams():
    assert convert_mass_to_grams(10.5, "g") == 10.5
    assert convert_mass_to_grams(5000.0, "mg") == 5.0
    assert convert_mass_to_grams(0.05, "kg") == 50.0


def test_convert_mass_invalid_unit():
    with pytest.raises(NormalizationError, match="Unsupported mass unit"):
        convert_mass_to_grams(10.0, "pounds")


def test_convert_mass_negative():
    with pytest.raises(NormalizationError, match="cannot be negative"):
        convert_mass_to_grams(-1.0, "g")


def test_convert_mass_to_mg():
    assert convert_mass_to_mg(50.0, "mg") == 50.0
    assert convert_mass_to_mg(0.05, "g") == 50.0
    assert convert_mass_to_mg(2000.0, "mcg") == 2.0


def test_convert_energy_to_kcal():
    assert convert_energy_to_kcal(150.0, "kcal") == 150.0
    # 418.4 kJ = 100 kcal
    assert pytest.approx(convert_energy_to_kcal(418.4, "kj"), 0.01) == 100.0


def test_convert_energy_negative():
    with pytest.raises(NormalizationError, match="cannot be negative"):
        convert_energy_to_kcal(-10.0, "kcal")


# =====================================================================
# Alcohol Percentage Normalization Tests
# =====================================================================

def test_normalize_alcohol_percentage():
    assert normalize_alcohol_percentage(5.0, "%") == 5.0
    assert normalize_alcohol_percentage(12.5, "abv") == 12.5
    assert normalize_alcohol_percentage(0.05, "fraction") == 5.0


def test_normalize_alcohol_invalid():
    with pytest.raises(NormalizationError, match="cannot be negative"):
        normalize_alcohol_percentage(-1.0, "%")

    with pytest.raises(NormalizationError, match="cannot exceed 100%"):
        normalize_alcohol_percentage(105.0, "%")


# =====================================================================
# normalize_beverage_input Overall Function Tests
# =====================================================================

def test_normalize_beverage_input_preserves_nulls():
    """
    Ensure missing values are strictly None and NOT replaced with zero.
    """
    norm = normalize_beverage_input(
        beverage_type=BeverageType.BEER,
        serving_size=500.0,
        serving_size_unit="ml",
    )
    assert norm.beverage_type == BeverageType.BEER
    assert norm.serving_size_ml == 500.0
    assert norm.sugar_g is None
    assert norm.sugar_concentration_g_per_100ml is None
    assert norm.calories is None
    assert norm.sodium_mg is None
    assert norm.caffeine_mg is None
    assert norm.alcohol_percentage is None


def test_normalize_beverage_input_with_unit_conversions():
    """
    Ensure unit conversions are properly tracked in conversions_applied.
    """
    norm = normalize_beverage_input(
        beverage_type="Energy drink",
        serving_size=1.0,
        serving_size_unit="l",  # 1.0 L -> 1000.0 mL
        sugar=25000.0,
        sugar_unit="mg",        # 25000 mg -> 25 g
        calories=836.8,
        calories_unit="kj",     # 836.8 kJ -> 200 kcal
        caffeine=0.08,
        caffeine_unit="g",      # 0.08 g -> 80 mg
        alcohol_percentage=0.0,
        alcohol_unit="%",
    )
    assert norm.beverage_type == BeverageType.ENERGY_DRINK
    assert norm.serving_size_ml == 1000.0
    assert norm.sugar_g == 25.0
    assert pytest.approx(norm.calories, 0.01) == 200.0
    assert norm.caffeine_mg == 80.0
    assert norm.alcohol_percentage == 0.0
    assert "serving_size" in norm.conversions_applied
    assert "sugar" in norm.conversions_applied
    assert "calories" in norm.conversions_applied
    assert "caffeine" in norm.conversions_applied


def test_normalize_beverage_input_invalid_beverage_type():
    with pytest.raises(NormalizationError, match="Invalid beverage type"):
        normalize_beverage_input(
            beverage_type="Sparkling Water",
            serving_size=250.0,
        )
