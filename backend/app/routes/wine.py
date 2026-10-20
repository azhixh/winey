"""
Wine quality machine learning prediction API routes.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.wine import (
    WinePredictionRequest,
    WinePredictionResponse,
)
from app.engine.wine_quality import (
    get_wine_quality_service,
    WineModelUnavailableError,
)

router = APIRouter(prefix="/wine", tags=["Wine Quality Model"])


@router.post(
    "/predict",
    response_model=WinePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Estimate wine sensory quality using trained regression models",
    description=(
        "Estimates the sensory quality rating of red or white wine based on 11 physicochemical laboratory metrics. "
        "Strictly validated against UCI Wine Quality schema. "
        "This estimate is non-clinical, does NOT predict health effects or safety, and is specific to Portuguese Vinho Verde wines."
    ),
)
async def predict_wine_quality(payload: WinePredictionRequest) -> WinePredictionResponse:
    """
    Predict sensory wine quality rating based on 11 physicochemical metrics.
    """
    service = get_wine_quality_service()

    features = {
        "fixed_acidity": payload.fixed_acidity,
        "volatile_acidity": payload.volatile_acidity,
        "citric_acid": payload.citric_acid,
        "residual_sugar": payload.residual_sugar,
        "chlorides": payload.chlorides,
        "free_sulfur_dioxide": payload.free_sulfur_dioxide,
        "total_sulfur_dioxide": payload.total_sulfur_dioxide,
        "density": payload.density,
        "pH": payload.pH,
        "sulphates": payload.sulphates,
        "alcohol": payload.alcohol,
    }

    try:
        result = service.predict(payload.wine_type, features)
        return WinePredictionResponse(**result)
    except WineModelUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Wine quality prediction model unavailable: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/model-card",
    summary="Retrieve wine quality model card and evaluation metrics",
    description="Returns the full provenance, train/test split strategy, test metrics, and limitations for the wine models.",
)
async def get_wine_model_card() -> dict:
    """
    Return full model card metadata.
    """
    service = get_wine_quality_service()
    try:
        return service.get_model_card()
    except WineModelUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model card unavailable: {str(e)}",
        )
