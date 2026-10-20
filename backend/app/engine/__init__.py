"""
Beverage Quality Analysis System (BQAS) - Modular Analysis Engine.
"""

from .normalization import (
    NormalizedBeverageData,
    NormalizationError,
    normalize_beverage_input,
    convert_volume,
    convert_mass_to_grams,
    convert_mass_to_mg,
    convert_energy_to_kcal,
)
from .composition import (
    ETHANOL_DENSITY_G_ML,
    calculate_sugar_per_serving,
    calculate_energy_per_100ml,
    calculate_alcohol_grams,
    calculate_sugar_concentration_per_100ml,
    CompositionScorer,
    ReferenceDatasetMetadata,
)
from .health_impact import (
    HealthImpactEngine,
    HealthRule as HealthImpactRule,
    HealthRuleEvaluation,
)
from .evidence_registry import (
    EvidenceRegistry,
    EvidenceRule,
    EvidenceObservation,
    WHO_ALCOHOL_RULE,
    WHO_SUGAR_RULE,
    EFSA_CAFFEINE_RULE,
)
from .reference_data import (
    ReferenceDataRepository,
    BenchmarkProvenance,
    ValidatedBenchmark,
)
from .composition_scoring import (
    CompositionScoringEngine,
    CompositionScoreResult,
)
from .health_assessment import (
    HealthAssessmentEngine,
    HealthAssessmentResult,
)
from .analysis import (
    BeverageAnalysisService,
    BeverageAnalysisResult,
    AvailableCalculations,
)
from .wine_quality import (
    WineQualityModelService,
    get_wine_quality_service,
    WineModelUnavailableError,
)
from .scoring_engine import (
    BQASScoringEngine,
    get_scoring_engine,
    UserProfile,
    ScoringEngineResult,
    calculate_guideline_ratio,
    calculate_subscore_from_ratio,
    classify_benchmark_percentile,
    calculate_composition_credit,
    calculate_confidence,
)

__all__ = [
    "NormalizedBeverageData",
    "NormalizationError",
    "normalize_beverage_input",
    "convert_volume",
    "convert_mass_to_grams",
    "convert_mass_to_mg",
    "convert_energy_to_kcal",
    "ETHANOL_DENSITY_G_ML",
    "calculate_sugar_per_serving",
    "calculate_energy_per_100ml",
    "calculate_alcohol_grams",
    "calculate_sugar_concentration_per_100ml",
    "CompositionScorer",
    "ReferenceDatasetMetadata",
    "HealthImpactEngine",
    "HealthImpactRule",
    "HealthRuleEvaluation",
    "EvidenceRegistry",
    "EvidenceRule",
    "EvidenceObservation",
    "WHO_ALCOHOL_RULE",
    "WHO_SUGAR_RULE",
    "EFSA_CAFFEINE_RULE",
    "ReferenceDataRepository",
    "BenchmarkProvenance",
    "ValidatedBenchmark",
    "CompositionScoringEngine",
    "CompositionScoreResult",
    "HealthAssessmentEngine",
    "HealthAssessmentResult",
    "BeverageAnalysisService",
    "BeverageAnalysisResult",
    "AvailableCalculations",
    "WineQualityModelService",
    "get_wine_quality_service",
    "WineModelUnavailableError",
    "BQASScoringEngine",
    "get_scoring_engine",
    "UserProfile",
    "ScoringEngineResult",
    "calculate_guideline_ratio",
    "calculate_subscore_from_ratio",
    "classify_benchmark_percentile",
    "calculate_composition_credit",
    "calculate_confidence",
]
