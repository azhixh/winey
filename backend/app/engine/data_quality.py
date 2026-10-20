"""
Data quality assessment and scope validation engine for external beverage records.

Responsibilities:
- Validate that product lookups are restricted to non-alcoholic beverages (Soft drink, Energy drink).
- Reject alcoholic beverage categories (Beer, Wine, Spirits) from external product search.
- Evaluate completeness, plausible physical bounds, and provider declaration statuses.
- Generate objective, non-fabricated data quality warnings.
- Explicitly flag unverified provider declarations.
"""

from typing import Optional
from app.schemas.products import ProductRecord, NonAlcoholicCategory


class ScopeRestrictionError(ValueError):
    """Raised when an alcoholic beverage lookup is attempted."""
    pass


class DataQualityError(ValueError):
    """Raised when a product record violates critical data consistency rules."""
    pass


SUPPORTED_NON_ALCOHOLIC_CATEGORIES = [
    NonAlcoholicCategory.SOFT_DRINK.value,
    NonAlcoholicCategory.ENERGY_DRINK.value,
]

DISALLOWED_ALCOHOLIC_CATEGORIES = [
    "Beer",
    "Wine",
    "Spirits",
]


def validate_beverage_scope(beverage_type: Optional[str]) -> Optional[str]:
    """
    Validate that the requested beverage type is within the Step 3 non-alcoholic scope.
    Allowed: 'Soft drink', 'Energy drink' (case-insensitive).
    Rejects: 'Beer', 'Wine', 'Spirits', and unknown types.
    """
    if beverage_type is None:
        return None

    clean_type = beverage_type.strip().lower()

    # Check for alcoholic beverage requests
    for alc in DISALLOWED_ALCOHOLIC_CATEGORIES:
        if clean_type == alc.lower():
            raise ScopeRestrictionError(
                f"Alcoholic beverage lookup for '{beverage_type}' is strictly disallowed in Step 3. "
                "Product lookup is currently restricted to non-alcoholic beverages (Soft drink, Energy drink)."
            )

    # Check if matching supported categories
    for supported in SUPPORTED_NON_ALCOHOLIC_CATEGORIES:
        if clean_type == supported.lower():
            return supported

    # If it's something else
    allowed_list = ", ".join(SUPPORTED_NON_ALCOHOLIC_CATEGORIES)
    raise ScopeRestrictionError(
        f"Unsupported category '{beverage_type}'. Only non-alcoholic beverages ({allowed_list}) are supported."
    )


def assess_product_data_quality(
    product_name: str,
    beverage_type: Optional[str],
    serving_size_value: Optional[float],
    serving_size_unit: Optional[str],
    sugar_per_100ml: Optional[float],
    sugar_per_serving: Optional[float],
    calories_per_100ml: Optional[float],
    calories_per_serving: Optional[float],
    sodium_per_100ml: Optional[float],
    sodium_per_serving: Optional[float],
    caffeine_per_100ml: Optional[float],
    caffeine_per_serving: Optional[float],
    ingredients: Optional[str],
    is_independently_verified: bool = False,
    source_name: str = "Unknown",
) -> list[str]:
    """
    Evaluate data quality and completeness for a single product record.
    Returns a list of clear, human-readable data quality notices.
    """
    warnings: list[str] = []

    # 1. Verification status notice
    if not is_independently_verified:
        warnings.append(
            f"Provider-supplied record from '{source_name}': values are self-declared by manufacturers or community contributors and have not been independently laboratory verified."
        )

    # 2. Serving size validation
    if serving_size_value is None or serving_size_value <= 0.0:
        warnings.append("Serving size is missing or unparseable; per-serving calculations cannot be verified.")
    elif serving_size_value > 5000.0:
        warnings.append(f"Unusually large serving size reported ({serving_size_value} {serving_size_unit or 'mL'}).")

    # 3. Missing nutritional values (Preserved as null, never zero)
    missing_nutrients: list[str] = []
    if sugar_per_100ml is None and sugar_per_serving is None:
        missing_nutrients.append("sugar")
    if calories_per_100ml is None and calories_per_serving is None:
        missing_nutrients.append("calories")
    if sodium_per_100ml is None and sodium_per_serving is None:
        missing_nutrients.append("sodium")

    if missing_nutrients:
        warnings.append(
            f"Missing core nutrient data for: [{', '.join(missing_nutrients)}]. Values preserved as null; incomplete records cannot be used for composite scoring."
        )

    # 4. Energy drink specific check
    bev_type_clean = (beverage_type or "").strip().lower()
    if "energy" in bev_type_clean:
        if caffeine_per_100ml is None and caffeine_per_serving is None:
            warnings.append(
                "Energy drink product does not report quantitative caffeine content. Caffeine presence should not be assumed to be zero."
            )

    # 5. Implausible physical values checks
    if sugar_per_100ml is not None:
        if sugar_per_100ml < 0.0:
            warnings.append("Reported sugar content is negative, indicating provider data corruption.")
        elif sugar_per_100ml > 100.0:
            warnings.append(f"Implausibly high sugar content ({sugar_per_100ml} g/100 mL exceeds maximum physical limit of 100 g).")

    if calories_per_100ml is not None:
        if calories_per_100ml < 0.0:
            warnings.append("Reported calorie content is negative.")
        elif calories_per_100ml > 400.0:
            warnings.append(f"Unusually high energy density ({calories_per_100ml} kcal/100 mL) for a non-fat beverage.")

    if sodium_per_100ml is not None and sodium_per_100ml < 0.0:
        warnings.append("Reported sodium content is negative.")

    if caffeine_per_100ml is not None and caffeine_per_100ml < 0.0:
        warnings.append("Reported caffeine content is negative.")

    # 6. Ingredients text presence
    if not ingredients or not ingredients.strip():
        warnings.append("Ingredients list was not provided by the data source.")

    return warnings
