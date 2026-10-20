"""
Health and status routes for BQAS backend.
"""

import os
from fastapi import APIRouter
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Server Health Check")
async def get_health() -> HealthResponse:
    """
    Check server status.
    Returns the server operational status, application name, and semantic version.
    """
    return HealthResponse(
        status="ok",
        app_name=os.getenv("APP_NAME", "Beverage Quality Analysis System (BQAS) Backend"),
        version=os.getenv("APP_VERSION", "0.1.0"),
        environment=os.getenv("ENVIRONMENT", "development")
    )
