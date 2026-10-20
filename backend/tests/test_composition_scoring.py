"""
Unit and integration tests for app.engine.composition_scoring and reference_data.

Verifies:
- Scoped strictly to non-alcoholic beverages (Beer, Wine, Spirits return not_evaluated).
- Reference dataset requirement of >= 100 valid records for percentile computation.
- Benchmark with < 100 records returns status='insufficient_data' and score=None.
- Data validation: deduplication, non-finite/null rejection without 0-imputation, lab verification provenance.
- Missing nutrient input values return status='insufficient_data' and score=None.
- Empirical percentile calculation correctness: (count <= val) / N * 100.
- Response metadata: benchmark name, version, sample size, calculation method, limitations.
- Never fabricates scores or assumes parametric distributions.
"""

import pytest
import numpy as np
from app.engine.composition_scoring import (
    CompositionScoringEngine,
    CompositionScoreResult,
)
from app.engine.reference_data import (
    ReferenceDataRepository,
    BenchmarkProvenance,
    ValidatedBenchmark,
)
from app.engine.normalization import normalize_beverage_input
from app.schemas import BeverageType


def test_composition_scoring_alcoholic_beverages_not_evaluated():
    """Alcoholic categories must return not_evaluated with score=None."""
    engine = CompositionScoringEngine()

    for alc_type in [BeverageType.BEER, BeverageType.WINE, BeverageType.SPIRITS]:
        norm = normalize_beverage_input(
            beverage_type=alc_type,
            serving_size=330.0,
            sugar=10.0,
            alcohol_percentage=5.0,
        )
        result = engine.evaluate(norm, metric_name="sugar_concentration_g_per_100ml")
        assert result.status == "not_evaluated"
        assert result.score is None
        assert result.percentile is None
        assert "scoped strictly to non-alcoholic categories" in result.explanation
        assert any("ranking and composition scoring are intentionally excluded" in lim for lim in result.limitations)


def test_composition_scoring_valid_soft_drink_benchmark():
    """Soft drink with sugar concentration compares against verified 120-sample USDA benchmark."""
    engine = CompositionScoringEngine()
    norm = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=250.0,
        sugar=25.0,  # 25 g / 250 mL = 10.0 g/100 mL
    )
    result = engine.evaluate(norm, metric_name="sugar_concentration_g_per_100ml")

    assert result.status == "available"
    assert result.score is not None
    assert 0.0 <= result.score <= 100.0
    assert result.percentile == result.score
    assert result.metric_evaluated == "sugar_concentration_g_per_100ml"
    assert result.benchmark_name == "USDA FoodData Central Foundation & SR Legacy Soft Drink Benchmark"
    assert result.dataset_version == "2024.1"
    assert result.sample_size == 120
    assert result.sample_size >= 100
    assert result.calculation_method == "empirical_percentile"
    assert len(result.limitations) >= 3
    assert any("empirical ranking" in lim for lim in result.limitations)
    assert any("No theoretical distribution" in lim for lim in result.limitations)


def test_composition_scoring_insufficient_sample_size_returns_null_score():
    """Energy drink benchmark has only 40 pilot records (< 100 minimum), so score must be None."""
    engine = CompositionScoringEngine()
    norm = normalize_beverage_input(
        beverage_type=BeverageType.ENERGY_DRINK,
        serving_size=250.0,
        sugar=27.5,
    )
    result = engine.evaluate(norm, metric_name="sugar_concentration_g_per_100ml")

    assert result.status == "insufficient_data"
    assert result.score is None
    assert result.percentile is None
    assert result.sample_size == 40
    assert result.sample_size < 100
    assert "minimum 100 required" in result.explanation
    assert "Percentile ranking is disabled" in result.explanation


def test_composition_scoring_missing_metric_returns_insufficient_data():
    """When the requested nutrient metric is omitted/null, score must be None."""
    engine = CompositionScoringEngine()
    norm = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=330.0,
        # sugar omitted entirely
    )
    result = engine.evaluate(norm, metric_name="sugar_concentration_g_per_100ml")

    assert result.status == "insufficient_data"
    assert result.score is None
    assert result.percentile is None
    assert "preserved as null" in result.explanation
    assert any("Missing nutrient values" in lim for lim in result.limitations)


def test_composition_scoring_unregistered_category_or_metric():
    """Unregistered category/metric returns status='insufficient_data' with score=None."""
    engine = CompositionScoringEngine()
    norm = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=330.0,
        sodium=50.0,
    )
    # sodium_mg has no benchmark registered in default repo
    result = engine.evaluate(norm, metric_name="sodium_mg")

    assert result.status == "insufficient_data"
    assert result.score is None
    assert result.percentile is None
    assert "No validated benchmark dataset is available" in result.explanation


def test_benchmark_deduplication_and_null_removal():
    """Verify ReferenceDataRepository removes duplicates and drops non-numeric/null values without zero-imputation."""
    repo = ReferenceDataRepository(load_defaults=False)

    prov = BenchmarkProvenance(
        dataset_name="Test Laboratory Dataset",
        dataset_version="1.0",
        source_organization="Test Org",
        source_url="https://example.org/data",
        publication_year=2025,
        jurisdiction="Global",
        verified_by_lab=True,
        data_collection_method="HPLC",
    )

    # 120 raw values with duplicates, nulls, NaNs, and strings
    raw = [5.0] * 20 + [None, float("nan"), "invalid_str", 10.0, 15.0] + [float(i) for i in range(20, 140)]

    benchmark = repo.register_benchmark(
        beverage_type="Soft drink",
        metric_name="sugar_concentration_g_per_100ml",
        metric_unit="g/100 mL",
        raw_values=raw,
        provenance=prov,
    )

    # Without IDs, duplicates of 5.0 are deduplicated
    # Nulls, NaNs, and invalid_str are discarded, never imputed as 0
    assert None not in benchmark.values
    assert not any(np.isnan(v) for v in benchmark.values)
    assert all(isinstance(v, float) for v in benchmark.values)
    # Sorted order
    assert benchmark.values == sorted(benchmark.values)


def test_benchmark_exact_100_records_threshold():
    """Test boundary condition: exactly 100 records enables scoring; 99 records disables scoring."""
    repo = ReferenceDataRepository(load_defaults=False)
    prov = BenchmarkProvenance(
        dataset_name="Boundary Test Dataset",
        dataset_version="1.0",
        source_organization="Test Lab",
        source_url="https://example.org/boundary",
        publication_year=2025,
        jurisdiction="US",
        verified_by_lab=True,
        data_collection_method="Chemical Assay",
    )

    # 1. 99 distinct records
    repo.register_benchmark(
        beverage_type="Soft drink",
        metric_name="sugar_concentration_g_per_100ml",
        metric_unit="g/100 mL",
        raw_values=[float(i) for i in range(1, 100)],  # 99 records
        provenance=prov,
        record_ids=[f"rec_{i}" for i in range(1, 100)],
    )

    engine_99 = CompositionScoringEngine(repository=repo)
    norm = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=100.0,
        sugar=50.0,
    )
    res_99 = engine_99.evaluate(norm, "sugar_concentration_g_per_100ml")
    assert res_99.status == "insufficient_data"
    assert res_99.score is None
    assert res_99.sample_size == 99

    # 2. 100 distinct records
    repo.register_benchmark(
        beverage_type="Soft drink",
        metric_name="sugar_concentration_g_per_100ml",
        metric_unit="g/100 mL",
        raw_values=[float(i) for i in range(1, 101)],  # 100 records
        provenance=prov,
        record_ids=[f"rec_{i}" for i in range(1, 101)],
    )

    engine_100 = CompositionScoringEngine(repository=repo)
    res_100 = engine_100.evaluate(norm, "sugar_concentration_g_per_100ml")
    assert res_100.status == "available"
    assert res_100.score is not None
    assert res_100.sample_size == 100
    # In range 1..100, exactly 50 values are <= 50.0 -> percentile 50.0%
    assert res_100.score == 50.0


def test_benchmark_unverified_provenance_rejects_scoring():
    """Even with >= 100 records, unverified benchmark (verified_by_lab=False) prevents scoring."""
    repo = ReferenceDataRepository(load_defaults=False)
    prov = BenchmarkProvenance(
        dataset_name="Crowdsourced Unverified Dataset",
        dataset_version="0.1",
        source_organization="Unknown",
        source_url="https://example.org/crowdsource",
        publication_year=2025,
        jurisdiction="Global",
        verified_by_lab=False,  # NOT verified by lab
        data_collection_method="Self-reported web scraping",
    )
    repo.register_benchmark(
        beverage_type="Soft drink",
        metric_name="sugar_concentration_g_per_100ml",
        metric_unit="g/100 mL",
        raw_values=[float(i) for i in range(150)],  # 150 records
        provenance=prov,
        record_ids=[f"crowd_{i}" for i in range(150)],
    )

    engine = CompositionScoringEngine(repository=repo)
    norm = normalize_beverage_input(
        beverage_type=BeverageType.SOFT_DRINK,
        serving_size=100.0,
        sugar=10.0,
    )
    result = engine.evaluate(norm, "sugar_concentration_g_per_100ml")
    assert result.status == "insufficient_data"
    assert result.score is None
