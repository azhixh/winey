"""
Beverage composition calculations and benchmark comparison engine.

Calculations:
1. Sugar per serving (from sugar concentration in g/100 mL and serving size in mL).
2. Energy per 100 mL (from energy in kcal per serving and serving size in mL).
3. Alcohol mass in grams (from serving size in mL, ABV %, and pure ethanol density 0.789 g/mL).
4. Sugar concentration per 100 mL (from sugar per serving in g and serving size in mL).

Scoring Interface:
- Strict protocol requiring >= 100 validated, clean records for the matching beverage type.
- Never invents percentile distributions or arbitrary ranges.
- Returns score=None with an explicit status when reference data is missing, insufficient (<100 records), or unverified.
- Records dataset name, sample size, version, and calculation method.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import numpy as np
import pandas as pd

# Standard ethanol density constant in g/mL at 20°C
ETHANOL_DENSITY_G_ML: float = 0.789


# =====================================================================
# Deterministic Physical / Chemical Calculations
# =====================================================================

def calculate_sugar_per_serving(
    sugar_concentration_g_per_100ml: Optional[float],
    serving_size_ml: Optional[float],
) -> tuple[Optional[float], Optional[str]]:
    """
    Calculate sugar content per serving in grams (g).

    Expected units:
    - sugar_concentration_g_per_100ml: grams of sugar per 100 mL (g/100 mL).
    - serving_size_ml: serving volume in milliliters (mL).

    Formula:
        sugar_per_serving (g) = sugar_concentration_g_per_100ml * (serving_size_ml / 100.0)

    Returns:
        (sugar_g, explanation_or_warning)
    """
    if sugar_concentration_g_per_100ml is None and serving_size_ml is None:
        return None, "Sugar per serving calculation unavailable: sugar concentration and serving size were not provided."
    if sugar_concentration_g_per_100ml is None:
        return None, "Sugar per serving calculation unavailable: sugar concentration (g/100 mL) was not provided."
    if serving_size_ml is None:
        return None, "Sugar per serving calculation unavailable: serving size (mL) was not provided."

    if serving_size_ml <= 0.0:
        raise ValueError("serving_size_ml must be strictly positive.")
    if sugar_concentration_g_per_100ml < 0.0:
        raise ValueError("sugar_concentration_g_per_100ml cannot be negative.")

    sugar_g = sugar_concentration_g_per_100ml * (serving_size_ml / 100.0)
    return round(sugar_g, 4), None


def calculate_energy_per_100ml(
    energy_per_serving_kcal: Optional[float],
    serving_size_ml: Optional[float],
) -> tuple[Optional[float], Optional[str]]:
    """
    Calculate energy density per 100 mL in kilocalories (kcal/100 mL).

    Expected units:
    - energy_per_serving_kcal: energy content per serving in kilocalories (kcal).
    - serving_size_ml: serving volume in milliliters (mL).

    Formula:
        energy_per_100ml (kcal/100 mL) = (energy_per_serving_kcal / serving_size_ml) * 100.0

    Returns:
        (energy_kcal_per_100ml, explanation_or_warning)
    """
    if energy_per_serving_kcal is None and serving_size_ml is None:
        return None, "Energy per 100 mL calculation unavailable: calories and serving size were not provided."
    if energy_per_serving_kcal is None:
        return None, "Energy per 100 mL calculation unavailable: energy per serving (kcal) was not provided."
    if serving_size_ml is None:
        return None, "Energy per 100 mL calculation unavailable: serving size (mL) was not provided."

    if serving_size_ml <= 0.0:
        raise ValueError("serving_size_ml must be strictly positive.")
    if energy_per_serving_kcal < 0.0:
        raise ValueError("energy_per_serving_kcal cannot be negative.")

    energy_density = (energy_per_serving_kcal / serving_size_ml) * 100.0
    return round(energy_density, 4), None


def calculate_alcohol_grams(
    serving_size_ml: Optional[float],
    alcohol_percentage: Optional[float],
    density_g_ml: float = ETHANOL_DENSITY_G_ML,
) -> tuple[Optional[float], Optional[str]]:
    """
    Calculate alcohol mass in grams (g) for a single serving.

    Expected units:
    - serving_size_ml: beverage volume in milliliters (mL).
    - alcohol_percentage: alcohol by volume percentage (% ABV, range 0.0 to 100.0%).
    - density_g_ml: pure ethanol density in g/mL (standard reference: 0.789 g/mL).

    Formula:
        alcohol_grams (g) = serving_size_ml * (alcohol_percentage / 100.0) * density_g_ml

    Returns:
        (alcohol_grams, explanation_or_warning)
    """
    if serving_size_ml is None and alcohol_percentage is None:
        return None, "Alcohol mass calculation unavailable: serving size and alcohol percentage were not provided."
    if serving_size_ml is None:
        return None, "Alcohol mass calculation unavailable: serving size (mL) was not provided."
    if alcohol_percentage is None:
        return None, "Alcohol mass calculation omitted: alcohol percentage was not provided."

    if serving_size_ml <= 0.0:
        raise ValueError("serving_size_ml must be strictly positive.")
    if not (0.0 <= alcohol_percentage <= 100.0):
        raise ValueError("alcohol_percentage must be between 0.0 and 100.0%.")

    grams = serving_size_ml * (alcohol_percentage / 100.0) * density_g_ml
    return round(grams, 2), None


def calculate_sugar_concentration_per_100ml(
    sugar_g_per_serving: Optional[float],
    serving_size_ml: Optional[float],
) -> tuple[Optional[float], Optional[str]]:
    """
    Calculate sugar concentration in grams per 100 mL (g/100 mL).

    Expected units:
    - sugar_g_per_serving: sugar content per serving in grams (g).
    - serving_size_ml: serving volume in milliliters (mL).

    Formula:
        sugar_concentration (g/100 mL) = (sugar_g_per_serving / serving_size_ml) * 100.0

    Returns:
        (sugar_concentration_g_per_100ml, explanation_or_warning)
    """
    if sugar_g_per_serving is None or serving_size_ml is None:
        return None, "Sugar concentration calculation unavailable: missing required inputs."
    if serving_size_ml <= 0.0:
        raise ValueError("serving_size_ml must be strictly positive.")
    if sugar_g_per_serving < 0.0:
        raise ValueError("sugar_g_per_serving cannot be negative.")

    conc = (sugar_g_per_serving / serving_size_ml) * 100.0
    return round(conc, 4), None


# =====================================================================
# Composition Scoring & Dataset Comparison Interface
# =====================================================================

@dataclass
class ReferenceDatasetMetadata:
    """
    Provenance and quality metadata for beverage reference datasets.
    """
    dataset_name: str
    sample_size: int
    data_version: str
    calculation_method: str
    source_url: str = ""
    beverage_type: Optional[str] = None
    verified: bool = False


@dataclass
class CompositionScoreResult:
    """
    Outcome of comparing beverage composition against a reference dataset.
    Maintains score=None whenever benchmark data is unavailable or inadequate.
    """
    score: Optional[float] = None
    percentile: Optional[float] = None
    status: str = "benchmark_unavailable"
    metric_evaluated: Optional[str] = None
    dataset_metadata: Optional[ReferenceDatasetMetadata] = None
    explanation: str = ""


class CompositionScorer:
    """
    Scorer interface for comparing beverage composition with validated reference datasets.

    Strict scientific constraints:
    - Requires at least 100 valid, non-null records for the specific beverage type.
    - Does not invent percentile distributions, gaussian assumptions, or arbitrary ranges.
    - Returns score=None whenever reference data is missing or has < 100 valid samples.
    - Stores dataset name, sample size, version, and calculation method with any result.
    - Keeps composition comparisons completely separate from health-risk assessments.
    """
    MIN_REQUIRED_RECORDS: int = 100

    def __init__(
        self,
        reference_data: Optional[pd.DataFrame] = None,
        metadata: Optional[ReferenceDatasetMetadata] = None,
    ):
        self.reference_data = reference_data
        self.metadata = metadata

    def compare_metric(
        self,
        beverage_type: str,
        metric_name: str,
        metric_value: Optional[float],
    ) -> CompositionScoreResult:
        """
        Compare a single metric against the reference dataset using empirical percentiles.

        Args:
            beverage_type: The beverage category (e.g., 'Beer', 'Soft drink').
            metric_name: Name of column/metric in reference dataset (e.g. 'sugar_g_per_100ml').
            metric_value: The beverage's value for this metric.
        """
        # Guard: No metric value provided
        if metric_value is None:
            return CompositionScoreResult(
                score=None,
                percentile=None,
                status="metric_missing",
                metric_evaluated=metric_name,
                dataset_metadata=self.metadata,
                explanation=f"Cannot perform composition comparison: input metric '{metric_name}' is null.",
            )

        # Guard: No reference dataset configured
        if self.reference_data is None or self.reference_data.empty:
            return CompositionScoreResult(
                score=None,
                percentile=None,
                status="benchmark_unavailable",
                metric_evaluated=metric_name,
                dataset_metadata=None,
                explanation=(
                    "No validated reference dataset is currently integrated. "
                    "Numeric composition score is withheld to avoid ungrounded or fabricated rankings."
                ),
            )

        # Guard: Metadata verification
        if self.metadata is None or not self.metadata.verified:
            return CompositionScoreResult(
                score=None,
                percentile=None,
                status="benchmark_unverified",
                metric_evaluated=metric_name,
                dataset_metadata=self.metadata,
                explanation="Reference dataset is present but has not been verified for scientific validity.",
            )

        # Filter by beverage type if column exists
        df = self.reference_data
        if "beverage_type" in df.columns:
            matched_df = df[df["beverage_type"].astype(str).str.lower() == beverage_type.strip().lower()]
        else:
            matched_df = df

        # Check metric column presence
        if metric_name not in matched_df.columns:
            return CompositionScoreResult(
                score=None,
                percentile=None,
                status="metric_not_in_dataset",
                metric_evaluated=metric_name,
                dataset_metadata=self.metadata,
                explanation=f"Metric '{metric_name}' is not present in reference dataset '{self.metadata.dataset_name}'.",
            )

        # Extract clean, non-null, finite numeric records
        clean_series = matched_df[metric_name].dropna()
        clean_series = clean_series[np.isfinite(clean_series)]
        valid_count = len(clean_series)

        # Guard: Minimum 100 valid records constraint
        if valid_count < self.MIN_REQUIRED_RECORDS:
            return CompositionScoreResult(
                score=None,
                percentile=None,
                status="insufficient_sample_size",
                metric_evaluated=metric_name,
                dataset_metadata=ReferenceDatasetMetadata(
                    dataset_name=self.metadata.dataset_name,
                    sample_size=valid_count,
                    data_version=self.metadata.data_version,
                    calculation_method=self.metadata.calculation_method,
                    source_url=self.metadata.source_url,
                    beverage_type=beverage_type,
                    verified=self.metadata.verified,
                ),
                explanation=(
                    f"Reference dataset contains only {valid_count} valid records for '{beverage_type}' "
                    f"(minimum {self.MIN_REQUIRED_RECORDS} required). "
                    "Percentile-based composition comparison is disabled."
                ),
            )

        # Empirical percentile calculation: (number of values <= metric_value) / total * 100
        empirical_percentile = float((clean_series <= metric_value).mean() * 100.0)
        score = round(empirical_percentile, 2)

        return CompositionScoreResult(
            score=score,
            percentile=score,
            status="computed",
            metric_evaluated=metric_name,
            dataset_metadata=ReferenceDatasetMetadata(
                dataset_name=self.metadata.dataset_name,
                sample_size=valid_count,
                data_version=self.metadata.data_version,
                calculation_method=self.metadata.calculation_method,
                source_url=self.metadata.source_url,
                beverage_type=beverage_type,
                verified=self.metadata.verified,
            ),
            explanation=(
                f"Compared against {valid_count} verified records in '{self.metadata.dataset_name}' (v{self.metadata.data_version}). "
                f"Empirical percentile: {score}%."
            ),
        )
