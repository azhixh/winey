"""
Unit tests for app.engine.composition module:
- Deterministic calculation functions (sugar per serving, energy per 100 mL, alcohol grams)
- Missing-input handling and explanatory messages
- Composition scoring interface:
  - Benchmark unavailable -> score=None
  - Dataset with < 100 records -> score=None, insufficient_sample_size
  - Dataset with >= 100 valid records -> valid empirical percentile calculation
  - Metadata tracking (name, sample size, version, method)
"""

import pytest
import pandas as pd
import numpy as np
from app.engine.composition import (
    ETHANOL_DENSITY_G_ML,
    calculate_sugar_per_serving,
    calculate_energy_per_100ml,
    calculate_alcohol_grams,
    calculate_sugar_concentration_per_100ml,
    CompositionScorer,
    ReferenceDatasetMetadata,
)


# =====================================================================
# Physical / Chemical Calculation Tests
# =====================================================================

def test_calculate_sugar_per_serving_valid():
    """
    10 g/100 mL in a 330 mL can = 33.0 g sugar.
    """
    sugar_g, explanation = calculate_sugar_per_serving(10.0, 330.0)
    assert sugar_g == 33.0
    assert explanation is None


def test_calculate_sugar_per_serving_missing():
    sugar_g, explanation = calculate_sugar_per_serving(None, 330.0)
    assert sugar_g is None
    assert "sugar concentration" in explanation.lower()

    sugar_g, explanation = calculate_sugar_per_serving(10.0, None)
    assert sugar_g is None
    assert "serving size" in explanation.lower()


def test_calculate_energy_per_100ml_valid():
    """
    140 kcal in 350 mL = 40.0 kcal per 100 mL.
    """
    energy_100ml, explanation = calculate_energy_per_100ml(140.0, 350.0)
    assert energy_100ml == 40.0
    assert explanation is None


def test_calculate_energy_per_100ml_missing():
    energy_100ml, explanation = calculate_energy_per_100ml(None, 350.0)
    assert energy_100ml is None
    assert "energy per serving" in explanation.lower()


def test_calculate_alcohol_grams_valid():
    """
    500 mL at 5.0% ABV using 0.789 g/mL:
    500 * 0.05 * 0.789 = 25 * 0.789 = 19.725 -> 19.73 g
    """
    grams, explanation = calculate_alcohol_grams(500.0, 5.0, ETHANOL_DENSITY_G_ML)
    assert grams == 19.73
    assert explanation is None


def test_calculate_alcohol_grams_missing():
    grams, explanation = calculate_alcohol_grams(500.0, None)
    assert grams is None
    assert "alcohol percentage was not provided" in explanation.lower()


def test_calculate_sugar_concentration_per_100ml_valid():
    """
    25 g sugar in 250 mL = 10.0 g/100 mL.
    """
    conc, explanation = calculate_sugar_concentration_per_100ml(25.0, 250.0)
    assert conc == 10.0
    assert explanation is None


def test_calculations_reject_invalid_inputs():
    with pytest.raises(ValueError, match="strictly positive"):
        calculate_sugar_per_serving(10.0, 0.0)

    with pytest.raises(ValueError, match="strictly positive"):
        calculate_energy_per_100ml(100.0, -10.0)

    with pytest.raises(ValueError, match="between 0.0 and 100.0%"):
        calculate_alcohol_grams(500.0, 110.0)


# =====================================================================
# Composition Scoring & Benchmark Interface Tests
# =====================================================================

def test_scorer_without_dataset_returns_none_score():
    """
    Crucial scientific safeguard:
    When no benchmark data is available, NEVER invent a score or percentile.
    """
    scorer = CompositionScorer()
    res = scorer.compare_metric("Beer", "sugar_g_per_100ml", 3.5)

    assert res.score is None
    assert res.percentile is None
    assert res.status == "benchmark_unavailable"
    assert "withheld" in res.explanation.lower()


def test_scorer_with_insufficient_sample_size_returns_none():
    """
    Rule: Dataset with fewer than 100 records must refuse percentile comparison.
    """
    # Create dataset with only 50 records
    df = pd.DataFrame({
        "beverage_type": ["Beer"] * 50,
        "sugar_g_per_100ml": np.linspace(1.0, 5.0, 50),
    })
    meta = ReferenceDatasetMetadata(
        dataset_name="Small Pilot Dataset",
        sample_size=50,
        data_version="0.1",
        calculation_method="empirical_percentile",
        verified=True,
    )
    scorer = CompositionScorer(reference_data=df, metadata=meta)
    res = scorer.compare_metric("Beer", "sugar_g_per_100ml", 3.0)

    assert res.score is None
    assert res.percentile is None
    assert res.status == "insufficient_sample_size"
    assert "minimum 100 required" in res.explanation.lower()
    assert res.dataset_metadata.sample_size == 50


def test_scorer_with_valid_dataset_computes_empirical_percentile():
    """
    Dataset with >= 100 records (e.g. 200 records) computes empirical percentile accurately.
    """
    # 200 records of sugar from 0.0 to 10.0 g/100 mL
    values = np.linspace(0.0, 10.0, 200)
    df = pd.DataFrame({
        "beverage_type": ["Soft drink"] * 200,
        "sugar_g_per_100ml": values,
    })
    meta = ReferenceDatasetMetadata(
        dataset_name="Verified Soft Drink Benchmark",
        sample_size=200,
        data_version="1.0",
        calculation_method="empirical_percentile",
        source_url="https://example.gov/beverages",
        verified=True,
    )
    scorer = CompositionScorer(reference_data=df, metadata=meta)

    # Value 5.0 is the exact median (50th percentile)
    res = scorer.compare_metric("Soft drink", "sugar_g_per_100ml", 5.0)

    assert res.score is not None
    assert res.percentile is not None
    assert pytest.approx(res.score, 1.0) == 50.0
    assert res.status == "computed"
    assert res.dataset_metadata.dataset_name == "Verified Soft Drink Benchmark"
    assert res.dataset_metadata.sample_size == 200
    assert res.dataset_metadata.data_version == "1.0"
    assert res.dataset_metadata.calculation_method == "empirical_percentile"


def test_scorer_with_unverified_dataset_refuses_score():
    """
    Unverified datasets cannot be used to generate scores.
    """
    df = pd.DataFrame({
        "beverage_type": ["Beer"] * 150,
        "sugar_g_per_100ml": np.linspace(1.0, 5.0, 150),
    })
    meta = ReferenceDatasetMetadata(
        dataset_name="Unverified Scraped Data",
        sample_size=150,
        data_version="0.1",
        calculation_method="empirical_percentile",
        verified=False,  # Unverified!
    )
    scorer = CompositionScorer(reference_data=df, metadata=meta)
    res = scorer.compare_metric("Beer", "sugar_g_per_100ml", 3.0)

    assert res.score is None
    assert res.status == "benchmark_unverified"
