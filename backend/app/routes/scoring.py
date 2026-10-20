"""
Scoring API endpoints for PRD Section 12 Scoring Engine.

Endpoints:
- POST /api/scoring/evaluate: Evaluates beverage composition, guideline ratios, subscores, benchmarks, confidence, and critical overrides.
- GET /api/scoring/rules: Returns authoritative rules.json configuration including verification statuses and sources.
- GET /api/scoring/benchmarks: Returns category reference ranges and sample counts from reference_ranges.json.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.scoring import (
    ScoringEvaluationRequest,
    ScoringEvaluationResponse,
    UserProfileSchema,
)
from app.engine.scoring_engine import (
    get_scoring_engine,
    UserProfile,
    load_rules,
    load_reference_ranges,
)

router = APIRouter(prefix="/scoring", tags=["Scoring Engine"])


@router.post(
    "/evaluate",
    response_model=ScoringEvaluationResponse,
    summary="Evaluate Beverage with PRD Section 12 Scoring Engine",
)
async def evaluate_beverage(payload: ScoringEvaluationRequest) -> ScoringEvaluationResponse:
    """
    Execute deterministic PRD Section 12 scoring pipeline:
    - Normalizes units and serving volume.
    - Evaluates guideline subscores against exact 5-band piecewise curve.
    - Evaluates composition credits against reference percentiles (sample count >= 100).
    - Applies critical overrides (methanol, acute caffeine) capping Health Impact Score at 40.
    - Scales limits for user profile (under 18, pregnancy, body weight).
    - Calculates confidence level (High >= 80%, Medium >= 60%, Low < 60% with Partial analysis).
    - Keeps Health Impact Score and Composition Score completely separate.
    """
    engine = get_scoring_engine()

    profile_obj = None
    if payload.profile:
        profile_obj = UserProfile(
            age_group=payload.profile.age_group,
            weight_kg=payload.profile.weight_kg,
            is_pregnant_or_breastfeeding=payload.profile.is_pregnant_or_breastfeeding,
            has_diabetes=payload.profile.has_diabetes,
            has_heart_condition=payload.profile.has_heart_condition,
            regulator_region=payload.profile.regulator_region,
            standard_drink_definition_g=payload.profile.standard_drink_definition_g,
        )

    try:
        result = engine.evaluate_beverage(
            beverage_type=payload.beverage_type,
            serving_size_ml=payload.serving_size_ml,
            inputs=payload.inputs,
            profile=profile_obj,
            product_name=payload.product_name,
            wine_color=payload.wine_color,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    return ScoringEvaluationResponse(
        beverage_type=result.beverage_type,
        serving_size_ml=result.serving_size_ml,
        product_name=result.product_name,
        health_impact_score=result.health_impact_score,
        uncapped_health_impact_score=result.uncapped_health_impact_score,
        composition_score=result.composition_score,
        guideline_evaluations=[g.__dict__ for g in result.guideline_evaluations],
        benchmark_evaluations=[b.__dict__ for b in result.benchmark_evaluations],
        alcohol_grams=result.alcohol_grams,
        standard_drinks=result.standard_drinks,
        alcohol_advisory=result.alcohol_advisory,
        critical_override=result.critical_override.__dict__,
        confidence_level=result.confidence_level,
        confidence_percentage=result.confidence_percentage,
        is_partial_analysis=result.is_partial_analysis,
        higher_than_typical=result.higher_than_typical,
        lower_than_typical=result.lower_than_typical,
        missing_fields=result.missing_fields,
        warnings=result.warnings,
        disclaimer=result.disclaimer,
        rules_version=result.rules_version,
        dataset_version=result.dataset_version,
        wine_model=result.wine_model,
    )


@router.get("/rules", summary="Get Configured Guideline and Scoring Rules")
async def get_rules():
    """Returns the full centralized rules.json configuration."""
    return load_rules()


@router.get("/benchmarks", summary="Get Reference Distributions and Sample Counts")
async def get_benchmarks():
    """Returns the full reference_ranges.json configuration."""
    return load_reference_ranges()
