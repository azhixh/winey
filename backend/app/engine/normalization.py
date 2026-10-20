"""
Unit normalization and input validation module for BQAS.

Key responsibilities:
- Convert various volume, mass, energy, and concentration units into standard SI / metric units.
- Validate serving size and composition boundaries.
- Preserve missing or unknown values strictly as None (null).
- Reject invalid units and impossible numeric values (negative, infinite, NaN, out-of-bounds).
"""

import math
from dataclasses import dataclass, field
from typing import Optional, Any
from app.schemas import BeverageType


class NormalizationError(ValueError):
    """Raised when an input fails unit normalization or numeric validation."""
    pass


# Supported unit conversion constants
VOLUME_CONVERSIONS_TO_ML: dict[str, float] = {
    "ml": 1.0,
    "milliliter": 1.0,
    "milliliters": 1.0,
    "l": 1000.0,
    "liter": 1000.0,
    "liters": 1000.0,
    "litre": 1000.0,
    "litres": 1000.0,
    "cl": 10.0,
    "centiliter": 10.0,
    "centiliters": 10.0,
    "fl_oz": 29.5735295625,
    "floz": 29.5735295625,
    "fl oz": 29.5735295625,
    "fluid_ounce": 29.5735295625,
    "fluid_ounces": 29.5735295625,
}

MASS_CONVERSIONS_TO_GRAMS: dict[str, float] = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "mg": 0.001,
    "milligram": 0.001,
    "milligrams": 0.001,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "kilograms": 1000.0,
}

MASS_CONVERSIONS_TO_MG: dict[str, float] = {
    "mg": 1.0,
    "milligram": 1.0,
    "milligrams": 1.0,
    "g": 1000.0,
    "gram": 1000.0,
    "grams": 1000.0,
    "mcg": 0.001,
    "ug": 0.001,
    "microgram": 0.001,
    "micrograms": 0.001,
}

ENERGY_CONVERSIONS_TO_KCAL: dict[str, float] = {
    "kcal": 1.0,
    "calories": 1.0,
    "cal": 1.0,
    "kilocalories": 1.0,
    "kj": 1.0 / 4.184,
    "kilojoules": 1.0 / 4.184,
}

ALCOHOL_PERCENTAGE_CONVERSIONS: dict[str, float] = {
    "%": 1.0,
    "percent": 1.0,
    "abv": 1.0,
    "pct": 1.0,
    "fraction": 100.0,
}


def _validate_numeric(val: Any, field_name: str) -> Optional[float]:
    """Validate that value is a finite number, or None."""
    if val is None:
        return None
    try:
        num = float(val)
    except (ValueError, TypeError):
        raise NormalizationError(f"{field_name} must be a valid numeric value.")
    if math.isnan(num) or math.isinf(num):
        raise NormalizationError(f"{field_name} cannot be NaN or infinite.")
    return num


def convert_volume(value: Optional[float], unit: str = "ml") -> Optional[float]:
    """
    Convert volume to milliliters (mL).
    Expected output unit: mL.
    Rejects values <= 0 mL or > 10,000 mL.
    """
    num = _validate_numeric(value, "Serving size")
    if num is None:
        return None
    clean_unit = unit.strip().lower()
    if clean_unit not in VOLUME_CONVERSIONS_TO_ML:
        valid_units = ", ".join(sorted(VOLUME_CONVERSIONS_TO_ML.keys()))
        raise NormalizationError(
            f"Unsupported volume unit: '{unit}'. Supported units are: {valid_units}"
        )
    ml_value = num * VOLUME_CONVERSIONS_TO_ML[clean_unit]
    if ml_value <= 0.0:
        raise NormalizationError("Serving size volume must be strictly greater than 0 mL.")
    if ml_value > 10000.0:
        raise NormalizationError("Serving size volume exceeds reasonable single serving limit (10000 mL).")
    return round(ml_value, 4)


def convert_mass_to_grams(value: Optional[float], unit: str = "g", field_name: str = "Sugar") -> Optional[float]:
    """
    Convert mass to grams (g).
    Expected output unit: g.
    Rejects values < 0 g or > 1000 g per serving.
    """
    num = _validate_numeric(value, field_name)
    if num is None:
        return None
    clean_unit = unit.strip().lower()
    if clean_unit not in MASS_CONVERSIONS_TO_GRAMS:
        valid_units = ", ".join(sorted(MASS_CONVERSIONS_TO_GRAMS.keys()))
        raise NormalizationError(
            f"Unsupported mass unit '{unit}' for {field_name}. Supported units are: {valid_units}"
        )
    grams = num * MASS_CONVERSIONS_TO_GRAMS[clean_unit]
    if grams < 0.0:
        raise NormalizationError(f"{field_name} content cannot be negative.")
    if grams > 1000.0:
        raise NormalizationError(f"{field_name} exceeds physical serving limit (1000 g).")
    return round(grams, 4)


def convert_mass_to_mg(value: Optional[float], unit: str = "mg", field_name: str = "Sodium/Caffeine") -> Optional[float]:
    """
    Convert mass to milligrams (mg).
    Expected output unit: mg.
    Rejects values < 0 mg.
    """
    num = _validate_numeric(value, field_name)
    if num is None:
        return None
    clean_unit = unit.strip().lower()
    if clean_unit not in MASS_CONVERSIONS_TO_MG:
        valid_units = ", ".join(sorted(MASS_CONVERSIONS_TO_MG.keys()))
        raise NormalizationError(
            f"Unsupported mass unit '{unit}' for {field_name}. Supported units are: {valid_units}"
        )
    mg = num * MASS_CONVERSIONS_TO_MG[clean_unit]
    if mg < 0.0:
        raise NormalizationError(f"{field_name} content cannot be negative.")
    if field_name.lower().startswith("sodium") and mg > 10000.0:
        raise NormalizationError("Sodium content exceeds reasonable single serving limit (10000 mg).")
    if field_name.lower().startswith("caffeine") and mg > 2000.0:
        raise NormalizationError("Caffeine content exceeds reasonable single serving limit (2000 mg).")
    return round(mg, 4)


def convert_energy_to_kcal(value: Optional[float], unit: str = "kcal") -> Optional[float]:
    """
    Convert energy to kilocalories (kcal).
    Expected output unit: kcal.
    Rejects values < 0 kcal or > 5000 kcal per serving.
    """
    num = _validate_numeric(value, "Calories")
    if num is None:
        return None
    clean_unit = unit.strip().lower()
    if clean_unit not in ENERGY_CONVERSIONS_TO_KCAL:
        valid_units = ", ".join(sorted(ENERGY_CONVERSIONS_TO_KCAL.keys()))
        raise NormalizationError(
            f"Unsupported energy unit '{unit}'. Supported units are: {valid_units}"
        )
    kcal = num * ENERGY_CONVERSIONS_TO_KCAL[clean_unit]
    if kcal < 0.0:
        raise NormalizationError("Energy content cannot be negative.")
    if kcal > 5000.0:
        raise NormalizationError("Energy content exceeds reasonable single serving limit (5000 kcal).")
    return round(kcal, 4)


def normalize_alcohol_percentage(value: Optional[float], unit: str = "%") -> Optional[float]:
    """
    Normalize alcohol percentage (% ABV).
    Expected output unit: % (0.0 to 100.0).
    Rejects values < 0% or > 100%.
    """
    num = _validate_numeric(value, "Alcohol percentage")
    if num is None:
        return None
    clean_unit = unit.strip().lower()
    if clean_unit not in ALCOHOL_PERCENTAGE_CONVERSIONS:
        valid_units = ", ".join(sorted(ALCOHOL_PERCENTAGE_CONVERSIONS.keys()))
        raise NormalizationError(
            f"Unsupported alcohol unit '{unit}'. Supported units are: {valid_units}"
        )
    pct = num * ALCOHOL_PERCENTAGE_CONVERSIONS[clean_unit]
    if pct < 0.0:
        raise NormalizationError("Alcohol percentage cannot be negative.")
    if pct > 100.0:
        raise NormalizationError("Alcohol percentage cannot exceed 100%.")
    return round(pct, 4)


@dataclass
class NormalizedBeverageData:
    """
    Standardized internal representation of beverage input metrics.
    All missing or unspecified metrics are strictly preserved as None.
    """
    beverage_type: BeverageType
    serving_size_ml: float
    sugar_g: Optional[float] = None
    sugar_concentration_g_per_100ml: Optional[float] = None
    calories: Optional[float] = None
    sodium_mg: Optional[float] = None
    caffeine_mg: Optional[float] = None
    alcohol_percentage: Optional[float] = None
    conversions_applied: dict[str, str] = field(default_factory=dict)


def normalize_beverage_input(
    beverage_type: Any,
    serving_size: float,
    serving_size_unit: str = "ml",
    sugar: Optional[float] = None,
    sugar_unit: str = "g",
    sugar_concentration_g_per_100ml: Optional[float] = None,
    calories: Optional[float] = None,
    calories_unit: str = "kcal",
    sodium: Optional[float] = None,
    sodium_unit: str = "mg",
    caffeine: Optional[float] = None,
    caffeine_unit: str = "mg",
    alcohol_percentage: Optional[float] = None,
    alcohol_unit: str = "%",
) -> NormalizedBeverageData:
    """
    Normalize raw user inputs into canonical internal representation.
    Preserves missing values as None, never replacing them with zero.
    """
    # 1. Validate Beverage Type
    if isinstance(beverage_type, BeverageType):
        norm_type = beverage_type
    elif isinstance(beverage_type, str):
        norm_type = BeverageType._missing_(beverage_type)
        if norm_type is None:
            valid_cats = ", ".join([b.value for b in BeverageType])
            raise NormalizationError(
                f"Invalid beverage type: '{beverage_type}'. Allowed types are: {valid_cats}"
            )
    else:
        raise NormalizationError("Beverage type must be a valid category string.")

    conversions: dict[str, str] = {}

    # 2. Normalize Serving Size
    norm_serving = convert_volume(serving_size, serving_size_unit)
    if norm_serving is None:
        raise NormalizationError("Serving size is required and cannot be null.")
    if serving_size_unit.lower() != "ml":
        conversions["serving_size"] = f"{serving_size} {serving_size_unit} -> {norm_serving} mL"

    # 3. Normalize Sugar
    norm_sugar = convert_mass_to_grams(sugar, sugar_unit, field_name="Sugar")
    if sugar is not None and sugar_unit.lower() != "g":
        conversions["sugar"] = f"{sugar} {sugar_unit} -> {norm_sugar} g"

    # Optional Sugar Concentration per 100 mL
    norm_conc = _validate_numeric(sugar_concentration_g_per_100ml, "Sugar concentration")
    if norm_conc is not None:
        if norm_conc < 0.0:
            raise NormalizationError("Sugar concentration cannot be negative.")
        if norm_conc > 100.0:
            raise NormalizationError("Sugar concentration cannot exceed 100 g/100 mL.")

    # 4. Normalize Calories
    norm_calories = convert_energy_to_kcal(calories, calories_unit)
    if calories is not None and calories_unit.lower() not in ("kcal", "calories"):
        conversions["calories"] = f"{calories} {calories_unit} -> {norm_calories} kcal"

    # 5. Normalize Sodium
    norm_sodium = convert_mass_to_mg(sodium, sodium_unit, field_name="Sodium")
    if sodium is not None and sodium_unit.lower() != "mg":
        conversions["sodium"] = f"{sodium} {sodium_unit} -> {norm_sodium} mg"

    # 6. Normalize Caffeine
    norm_caffeine = convert_mass_to_mg(caffeine, caffeine_unit, field_name="Caffeine")
    if caffeine is not None and caffeine_unit.lower() != "mg":
        conversions["caffeine"] = f"{caffeine} {caffeine_unit} -> {norm_caffeine} mg"

    # 7. Normalize Alcohol
    norm_alcohol = normalize_alcohol_percentage(alcohol_percentage, alcohol_unit)
    if alcohol_percentage is not None and alcohol_unit.lower() not in ("%", "abv", "pct"):
        conversions["alcohol_percentage"] = f"{alcohol_percentage} {alcohol_unit} -> {norm_alcohol}%"

    return NormalizedBeverageData(
        beverage_type=norm_type,
        serving_size_ml=norm_serving,
        sugar_g=norm_sugar,
        sugar_concentration_g_per_100ml=norm_conc,
        calories=norm_calories,
        sodium_mg=norm_sodium,
        caffeine_mg=norm_caffeine,
        alcohol_percentage=norm_alcohol,
        conversions_applied=conversions,
    )
