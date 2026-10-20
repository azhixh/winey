"""
Wine Quality Machine Learning Engine for BQAS.

Loads and executes trained scikit-learn regression models for Portuguese Vinho Verde wines.
Features:
- Separate models for Red and White wine pipelines.
- Strict input feature mapping to the 11 UCI physicochemical attributes.
- Complete separation from Composition Scoring and Health Impact Assessment.
- Explicit disclaimers on sensory estimation and regional generalizability.
"""

import os
import json
from pathlib import Path
from typing import Optional, Any
import joblib
import pandas as pd


FEATURE_NAMES = [
    "fixed acidity",
    "volatile acidity",
    "citric acid",
    "residual sugar",
    "chlorides",
    "free sulfur dioxide",
    "total sulfur dioxide",
    "density",
    "pH",
    "sulphates",
    "alcohol",
]

DEFAULT_MODEL_DIR = Path(__file__).parent / "wine_models"

REGIONAL_APPLICABILITY_NOTE = (
    "Trained exclusively on physicochemical data representing Portuguese Vinho Verde wines from Northwest Portugal "
    "(Cortez et al., 2009). This model reflects the unique high-acidity, low-alcohol profile of Vinho Verde "
    "and may not generalize to other wine regions, styles, grape varieties, vintages, or production methods."
)

SENSORY_ESTIMATE_DISCLAIMER = (
    "This estimated sensory quality rating is an empirical machine-learning estimate based on expert panel scores "
    "and is strictly non-clinical. It does NOT represent a health claim, a toxicological assessment, a safety guarantee, "
    "or an accredited laboratory certification. Sensory ratings must not be used to infer health benefits or justify consumption."
)


class WineModelUnavailableError(FileNotFoundError):
    """Raised when a requested wine model file or model card cannot be found."""
    pass


class WineQualityModelService:
    """
    Inference service for wine quality regression models.
    """

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._models: dict[str, Any] = {}
        self._model_card: Optional[dict[str, Any]] = None
        self._load_assets()

    def _load_assets(self) -> None:
        """Load Joblib model pipelines and JSON model card if present."""
        red_path = self.model_dir / "wine_model_red.joblib"
        white_path = self.model_dir / "wine_model_white.joblib"
        card_path = self.model_dir / "model_card.json"

        if red_path.exists():
            try:
                self._models["red"] = joblib.load(red_path)
            except Exception as e:
                self._models["red"] = None
        else:
            self._models["red"] = None

        if white_path.exists():
            try:
                self._models["white"] = joblib.load(white_path)
            except Exception as e:
                self._models["white"] = None
        else:
            self._models["white"] = None

        if card_path.exists():
            try:
                self._model_card = json.loads(card_path.read_text(encoding="utf-8"))
            except Exception:
                self._model_card = None
        else:
            self._model_card = None

    def is_model_available(self, wine_type: str) -> bool:
        """Check if model pipeline is loaded and ready for inference."""
        clean = wine_type.strip().lower()
        return self._models.get(clean) is not None

    def get_model_card(self) -> dict[str, Any]:
        """Return the structured model card."""
        if not self._model_card:
            raise WineModelUnavailableError(
                f"Model card not found at {self.model_dir / 'model_card.json'}. "
                "Ensure training script has been executed."
            )
        return self._model_card

    def predict(self, wine_type: str, features: dict[str, float]) -> dict[str, Any]:
        """
        Execute sensory quality estimation for a validated feature dictionary.

        Args:
            wine_type: 'red' or 'white' (case-insensitive)
            features: Dictionary containing all 11 required physicochemical metrics.

        Returns:
            Structured dictionary matching WinePredictionResponse.
        """
        clean_type = wine_type.strip().lower()
        if clean_type not in ("red", "white"):
            raise ValueError(f"Invalid wine_type '{wine_type}'. Must be 'red' or 'white'.")

        model = self._models.get(clean_type)
        if model is None:
            raise WineModelUnavailableError(
                f"Trained model for '{clean_type}' wine is unavailable at {self.model_dir}. "
                "Please run scripts/train_wine_model.py to generate model artifacts."
            )

        card = self.get_model_card()

        # Map input features to UCI DataFrame columns
        feature_map = {
            "fixed acidity": float(features["fixed_acidity"]),
            "volatile acidity": float(features["volatile_acidity"]),
            "citric acid": float(features["citric_acid"]),
            "residual sugar": float(features["residual_sugar"]),
            "chlorides": float(features["chlorides"]),
            "free sulfur dioxide": float(features["free_sulfur_dioxide"]),
            "total sulfur dioxide": float(features["total_sulfur_dioxide"]),
            "density": float(features["density"]),
            "pH": float(features["pH"]),
            "sulphates": float(features["sulphates"]),
            "alcohol": float(features["alcohol"]),
        }

        # Build single-sample DataFrame with exact column names expected by scikit-learn pipeline
        df_in = pd.DataFrame([feature_map], columns=FEATURE_NAMES)

        # Run pipeline inference (StandardScaler + RandomForestRegressor)
        raw_pred = float(model.predict(df_in)[0])
        # Bound estimate to valid sensory rating scale [0.0, 10.0]
        estimated_score = round(max(0.0, min(10.0, raw_pred)), 2)
        rounded_grade = int(round(estimated_score))

        # Extract held-out test evaluation metrics for this wine type
        eval_summary = card.get("evaluation_summary", {}).get(f"{clean_type}_wine", {})
        test_metrics = eval_summary.get("selected_test_metrics", {"mae": 0.0, "rmse": 0.0, "r2_score": 0.0})
        algorithm_name = eval_summary.get("algorithm", "RandomForestRegressor")
        model_version = card.get("model_version", "1.0.0")

        # Reference card DTO
        dataset_meta = card.get("dataset_metadata", {})
        protocol = card.get("training_protocol", {})
        ref_dto = {
            "model_name": card.get("model_name", "BQAS Wine Quality Sensory Predictor"),
            "model_version": model_version,
            "dataset_name": dataset_meta.get("dataset_name", "UCI Wine Quality Dataset"),
            "dataset_url": dataset_meta.get("dataset_url", "https://archive.ics.uci.edu/dataset/186/wine+quality"),
            "geographic_origin": dataset_meta.get("geographic_origin", "Vinho Verde region, Portugal"),
            "citation": dataset_meta.get("citation", "Cortez et al., 2009"),
            "train_test_split": protocol.get("train_test_split", "80% Train, 20% Held-Out Test"),
            "random_seed": protocol.get("random_seed", 42),
            "train_samples": eval_summary.get("train_samples", 0),
            "test_samples": eval_summary.get("test_samples", 0),
        }

        return {
            "status": "success",
            "wine_type": clean_type,
            "estimated_quality_score": estimated_score,
            "rounded_quality_rating": rounded_grade,
            "model_version": model_version,
            "model_algorithm": algorithm_name,
            "evaluation_metrics": test_metrics,
            "model_card_reference": ref_dto,
            "disclaimer": SENSORY_ESTIMATE_DISCLAIMER,
            "regional_applicability": REGIONAL_APPLICABILITY_NOTE,
            "input_features": {k: float(v) for k, v in features.items()},
        }


# Singleton service instance
_default_service: Optional[WineQualityModelService] = None


def get_wine_quality_service() -> WineQualityModelService:
    """Return default singleton WineQualityModelService instance."""
    global _default_service
    if _default_service is None:
        _default_service = WineQualityModelService()
    return _default_service
