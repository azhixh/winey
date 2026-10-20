"""
Composition scoring engine for non-alcoholic beverages.

Scientific principles:
- Scoped strictly to non-alcoholic beverages (Soft drink, Energy drink).
- Compares nutrient metrics against validated reference datasets.
- Mandates at least 100 valid, deduplicated records before calculating an empirical percentile.
- Returns score as None whenever benchmark is unavailable, unverified, or has < 100 records.
- Status values: 'available', 'insufficient_data', 'not_evaluated'.
- Never invents scores, weights, or synthetic distributions.
"""

from dataclasses import dataclass, field
from typing import Optional
from app.engine.normalization import NormalizedBeverageData
from app.engine.reference_data import (
    ReferenceDataRepository,
    ValidatedBenchmark,
)


@dataclass
class CompositionScoreResult:
    """
    Result of comparing a beverage nutrient against a validated reference dataset.
    Score remains null unless backed by >= 100 verified records.
    """
    status: str                         # 'available', 'insufficient_data', 'not_evaluated'
    score: Optional[float] = None       # Empirical percentile (0.0 - 100.0) or None
    percentile: Optional[float] = None  # Alias matching score
    metric_evaluated: Optional[str] = None
    benchmark_name: Optional[str] = None
    dataset_version: Optional[str] = None
    sample_size: Optional[int] = None
    calculation_method: Optional[str] = None
    limitations: list[str] = field(default_factory=list)
    explanation: str = ""


class CompositionScoringEngine:
    """
    Engine for evaluating non-alcoholic beverage composition against authenticated benchmarks.
    """

    def __init__(self, repository: Optional[ReferenceDataRepository] = None):
        self.repository = repository or ReferenceDataRepository()

    def evaluate(
        self,
        beverage: NormalizedBeverageData,
        metric_name: str = "sugar_concentration_g_per_100ml",
    ) -> CompositionScoreResult:
        """
        Evaluate beverage composition against the appropriate reference dataset.
        """
        bev_type = beverage.beverage_type.value

        # 1. Non-alcoholic scope check
        if bev_type in ["Beer", "Wine", "Spirits"]:
            return CompositionScoreResult(
                status="not_evaluated",
                score=None,
                percentile=None,
                metric_evaluated=metric_name,
                explanation="Composition scoring is not evaluated for alcoholic beverages (scoped strictly to non-alcoholic categories).",
                limitations=["Alcoholic beverage ranking and composition scoring are intentionally excluded."],
            )

        # 2. Extract requested metric value from normalized beverage
        if metric_name == "sugar_concentration_g_per_100ml":
            val = beverage.sugar_concentration_g_per_100ml
            # If concentration not explicitly given, check if derivable from sugar_g and serving_size_ml
            if val is None and beverage.sugar_g is not None and beverage.serving_size_ml > 0:
                val = round((beverage.sugar_g / beverage.serving_size_ml) * 100.0, 4)
        else:
            val = getattr(beverage, metric_name, None)

        # If metric is missing in the beverage input
        if val is None:
            return CompositionScoreResult(
                status="insufficient_data",
                score=None,
                percentile=None,
                metric_evaluated=metric_name,
                explanation=f"Cannot compute composition score: input metric '{metric_name}' was not provided (preserved as null).",
                limitations=["Missing nutrient values prevent benchmark percentile ranking."],
            )

        # 3. Retrieve benchmark from repository
        benchmark: Optional[ValidatedBenchmark] = self.repository.get_benchmark(bev_type, metric_name)

        # Guard: No benchmark registered
        if benchmark is None:
            return CompositionScoreResult(
                status="insufficient_data",
                score=None,
                percentile=None,
                metric_evaluated=metric_name,
                explanation=f"No validated benchmark dataset is available for '{bev_type}' on metric '{metric_name}'.",
                limitations=["Benchmark dataset has not been compiled or registered for this category and metric."],
            )

        # Guard: Insufficient sample size (< 100 records)
        if not benchmark.is_sufficient:
            limitations = list(benchmark.provenance.limitations)
            return CompositionScoreResult(
                status="insufficient_data",
                score=None,
                percentile=None,
                metric_evaluated=metric_name,
                benchmark_name=benchmark.provenance.dataset_name,
                dataset_version=benchmark.provenance.dataset_version,
                sample_size=benchmark.sample_size,
                calculation_method="empirical_percentile",
                limitations=limitations,
                explanation=(
                    f"Reference dataset '{benchmark.provenance.dataset_name}' contains {benchmark.sample_size} valid records "
                    f"(minimum {self.repository.MIN_REQUIRED_RECORDS} required). Percentile ranking is disabled."
                ),
            )

        # 4. Compute empirical percentile rank
        # Formula: (count of benchmark values <= beverage value) / total sample size * 100
        clean_vals = benchmark.values
        empirical_percentile = float(sum(1 for x in clean_vals if x <= val) / len(clean_vals) * 100.0)
        rounded_score = round(empirical_percentile, 2)

        limitations = list(benchmark.provenance.limitations)
        limitations.append(
            f"Percentile calculation uses empirical ranking across {benchmark.sample_size} laboratory-verified records. "
            "No theoretical distribution (e.g. Gaussian) was assumed."
        )

        return CompositionScoreResult(
            status="available",
            score=rounded_score,
            percentile=rounded_score,
            metric_evaluated=metric_name,
            benchmark_name=benchmark.provenance.dataset_name,
            dataset_version=benchmark.provenance.dataset_version,
            sample_size=benchmark.sample_size,
            calculation_method="empirical_percentile",
            limitations=limitations,
            explanation=(
                f"Beverage {metric_name} ({val} {benchmark.metric_unit}) is at the {rounded_score}th percentile "
                f"of {benchmark.sample_size} validated records in '{benchmark.provenance.dataset_name}' (v{benchmark.provenance.dataset_version})."
            ),
        )
