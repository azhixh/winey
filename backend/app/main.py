"""
Main entry point for Beverage Quality Analysis System (BQAS) Backend API.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes import (
    health_router,
    beverages_router,
    products_router,
    wine_router,
    scoring_router,
)

# Environment configuration
APP_NAME = os.getenv("APP_NAME", "Beverage Quality Analysis System (BQAS) Backend")
APP_VERSION = os.getenv("APP_VERSION", "0.5.0")
APP_DESCRIPTION = (
    "Backend service for analyzing beverage composition, nutritional profiles, "
    "integrating external nutritional datasets, and predicting wine sensory quality ratings."
)
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def parse_cors_origins() -> list[str]:
    """Parse CORS origins from environment variable, falling back to localhost defaults."""
    env_origins = os.getenv("CORS_ORIGINS")
    if not env_origins:
        return DEFAULT_CORS_ORIGINS
    return [origin.strip() for origin in env_origins.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan handler."""
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS Middleware
origins = parse_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Format request validation errors into a structured, clear response.
    Provides human-readable feedback on why payload parameters failed validation.
    """
    errors: list[dict[str, str]] = []
    for err in exc.errors():
        # Build field path (e.g., body -> serving_size_ml)
        location = " -> ".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        field_name = location if location else "payload"
        errors.append({
            "field": field_name,
            "message": err.get("msg", "Invalid input value"),
            "type": err.get("type", "validation_error"),
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "One or more input fields failed validation.",
            "detail": errors,
            "details": errors,
        },
    )


# Register API routes with /api prefix
app.include_router(health_router, prefix="/api")
app.include_router(beverages_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(wine_router, prefix="/api")
app.include_router(scoring_router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint welcoming users and linking to API documentation."""
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "docs_url": "/docs",
        "health_url": "/api/health",
        "supported_endpoints": [
            "GET /api/health",
            "GET /api/beverage-types",
            "POST /api/analyze",
            "POST /api/scoring/evaluate",
            "GET /api/scoring/rules",
            "GET /api/scoring/benchmarks",
            "GET /api/products/search",
            "GET /api/products/{product_id}",
            "GET /api/data-sources",
            "POST /api/wine/predict",
            "GET /api/wine/model-card",
        ],
    }

