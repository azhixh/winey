"""
Beverage analysis and classification endpoints for BQAS backend.
"""

from typing import Optional
from fastapi import APIRouter
from app.schemas import (
    BeverageType,
    BeverageTypesResponse,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisInputData,
    CalculationsResult,
    CompositionComparisonResponse,
    HealthAssessmentResponse,
)
from app.engine.analysis import BeverageAnalysisService

router = APIRouter(tags=["Beverages"])

# Shared engine service instance
analysis_service = BeverageAnalysisService()


@router.get("/beverage-types", response_model=BeverageTypesResponse, summary="List Beverage Categories")
async def get_beverage_types() -> BeverageTypesResponse:
    """
    Returns the supported beverage categories for BQAS.
    Supported types:
    - Soft drink
    - Beer
    - Wine
    - Spirits
    - Energy drink
    """
    categories = [beverage.value for beverage in BeverageType]
    return BeverageTypesResponse(
        beverage_types=categories,
        total=len(categories),
    )


@router.post("/analyze", response_model=AnalysisResponse, summary="Analyze Beverage Composition")
async def analyze_beverage(payload: AnalysisRequest) -> AnalysisResponse:
    """
    Perform transparent, evidence-based beverage analysis and composition comparison.

    Executes through BeverageAnalysisService:
    - Normalizes supported units into standard internal metrics.
    - Validates boundary conditions and preserves missing values as null (never zero).
    - Calculates alcohol mass using pure ethanol density (0.789 g/mL), sugar per serving, and energy per 100 mL.
    - Evaluates non-alcoholic composition against verified reference benchmarks (requiring >= 100 records).
    - Evaluates evidence rules from EvidenceRegistry (reporting cited observations).
    - Returns structured statuses ('available', 'insufficient_data', 'not_evaluated').
    - Keeps health_impact_score strictly null to prevent unverified medical assertions.
    """
    # Execute modular analysis pipeline
    result = analysis_service.analyze(
        beverage_type=payload.beverage_type,
        serving_size=payload.serving_size_ml,
        serving_size_unit=payload.serving_size_unit,
        sugar=payload.sugar_g,
        sugar_unit=payload.sugar_unit,
        sugar_concentration_g_per_100ml=payload.sugar_concentration_g_per_100ml,
        calories=payload.calories,
        calories_unit=payload.calories_unit,
        sodium=payload.sodium_mg,
        sodium_unit=payload.sodium_unit,
        caffeine=payload.caffeine_mg,
        caffeine_unit=payload.caffeine_unit,
        alcohol_percentage=payload.alcohol_percentage,
        alcohol_unit=payload.alcohol_unit,
    )

    norm_in = result.normalized_input
    input_data = AnalysisInputData(
        beverage_type=norm_in.beverage_type,
        serving_size_ml=norm_in.serving_size_ml,
        sugar_g=norm_in.sugar_g,
        sugar_concentration_g_per_100ml=norm_in.sugar_concentration_g_per_100ml,
        calories=norm_in.calories,
        sodium_mg=norm_in.sodium_mg,
        caffeine_mg=norm_in.caffeine_mg,
        alcohol_percentage=norm_in.alcohol_percentage,
        conversions_applied=norm_in.conversions_applied,
    )

    calc = result.calculations
    calculations_dto = CalculationsResult(
        alcohol_grams=calc.alcohol_grams,
        alcohol_grams_unit=calc.alcohol_grams_unit,
        ethanol_density_used_g_ml=calc.ethanol_density_used_g_ml,
        sugar_per_serving_g=calc.sugar_per_serving_g,
        sugar_per_serving_unit=calc.sugar_per_serving_unit,
        energy_per_100ml_kcal=calc.energy_per_100ml_kcal,
        energy_per_100ml_unit=calc.energy_per_100ml_unit,
        sugar_concentration_g_per_100ml=calc.sugar_concentration_g_per_100ml,
        sugar_concentration_unit=calc.sugar_concentration_unit,
        explanations=calc.explanations,
    )

    comp_comp = result.composition_comparison
    metadata_dict = {
        "dataset_name": comp_comp.benchmark_name,
        "dataset_version": comp_comp.dataset_version,
        "sample_size": comp_comp.sample_size,
        "calculation_method": comp_comp.calculation_method,
    } if comp_comp.benchmark_name else None

    comp_comparison_dto = CompositionComparisonResponse(
        status=comp_comp.status,
        score=comp_comp.score,
        percentile=comp_comp.percentile,
        metric_evaluated=comp_comp.metric_evaluated,
        benchmark_name=comp_comp.benchmark_name,
        dataset_version=comp_comp.dataset_version,
        sample_size=comp_comp.sample_size,
        calculation_method=comp_comp.calculation_method,
        limitations=comp_comp.limitations,
        dataset_metadata=metadata_dict,
        explanation=comp_comp.explanation,
    )

    health_dto = HealthAssessmentResponse(
        status=result.health_assessment.status,
        health_impact_score=result.health_assessment.health_impact_score,
        observations=result.health_assessment.observations,
        advisories=result.health_assessment.advisories,
        missing_data_notices=result.health_assessment.missing_data_notices,
        warnings=result.health_assessment.warnings,
        sources=result.health_assessment.sources,
        limitations=result.health_assessment.limitations,
    )

    return AnalysisResponse(
        status="success",
        input_data=input_data,
        calculations=calculations_dto,
        composition_score=comp_comp.score,
        health_impact_score=result.health_assessment.health_impact_score,
        composition_comparison=comp_comparison_dto,
        health_assessment=health_dto,
        warnings=result.warnings,
        sources=result.sources,
    )
