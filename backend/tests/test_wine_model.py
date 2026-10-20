"""
Automated tests for Wine Quality Machine Learning Model (Step 5).

Verifies:
- Asset existence and model card integrity (non-fabricated metrics).
- Red and white model inference pipelines.
- Model unavailability error handling and 503 response.
- Strict input validation on POST /api/wine/predict:
  - Missing features are rejected (never replaced with zero).
  - Non-finite (NaN, inf) values are rejected.
  - Out-of-bounds physical values are rejected.
  - free_sulfur_dioxide > total_sulfur_dioxide cross-validation rejection.
  - Case-insensitive wine type handling.
  - Invalid wine types rejected.
- Output requirements:
  - Estimated quality score (0-10) and rounded integer rating.
  - Evaluation metrics (MAE, RMSE, R2) from held-out test data.
  - Model card reference with UCI provenance and citation.
  - Explicit disclaimer that estimate is not a health score or lab result.
  - Clear statement regarding Portuguese Vinho Verde regional applicability.
- Total separation from composition score and health impact assessment.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.engine.wine_quality import (
    WineQualityModelService,
    WineModelUnavailableError,
    DEFAULT_MODEL_DIR,
    FEATURE_NAMES,
)

client = TestClient(app)

VALID_RED_WINE_PAYLOAD = {
    "wine_type": "red",
    "fixed_acidity": 7.4,
    "volatile_acidity": 0.70,
    "citric_acid": 0.0,
    "residual_sugar": 1.9,
    "chlorides": 0.076,
    "free_sulfur_dioxide": 11.0,
    "total_sulfur_dioxide": 34.0,
    "density": 0.9978,
    "pH": 3.51,
    "sulphates": 0.56,
    "alcohol": 9.4,
}

VALID_WHITE_WINE_PAYLOAD = {
    "wine_type": "white",
    "fixed_acidity": 7.0,
    "volatile_acidity": 0.27,
    "citric_acid": 0.36,
    "residual_sugar": 20.7,
    "chlorides": 0.045,
    "free_sulfur_dioxide": 45.0,
    "total_sulfur_dioxide": 170.0,
    "density": 1.0010,
    "pH": 3.00,
    "sulphates": 0.45,
    "alcohol": 8.8,
}


def test_wine_model_assets_exist_and_unfabricated():
    """Verify saved models and model card exist with valid metadata."""
    red_path = DEFAULT_MODEL_DIR / "wine_model_red.joblib"
    white_path = DEFAULT_MODEL_DIR / "wine_model_white.joblib"
    card_path = DEFAULT_MODEL_DIR / "model_card.json"

    assert red_path.exists(), "Red wine model file must exist."
    assert white_path.exists(), "White wine model file must exist."
    assert card_path.exists(), "Model card JSON must exist."

    service = WineQualityModelService()
    card = service.get_model_card()

    assert card["model_name"] == "BQAS Wine Quality Sensory Predictor"
    assert "archive.ics.uci.edu" in card["dataset_metadata"]["dataset_url"]
    assert "Cortez" in card["dataset_metadata"]["citation"]
    assert "Vinho Verde" in card["dataset_metadata"]["geographic_origin"]

    # Verify actual test metrics were computed (not fabricated placeholders)
    red_metrics = card["evaluation_summary"]["red_wine"]["selected_test_metrics"]
    white_metrics = card["evaluation_summary"]["white_wine"]["selected_test_metrics"]

    assert red_metrics["mae"] > 0.0
    assert red_metrics["rmse"] > 0.0
    assert red_metrics["r2_score"] > 0.4  # Random Forest on red wine achieved ~0.54

    assert white_metrics["mae"] > 0.0
    assert white_metrics["rmse"] > 0.0
    assert white_metrics["r2_score"] > 0.4  # Random Forest on white wine achieved ~0.55


def test_model_service_predict_red_and_white():
    """Verify direct service inference on red and white features."""
    service = WineQualityModelService()

    # Red wine
    red_features = {k: v for k, v in VALID_RED_WINE_PAYLOAD.items() if k != "wine_type"}
    red_res = service.predict("red", red_features)

    assert red_res["status"] == "success"
    assert red_res["wine_type"] == "red"
    assert 0.0 <= red_res["estimated_quality_score"] <= 10.0
    assert 0 <= red_res["rounded_quality_rating"] <= 10
    assert red_res["model_algorithm"] == "random_forest_regressor"
    assert "evaluation_metrics" in red_res
    assert red_res["evaluation_metrics"]["mae"] > 0.0
    assert "Portuguese Vinho Verde" in red_res["regional_applicability"]
    assert "strictly non-clinical" in red_res["disclaimer"]

    # White wine
    white_features = {k: v for k, v in VALID_WHITE_WINE_PAYLOAD.items() if k != "wine_type"}
    white_res = service.predict("white", white_features)

    assert white_res["status"] == "success"
    assert white_res["wine_type"] == "white"
    assert 0.0 <= white_res["estimated_quality_score"] <= 10.0
    assert 0 <= white_res["rounded_quality_rating"] <= 10


def test_model_unavailable_handling(tmp_path: Path):
    """Verify clean exception when model assets are missing."""
    empty_service = WineQualityModelService(model_dir=tmp_path)
    assert empty_service.is_model_available("red") is False
    assert empty_service.is_model_available("white") is False

    with pytest.raises(WineModelUnavailableError):
        empty_service.get_model_card()

    with pytest.raises(WineModelUnavailableError):
        features = {k: v for k, v in VALID_RED_WINE_PAYLOAD.items() if k != "wine_type"}
        empty_service.predict("red", features)


def test_api_wine_predict_success_red():
    """POST /api/wine/predict succeeds with valid red wine inputs."""
    response = client.post("/api/wine/predict", json=VALID_RED_WINE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["wine_type"] == "red"
    assert isinstance(data["estimated_quality_score"], float)
    assert isinstance(data["rounded_quality_rating"], int)
    assert 3 <= data["rounded_quality_rating"] <= 9
    assert data["model_version"] == "1.0.0"
    assert data["model_algorithm"] == "random_forest_regressor"

    # Evaluation metrics
    metrics = data["evaluation_metrics"]
    assert metrics["mae"] > 0.0
    assert metrics["rmse"] > 0.0
    assert metrics["r2_score"] > 0.0

    # Model card reference
    ref = data["model_card_reference"]
    assert "UCI Wine Quality Dataset" in ref["dataset_name"]
    assert ref["train_samples"] > 1000
    assert ref["test_samples"] > 300

    # Disclaimers
    assert "Portuguese Vinho Verde" in data["regional_applicability"]
    assert "does NOT represent a health claim" in data["disclaimer"]


def test_api_wine_predict_success_white():
    """POST /api/wine/predict succeeds with valid white wine inputs."""
    response = client.post("/api/wine/predict", json=VALID_WHITE_WINE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["wine_type"] == "white"
    assert isinstance(data["estimated_quality_score"], float)
    assert isinstance(data["rounded_quality_rating"], int)
    assert data["evaluation_metrics"]["r2_score"] > 0.0


def test_api_wine_predict_case_insensitive_type():
    """Wine type is case-insensitive ('RED', 'White')."""
    payload_upper = dict(VALID_RED_WINE_PAYLOAD)
    payload_upper["wine_type"] = "RED"
    res1 = client.post("/api/wine/predict", json=payload_upper)
    assert res1.status_code == 200
    assert res1.json()["wine_type"] == "red"

    payload_mixed = dict(VALID_WHITE_WINE_PAYLOAD)
    payload_mixed["wine_type"] = "White "
    res2 = client.post("/api/wine/predict", json=payload_mixed)
    assert res2.status_code == 200
    assert res2.json()["wine_type"] == "white"


def test_api_wine_predict_invalid_wine_type():
    """Unsupported wine types return 422 Unprocessable Entity."""
    payload = dict(VALID_RED_WINE_PAYLOAD)
    payload["wine_type"] = "rosé"
    response = client.post("/api/wine/predict", json=payload)
    assert response.status_code == 422
    assert "Unsupported wine_type" in response.text


def test_api_wine_predict_missing_feature_rejected():
    """Missing features are strictly rejected and never silently replaced with zero."""
    for field in [
        "fixed_acidity",
        "volatile_acidity",
        "citric_acid",
        "residual_sugar",
        "chlorides",
        "free_sulfur_dioxide",
        "total_sulfur_dioxide",
        "density",
        "pH",
        "sulphates",
        "alcohol",
    ]:
        incomplete_payload = dict(VALID_RED_WINE_PAYLOAD)
        del incomplete_payload[field]
        response = client.post("/api/wine/predict", json=incomplete_payload)
        assert response.status_code == 422, f"Omitting {field} must fail with 422."


def test_api_wine_predict_non_finite_rejected():
    """Non-finite values (null, NaN, inf) are strictly rejected."""
    # null
    payload_null = dict(VALID_RED_WINE_PAYLOAD)
    payload_null["alcohol"] = None
    res1 = client.post("/api/wine/predict", json=payload_null)
    assert res1.status_code == 422

    # NaN string
    payload_nan = dict(VALID_RED_WINE_PAYLOAD)
    payload_nan["alcohol"] = "NaN"
    res2 = client.post("/api/wine/predict", json=payload_nan)
    assert res2.status_code == 422

    # inf
    payload_inf = dict(VALID_RED_WINE_PAYLOAD)
    payload_inf["pH"] = "inf"
    res3 = client.post("/api/wine/predict", json=payload_inf)
    assert res3.status_code == 422


def test_api_wine_predict_out_of_bounds_rejected():
    """Physically impossible feature values are rejected."""
    # Negative pH
    p1 = dict(VALID_RED_WINE_PAYLOAD)
    p1["pH"] = -1.0
    assert client.post("/api/wine/predict", json=p1).status_code == 422

    # pH too high for wine (> 5.0)
    p2 = dict(VALID_RED_WINE_PAYLOAD)
    p2["pH"] = 6.5
    assert client.post("/api/wine/predict", json=p2).status_code == 422

    # Negative alcohol
    p3 = dict(VALID_RED_WINE_PAYLOAD)
    p3["alcohol"] = -2.0
    assert client.post("/api/wine/predict", json=p3).status_code == 422

    # Excessive alcohol (> 25%)
    p4 = dict(VALID_RED_WINE_PAYLOAD)
    p4["alcohol"] = 40.0
    assert client.post("/api/wine/predict", json=p4).status_code == 422

    # Negative volatile acidity
    p5 = dict(VALID_RED_WINE_PAYLOAD)
    p5["volatile_acidity"] = -0.5
    assert client.post("/api/wine/predict", json=p5).status_code == 422


def test_api_wine_predict_free_so2_exceeding_total_so2_rejected():
    """free_sulfur_dioxide cannot exceed total_sulfur_dioxide."""
    invalid_so2 = dict(VALID_RED_WINE_PAYLOAD)
    invalid_so2["free_sulfur_dioxide"] = 100.0
    invalid_so2["total_sulfur_dioxide"] = 50.0  # Physically impossible
    response = client.post("/api/wine/predict", json=invalid_so2)
    assert response.status_code == 422
    assert "cannot exceed total_sulfur_dioxide" in response.text


def test_api_wine_model_card_endpoint():
    """GET /api/wine/model-card returns full metadata and evaluation results."""
    response = client.get("/api/wine/model-card")
    assert response.status_code == 200
    card = response.json()

    assert card["model_name"] == "BQAS Wine Quality Sensory Predictor"
    assert "dataset_metadata" in card
    assert "training_protocol" in card
    assert "evaluation_summary" in card
    assert "red_wine" in card["evaluation_summary"]
    assert "white_wine" in card["evaluation_summary"]
    assert len(card["limitations_and_disclaimers"]) >= 4


def test_separation_from_composition_and_health_scoring():
    """Verify sensory prediction contains no health scoring or clinical classification."""
    response = client.post("/api/wine/predict", json=VALID_RED_WINE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()

    # Never fabricate health or composition scores
    assert "composition_score" not in data
    assert "health_impact_score" not in data
    assert "health_assessment" not in data
    assert "safe" not in str(data["disclaimer"]).lower() or "not" in str(data["disclaimer"]).lower()
    assert "strictly non-clinical" in data["disclaimer"]
