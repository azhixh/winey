"""
Pydantic schemas and data transfer objects for the Beverage Quality Analysis System (BQAS).
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, AliasChoices

from .products import (
    NonAlcoholicCategory,
    NutritionalValues,
    ProductRecord,
    ProductSearchResponse,
    DataSourceInfo,
    DataSourcesResponse,
)
from .wine import (
    WineType,
    WinePredictionRequest,
    WinePredictionResponse,
)


class BeverageType(str, Enum):
    """
    Supported beverage categories for BQAS.
    Normalization supports case-insensitive lookup.
    """
    SOFT_DRINK = "Soft drink"
    BEER = "Beer"
    WINE = "Wine"
    SPIRITS = "Spirits"
    ENERGY_DRINK = "Energy drink"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            clean_val = value.strip().lower()
            for member in cls:
                if member.value.lower() == clean_val:
                    return member
        return None


class HealthResponse(BaseModel):
    """
    Server health check response schema.
    """
    status: str = Field(default="ok", description="Server operational status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application semantic version")
    environment: str = Field(default="development", description="Runtime environment")


class BeverageTypesResponse(BaseModel):
    """
    List of supported beverage categories response schema.
    """
    beverage_types: list[str] = Field(
        ...,
        description="List of supported beverage categories",
        examples=[["Soft drink", "Beer", "Wine", "Spirits", "Energy drink"]]
    )
    total: int = Field(..., description="Total count of supported beverage types")


class AnalysisRequest(BaseModel):
    """
    Input payload for beverage composition analysis.
    Validates positive serving sizes, nonnegative composition values, and reasonable physical limits.
    All nutritional fields are optional and preserve null when omitted.
    Supports flexible unit specifications.
    """
    model_config = ConfigDict(populate_by_name=True)

    beverage_type: BeverageType = Field(
        ...,
        description="Category of the beverage (Soft drink, Beer, Wine, Spirits, Energy drink)",
        examples=["Beer"]
    )
    serving_size_ml: float = Field(
        ...,
        gt=0.0,
        le=5000.0,
        validation_alias=AliasChoices("serving_size_ml", "serving_size"),
        description="Serving size in milliliters (mL). Must be strictly positive and <= 5000 mL.",
        examples=[330.0]
    )
    serving_size_unit: str = Field(
        default="ml",
        description="Unit for serving size (ml, l, cl, fl_oz)",
    )
    sugar_g: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1000000.0,
        validation_alias=AliasChoices("sugar_g", "sugar"),
        description="Sugar content per serving. Optional, non-negative.",
        examples=[12.5]
    )
    sugar_unit: str = Field(
        default="g",
        description="Unit for sugar (g, mg, kg)",
    )
    sugar_concentration_g_per_100ml: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Sugar concentration in grams per 100 mL (g/100 mL). Optional, non-negative.",
        examples=[3.8]
    )
    calories: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=25000.0,
        validation_alias=AliasChoices("calories", "calories_kcal", "energy_kcal"),
        description="Energy content per serving. Optional, non-negative.",
        examples=[150.0]
    )
    calories_unit: str = Field(
        default="kcal",
        description="Unit for calories (kcal, kj)",
    )
    sodium_mg: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10000000.0,
        validation_alias=AliasChoices("sodium_mg", "sodium"),
        description="Sodium content per serving. Optional, non-negative.",
        examples=[10.0]
    )
    sodium_unit: str = Field(
        default="mg",
        description="Unit for sodium (mg, g)",
    )
    caffeine_mg: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2000000.0,
        validation_alias=AliasChoices("caffeine_mg", "caffeine"),
        description="Caffeine content per serving. Optional, non-negative.",
        examples=[32.0]
    )
    caffeine_unit: str = Field(
        default="mg",
        description="Unit for caffeine (mg, g, mcg)",
    )
    alcohol_percentage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        validation_alias=AliasChoices("alcohol_percentage", "alcohol_pct", "abv"),
        description="Alcohol by volume (ABV) as a percentage (0.0 to 100.0%). Optional, non-negative.",
        examples=[5.0]
    )
    alcohol_unit: str = Field(
        default="%",
        description="Unit for alcohol (% or fraction)",
    )


class AnalysisInputData(BaseModel):
    """
    Echoed input values preserving missing values as null (never defaulting to zero).
    """
    beverage_type: BeverageType
    serving_size_ml: float
    sugar_g: Optional[float] = None
    sugar_concentration_g_per_100ml: Optional[float] = None
    calories: Optional[float] = None
    sodium_mg: Optional[float] = None
    caffeine_mg: Optional[float] = None
    alcohol_percentage: Optional[float] = None
    conversions_applied: dict[str, str] = Field(default_factory=dict)


class CalculationsResult(BaseModel):
    """
    Deterministic physical and chemical calculations with explicit unit documentation.
    """
    alcohol_grams: Optional[float] = Field(
        default=None,
        description="Calculated alcohol mass in grams: serving_size_ml * (alcohol_percentage / 100) * 0.789 g/mL. Null if alcohol_percentage is not provided."
    )
    alcohol_grams_unit: str = Field(default="g", description="Unit of calculated alcohol mass")
    ethanol_density_used_g_ml: float = Field(
        default=0.789,
        description="Density of pure ethanol in g/mL used in calculation"
    )
    sugar_per_serving_g: Optional[float] = Field(
        default=None,
        description="Calculated or provided sugar mass per serving in grams (g)"
    )
    sugar_per_serving_unit: str = Field(default="g", description="Unit for sugar per serving")
    energy_per_100ml_kcal: Optional[float] = Field(
        default=None,
        description="Calculated energy density in kcal per 100 mL"
    )
    energy_per_100ml_unit: str = Field(default="kcal/100 mL", description="Unit for energy per 100 mL")
    sugar_concentration_g_per_100ml: Optional[float] = Field(
        default=None,
        description="Sugar concentration in grams per 100 mL"
    )
    sugar_concentration_unit: str = Field(default="g/100 mL", description="Unit for sugar concentration")
    explanations: list[str] = Field(default_factory=list, description="Calculation explanations or missing input notes")


class CompositionComparisonResponse(BaseModel):
    """
    Structured composition comparison result against verified reference datasets.
    """
    status: str = Field(
        default="insufficient_data",
        description="Status of composition comparison ('available', 'insufficient_data', 'not_evaluated')"
    )
    score: Optional[float] = Field(
        default=None,
        description="Percentile or benchmark score. Null when benchmark is unavailable, unverified, or has < 100 records."
    )
    percentile: Optional[float] = Field(
        default=None,
        description="Empirical percentile rank within reference dataset. Null if benchmark is unavailable."
    )
    metric_evaluated: Optional[str] = Field(default=None, description="Metric evaluated against benchmark")
    benchmark_name: Optional[str] = Field(default=None, description="Name of the validated benchmark dataset")
    dataset_version: Optional[str] = Field(default=None, description="Version string of the reference dataset")
    sample_size: Optional[int] = Field(default=None, description="Number of valid, non-null records in benchmark")
    calculation_method: Optional[str] = Field(default=None, description="Calculation methodology used (e.g. 'empirical_percentile')")
    limitations: list[str] = Field(default_factory=list, description="Methodological constraints and dataset limitations")
    dataset_metadata: Optional[dict[str, Any]] = Field(default=None, description="Extended metadata of reference dataset")
    explanation: str = Field(default="", description="Explanatory details of comparison or reasons for absence")


class HealthAssessmentResponse(BaseModel):
    """
    Structured evidence-backed health evaluation outcome.
    """
    status: str = Field(
        default="insufficient_data",
        description="Status of health assessment ('available', 'insufficient_data', 'not_evaluated')"
    )
    health_impact_score: Optional[float] = Field(
        default=None,
        description="Composite health score. Strictly null to prevent ungrounded medical claims."
    )
    observations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Evidence-backed observations citing authoritative scientific sources"
    )
    advisories: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Triggered evidence-based advisories and hazard notices"
    )
    missing_data_notices: list[str] = Field(
        default_factory=list,
        description="Explicit notices detailing missing nutritional variables"
    )
    warnings: list[str] = Field(default_factory=list, description="Health evaluation caveats and warnings")
    sources: list[dict[str, Any]] = Field(default_factory=list, description="Authoritative reference sources")
    limitations: list[str] = Field(
        default_factory=list,
        description="Scientific limitations and scope boundaries of the assessment"
    )


class AnalysisResponse(BaseModel):
    """
    Structured response for beverage analysis.
    Scores remain strictly null until validated datasets and evidence-backed rules are integrated.
    """
    status: str = Field(default="success", description="Status indicator of the analysis response")
    input_data: AnalysisInputData = Field(..., description="Input data echoed back preserving null values")
    calculations: CalculationsResult = Field(..., description="Available deterministic calculations")
    composition_score: Optional[float] = Field(
        default=None,
        description="Placeholder composition score. Maintained as null until verified models are implemented."
    )
    health_impact_score: Optional[float] = Field(
        default=None,
        description="Placeholder health impact score. Maintained as null until verified models are implemented."
    )
    composition_comparison: Optional[CompositionComparisonResponse] = Field(
        default=None,
        description="Structured comparison against validated reference datasets"
    )
    health_assessment: Optional[HealthAssessmentResponse] = Field(
        default=None,
        description="Structured evidence-grounded health impact assessment"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Contextual warnings regarding omitted values, calculation notes, and scoring constraints"
    )
    sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Authoritative references cited in the analysis"
    )


from .scoring import (
    UserProfileSchema,
    IngredientSubscoreSchema,
    IngredientBenchmarkSchema,
    CriticalOverrideSchema,
    WineModelResultSchema,
    ScoringEvaluationRequest,
    ScoringEvaluationResponse,
)


__all__ = [
    "BeverageType",
    "HealthResponse",
    "BeverageTypesResponse",
    "AnalysisRequest",
    "AnalysisInputData",
    "CalculationsResult",
    "CompositionComparisonResponse",
    "HealthAssessmentResponse",
    "AnalysisResponse",
    "NonAlcoholicCategory",
    "NutritionalValues",
    "ProductRecord",
    "ProductSearchResponse",
    "DataSourceInfo",
    "DataSourcesResponse",
    "WineType",
    "WinePredictionRequest",
    "WinePredictionResponse",
    "UserProfileSchema",
    "IngredientSubscoreSchema",
    "IngredientBenchmarkSchema",
    "CriticalOverrideSchema",
    "WineModelResultSchema",
    "ScoringEvaluationRequest",
    "ScoringEvaluationResponse",
]

