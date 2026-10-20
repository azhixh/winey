"""
Pydantic schemas for wine quality machine learning prediction.
"""

import math
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class WineType(str, Enum):
    RED = "red"
    WHITE = "white"


class WinePredictionRequest(BaseModel):
    """
    Input features for wine sensory quality prediction.
    Corresponds to the 11 physicochemical laboratory metrics from the UCI Wine Quality dataset.
    """
    wine_type: str = Field(
        ...,
        description="Type of wine ('red' or 'white'). Case-insensitive.",
        examples=["red"],
    )
    fixed_acidity: float = Field(
        ...,
        gt=0.0,
        le=30.0,
        description="Fixed acidity in g(tartaric acid)/dm³ (typically 4.0 - 16.0)",
        examples=[7.4],
    )
    volatile_acidity: float = Field(
        ...,
        ge=0.0,
        le=5.0,
        description="Volatile acidity in g(acetic acid)/dm³ (typically 0.1 - 2.0)",
        examples=[0.70],
    )
    citric_acid: float = Field(
        ...,
        ge=0.0,
        le=5.0,
        description="Citric acid in g/dm³ (typically 0.0 - 1.5)",
        examples=[0.0],
    )
    residual_sugar: float = Field(
        ...,
        ge=0.0,
        le=200.0,
        description="Residual sugar in g/dm³ (typically 0.5 - 70.0)",
        examples=[1.9],
    )
    chlorides: float = Field(
        ...,
        ge=0.0,
        le=2.0,
        description="Chlorides in g(sodium chloride)/dm³ (typically 0.01 - 0.7)",
        examples=[0.076],
    )
    free_sulfur_dioxide: float = Field(
        ...,
        ge=0.0,
        le=500.0,
        description="Free sulfur dioxide in mg/dm³ (typically 1.0 - 300.0)",
        examples=[11.0],
    )
    total_sulfur_dioxide: float = Field(
        ...,
        ge=0.0,
        le=1000.0,
        description="Total sulfur dioxide in mg/dm³ (typically 5.0 - 500.0)",
        examples=[34.0],
    )
    density: float = Field(
        ...,
        gt=0.85,
        le=1.15,
        description="Density in g/cm³ (typically 0.98 - 1.01)",
        examples=[0.9978],
    )
    pH: float = Field(
        ...,
        gt=2.0,
        lt=5.0,
        description="pH on a 0-14 scale (typically 2.7 - 4.1 in wine)",
        examples=[3.51],
    )
    sulphates: float = Field(
        ...,
        ge=0.0,
        le=5.0,
        description="Sulphates in g(potassium sulphate)/dm³ (typically 0.2 - 2.0)",
        examples=[0.56],
    )
    alcohol: float = Field(
        ...,
        gt=0.0,
        le=25.0,
        description="Alcohol content in % vol. (typically 7.0 - 16.0%)",
        examples=[9.4],
    )

    @field_validator(
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
        mode="before",
    )
    @classmethod
    def validate_finite_numbers(cls, v: Any) -> float:
        """Reject None, NaN, and infinite floating point values."""
        if v is None:
            raise ValueError("Feature value cannot be null or omitted.")
        try:
            val = float(v)
        except (ValueError, TypeError):
            raise ValueError("Feature must be a valid numeric value.")
        if math.isnan(val) or math.isinf(val):
            raise ValueError("Feature must be a finite numeric value (NaN and inf are rejected).")
        return val

    @field_validator("wine_type")
    @classmethod
    def validate_wine_type(cls, v: str) -> str:
        """Validate and normalize wine type to lowercase 'red' or 'white'."""
        if not v or not isinstance(v, str):
            raise ValueError("wine_type must be a non-empty string ('red' or 'white').")
        clean = v.strip().lower()
        if clean not in ("red", "white"):
            raise ValueError(f"Unsupported wine_type '{v}'. Must be either 'red' or 'white'.")
        return clean

    @model_validator(mode="after")
    def validate_sulfur_dioxide_consistency(self) -> "WinePredictionRequest":
        """Verify that free sulfur dioxide does not exceed total sulfur dioxide."""
        if self.free_sulfur_dioxide > self.total_sulfur_dioxide:
            raise ValueError(
                f"free_sulfur_dioxide ({self.free_sulfur_dioxide} mg/dm³) cannot exceed "
                f"total_sulfur_dioxide ({self.total_sulfur_dioxide} mg/dm³)."
            )
        return self


class EvaluationMetricsDto(BaseModel):
    """Held-out test set performance metrics."""
    mae: float = Field(..., description="Mean Absolute Error on held-out test set")
    rmse: float = Field(..., description="Root Mean Squared Error on held-out test set")
    r2_score: float = Field(..., description="R-squared coefficient of determination")


class ModelCardReferenceDto(BaseModel):
    """Reference metadata describing the model origin and training protocol."""
    model_name: str
    model_version: str
    dataset_name: str
    dataset_url: str
    geographic_origin: str
    citation: str
    train_test_split: str
    random_seed: int
    train_samples: int
    test_samples: int


class WinePredictionResponse(BaseModel):
    """
    Response model for wine sensory quality prediction.
    """
    status: str = Field(default="success", description="Status indicator")
    wine_type: str = Field(..., description="Wine category evaluated ('red' or 'white')")
    estimated_quality_score: float = Field(
        ...,
        description="Continuous estimated sensory quality rating on a 0-10 scale",
    )
    rounded_quality_rating: int = Field(
        ...,
        description="Rounded integer sensory quality grade (e.g. 5, 6, 7)",
    )
    model_version: str = Field(..., description="Semantic version of the prediction model")
    model_algorithm: str = Field(..., description="Machine learning algorithm name")
    evaluation_metrics: EvaluationMetricsDto = Field(
        ...,
        description="Actual evaluation metrics achieved on held-out test data",
    )
    model_card_reference: ModelCardReferenceDto = Field(
        ...,
        description="Provenance and training protocol reference",
    )
    disclaimer: str = Field(
        ...,
        description="Explicit notice stating this estimate is sensory and not a health or chemical certification",
    )
    regional_applicability: str = Field(
        ...,
        description="Statement on geographic origin (Portuguese Vinho Verde) and generalizability limitations",
    )
    input_features: dict[str, float] = Field(
        ...,
        description="Normalized feature values used during inference",
    )
