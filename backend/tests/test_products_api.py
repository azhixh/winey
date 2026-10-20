"""
Integration tests for FastAPI endpoints:
- GET /api/products/search
- GET /api/products/{product_id}
- GET /api/data-sources
Uses mocked provider manager to guarantee offline execution without external network dependence.
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.products import ProductRecord, NutritionalValues

client = TestClient(app)

SAMPLE_PRODUCT = ProductRecord(
    product_id="off:049000000443",
    product_name="Diet Cola",
    brand="Cola Co",
    beverage_type="Soft drink",
    ingredients="Carbonated water, aspartame, caramel color",
    nutritional_values=NutritionalValues(
        serving_size_value=355.0,
        serving_size_unit="ml",
        sugar_per_100ml=0.0,
        sugar_per_serving=0.0,
        calories_per_100ml=0.0,
        calories_per_serving=0.0,
        sodium_per_100ml=12.0,
        sodium_per_serving=40.0,
        caffeine_per_100ml=10.0,
        caffeine_per_serving=35.0,
        alcohol_percentage=0.0,
    ),
    source_name="Open Food Facts",
    source_url="https://world.openfoodfacts.org/product/049000000443",
    retrieval_timestamp="2026-10-20T12:00:00Z",
    verification_status="unverified_provider_data",
    is_independently_verified=False,
    data_quality_warnings=["Values are manufacturer-declared and unverified."],
)


# =====================================================================
# GET /api/products/search Tests
# =====================================================================

def test_search_missing_query_fails_validation():
    """Missing query string 'q' should trigger 422 Unprocessable Entity."""
    response = client.get("/api/products/search")
    assert response.status_code == 422


@patch("app.routes.products.provider_manager.search_products")
def test_search_successful_mocked(mock_search):
    mock_search.return_value = AsyncMock()
    mock_response = {
        "query": "cola",
        "beverage_type_filter": "Soft drink",
        "source_filter": "all",
        "total_results": 1,
        "page": 1,
        "page_size": 10,
        "results": [SAMPLE_PRODUCT.model_dump()],
        "warnings": [],
    }

    async def _async_mock(*args, **kwargs):
        from app.schemas.products import ProductSearchResponse
        return ProductSearchResponse(**mock_response)

    mock_search.side_effect = _async_mock

    response = client.get("/api/products/search?q=cola&beverage_type=Soft drink")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "cola"
    assert data["total_results"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["product_id"] == "off:049000000443"
    assert data["results"][0]["product_name"] == "Diet Cola"


def test_search_disallowed_alcoholic_beverage_returns_400():
    """
    Searching with beverage_type='Beer' or 'Wine' must return 400 Bad Request.
    """
    response = client.get("/api/products/search?q=heineken&beverage_type=Beer")
    assert response.status_code == 400
    data = response.json()
    assert "strictly disallowed in Step 3" in data["detail"]

    response = client.get("/api/products/search?q=merlot&beverage_type=Wine")
    assert response.status_code == 400
    assert "strictly disallowed in Step 3" in response.json()["detail"]


# =====================================================================
# GET /api/products/{product_id} Tests
# =====================================================================

@patch("app.routes.products.provider_manager.get_product_by_id")
def test_get_product_by_id_success(mock_get):
    async def _mock_get(product_id, client=None):
        if product_id == "off:049000000443":
            return SAMPLE_PRODUCT
        return None

    mock_get.side_effect = _mock_get

    response = client.get("/api/products/off:049000000443")
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "off:049000000443"
    assert data["brand"] == "Cola Co"
    assert data["source_name"] == "Open Food Facts"
    assert data["is_independently_verified"] is False


@patch("app.routes.products.provider_manager.get_product_by_id")
def test_get_product_by_id_not_found(mock_get):
    async def _mock_get(product_id, client=None):
        return None

    mock_get.side_effect = _mock_get

    response = client.get("/api/products/nonexistent:999999")
    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


# =====================================================================
# GET /api/data-sources Tests
# =====================================================================

def test_get_data_sources():
    response = client.get("/api/data-sources")
    assert response.status_code == 200
    data = response.json()

    assert "Soft drink" in data["supported_categories"]
    assert "Energy drink" in data["supported_categories"]
    assert "Beer" in data["disallowed_categories"]
    assert "Wine" in data["disallowed_categories"]
    assert "Spirits" in data["disallowed_categories"]

    assert len(data["data_sources"]) >= 2
    source_names = [ds["source_name"] for ds in data["data_sources"]]
    assert "Open Food Facts" in source_names
    assert "USDA FoodData Central" in source_names

    readiness = data["scoring_readiness"]
    assert readiness["composition_score_status"] == "unavailable"
    assert readiness["health_impact_score_status"] == "unavailable"
    assert readiness["sample_size_requirement"] == 100
    assert "Composition Score requires at least 100 quality-checked records" in readiness["explanation"]
