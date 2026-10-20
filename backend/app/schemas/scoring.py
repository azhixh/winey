"""
Pydantic schemas and typed result contracts for PRD Section 12 Scoring Engine.

Exposes deterministic, strongly-typed contracts for:
- Input normalization and user profiles (age group, weight, pregnancy, region, standard drink definition).
- Benchmark percentiles and classification.
- Piecewise guideline subscores and ratios.
- Health Impact Score (with critical overrides).
- Composition Score (PRD credit matrix).
- Confidence levels and partial analysis flags.
- Wine quality ML prediction metadata and regional applicability warnings.
"""

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class UserProfileSchema(BaseModel):
    """User personal profile for guideline limit scaling and personalization."""
    model_config = ConfigDict(populate_by_name=True)

    age_group: Literal["adult", "under_18"] = Field(
        default="adult",
        description="User age group ('adult' or 'under_18'). Minors receive strict caffeine and alcohol advisories."
    )
    weight_kg: float = Field(
        default=60.0,
        gt=0.0,
        le=500.0,
        description="Body weight in kilograms. Used for mg/kg/day ADI and caffeine scaling."
    )
    is_pregnant_or_breastfeeding: bool = Field(
        default=False,
        description="Pregnancy or breastfeeding status. Triggers 200 mg caffeine cap and alcohol contraindication."
    )
    has_diabetes: bool = Field(
        default=False,
        description="Diabetes flag for specialized dietary messaging."
    )
    has_heart_condition: bool = Field(
        default=False,
        description="Cardiac condition flag for stimulant advisories."
    )
    regulator_region: str = Field(
        default="WHO",
        description="Regional regulatory baseline ('WHO', 'EFSA', 'FDA', 'Health Canada')."
    )
    standard_drink_definition_g: float = Field(
        default=10.0,
        gt=0.0,
        description="Grams of pure ethanol per standard drink (WHO default: 10.0 g, US: 14.0 g, UK: 8.0 g)."
    )


class IngredientSubscoreSchema(BaseModel):
    """Individual guideline ingredient evaluation matching PRD Section 12 piecewise curve."""
    ingredient_key: str
    ingredient_name: str
    amount_per_serving: float
    amount_per_100ml: Optional[float] = None
    unit: str
    guideline_limit: float
    guideline_ratio: float
    band: str                               # 'Favourable', 'Moderate', 'Caution', 'High'
    subscore: float                         # 0.0 to 100.0
    daily_limit: Optional[float] = None
    daily_share: Optional[float] = None
    is_critical_breach: bool = False
    source_organization: str = ""
    source_url: str = ""
    publication_year: Optional[int] = None
    rationale: str = ""


class IngredientBenchmarkSchema(BaseModel):
    """Individual benchmark percentile classification against category reference distributions."""
    ingredient_key: str
    amount_evaluated: float
    unit: str
    status: str                             # 'lower_than_typical', 'typical', 'higher_than_typical', 'very_high', 'limited_benchmark_data'
    credit: Optional[float] = None          # 100, 60, 50, 20 or None
    percentile_band: Optional[str] = None   # '< P25', 'P25 - P75', 'P75 - P95', '> P95'
    sample_size: int
    is_sufficient: bool
    risk_direction: str


class CriticalOverrideSchema(BaseModel):
    """Critical override metadata and warning banner state."""
    is_critical: bool = False
    capped_score: Optional[float] = None
    uncapped_score: Optional[float] = None
    banner_color: Optional[str] = None
    critical_reasons: list[str] = Field(default_factory=list)


class WineModelResultSchema(BaseModel):
    """UCI Vinho Verde wine sensory quality machine learning estimation."""
    is_available: bool
    predicted_quality: Optional[float] = None
    predicted_rating: Optional[int] = None
    reason_if_unavailable: Optional[str] = None
    test_mae: Optional[float] = None
    model_limitations: Optional[str] = None
    disclaimer: Optional[str] = None


class ScoringEvaluationRequest(BaseModel):
    """Input payload for PRD Section 12 scoring engine."""
    model_config = ConfigDict(populate_by_name=True)

    beverage_type: str = Field(
        ...,
        description="Beverage category ('Soft drink', 'Beer', 'Wine', 'Spirits', 'Energy drink')",
        examples=["Soft drink"]
    )
    serving_size_ml: float = Field(
        ...,
        gt=0.0,
        le=5000.0,
        description="Serving size in mL. Must be positive.",
        examples=[330.0]
    )
    product_name: Optional[str] = Field(
        default=None,
        description="Optional brand or commercial beverage name"
    )
    wine_color: Optional[str] = Field(
        default=None,
        description="For Wine: 'red' or 'white'"
    )
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of ingredient amounts and units (e.g. {'sugars': 35.0, 'caffeine': 160.0})"
    )
    profile: Optional[UserProfileSchema] = Field(
        default=None,
        description="Personalization profile for limit scaling"
    )


class ScoringEvaluationResponse(BaseModel):
    """Complete, deterministic result contract for BQAS Scoring Engine."""
    beverage_type: str
    serving_size_ml: float
    product_name: Optional[str] = None

    # Scores (strictly separated)
    health_impact_score: Optional[float] = Field(
        default=None,
        description="Guideline-weighted health impact score (0-100). Capped at 40 upon critical override."
    )
    uncapped_health_impact_score: Optional[float] = Field(
        default=None,
        description="Underlying health score before critical capping, preserved for auditability."
    )
    composition_score: Optional[float] = Field(
        default=None,
        description="Empirical composition credit score (0-100) based on benchmark percentiles."
    )

    # Component evaluations
    guideline_evaluations: list[IngredientSubscoreSchema] = Field(default_factory=list)
    benchmark_evaluations: list[IngredientBenchmarkSchema] = Field(default_factory=list)

    # Alcohol specifics
    alcohol_grams: Optional[float] = None
    standard_drinks: Optional[float] = None
    alcohol_advisory: Optional[str] = None

    # Overrides and confidence
    critical_override: CriticalOverrideSchema = Field(default_factory=CriticalOverrideSchema)
    confidence_level: str                       # 'High', 'Medium', 'Low'
    confidence_percentage: float
    is_partial_analysis: bool

    # Categorical highlights
    higher_than_typical: list[str] = Field(default_factory=list)
    lower_than_typical: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str

    # Versions
    rules_version: str
    dataset_version: str

    # Wine ML integration
    wine_model: Optional[WineModelResultSchema] = None
