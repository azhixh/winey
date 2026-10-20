"""
Mocked unit tests for nutritional data providers:
- OpenFoodFactsProvider
- USDAFoodDataProvider
- ProductProviderManager
- SimpleTTLCache
Covers: field extraction, missing field preservation, unit conversion,
timeouts, rate limits (429), malformed responses, caching, and scope restriction.
No external network access required.
"""

from unittest.mock import AsyncMock, patch, MagicMock
import pytest
import httpx
from app.providers.cache import SimpleTTLCache
from app.providers.open_food_facts import OpenFoodFactsProvider
from app.providers.usda_food_data import USDAFoodDataProvider
from app.providers import ProductProviderManager
from app.engine.data_quality import ScopeRestrictionError


# =====================================================================
# SimpleTTLCache Tests
# =====================================================================

def test_cache_set_get_and_expiration():
    cache = SimpleTTLCache(default_ttl_seconds=1)
    cache.set("key1", "value1", ttl_seconds=10)
    assert cache.get("key1") == "value1"

    # Expired key
    cache.set("key2", "value2", ttl_seconds=-1)
    assert cache.get("key2") is None


def test_cache_clear():
    cache = SimpleTTLCache()
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.size() == 2
    cache.clear()
    assert cache.size() == 0
    assert cache.get("a") is None


# =====================================================================
# OpenFoodFactsProvider Tests (Mocked)
# =====================================================================

MOCK_OFF_SEARCH_RESPONSE = {
    "count": 1,
    "page": 1,
    "page_size": 10,
    "products": [
        {
            "code": "049000000443",
            "product_name": "Coca-Cola Original Taste",
            "brands": "Coca-Cola",
            "ingredients_text": "Carbonated Water, High Fructose Corn Syrup, Caramel Color, Phosphoric Acid",
            "serving_size": "12 fl oz (355 mL)",
            "categories_tags": ["en:beverages", "en:carbonated-drinks", "en:sodas", "en:soft-drinks"],
            "url": "https://world.openfoodfacts.org/product/049000000443",
            "nutriments": {
                "sugars_100g": 10.6,
                "sugars_serving": 39.0,
                "energy-kcal_100g": 42.0,
                "energy-kcal_serving": 140.0,
                "sodium_100g": 0.015,  # 0.015 g = 15 mg
                "sodium_serving": 0.045, # 0.045 g = 45 mg
                "caffeine_100g": 0.01,  # 0.01 g = 10 mg
                "caffeine_serving": 0.034, # 0.034 g = 34 mg
            },
        }
    ],
}


@pytest.mark.anyio
async def test_off_search_successful_parsing():
    provider = OpenFoodFactsProvider(cache=SimpleTTLCache())
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_OFF_SEARCH_RESPONSE
    mock_resp.raise_for_status.return_value = None
    mock_client.get.return_value = mock_resp

    results = await provider.search("coca cola", beverage_type="Soft drink", client=mock_client)

    assert len(results) == 1
    prod = results[0]
    assert prod.product_id == "off:049000000443"
    assert prod.product_name == "Coca-Cola Original Taste"
    assert prod.brand == "Coca-Cola"
    assert prod.beverage_type == "Soft drink"
    assert prod.nutritional_values.sugar_per_100ml == 10.6
    assert prod.nutritional_values.sugar_per_serving == 39.0
    assert prod.nutritional_values.calories_per_100ml == 42.0
    assert prod.nutritional_values.sodium_per_100ml == 15.0  # Converted to mg
    assert prod.nutritional_values.caffeine_per_100ml == 10.0 # Converted to mg
    assert prod.is_independently_verified is False
    assert prod.verification_status == "unverified_provider_data"


@pytest.mark.anyio
async def test_off_search_preserves_missing_fields_as_null():
    """
    Test missing fields are kept strictly as None and not defaulted to 0.
    """
    provider = OpenFoodFactsProvider(cache=SimpleTTLCache())
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "products": [
            {
                "code": "111111111111",
                "product_name": "Minimal Soda",
                # missing brands, ingredients, nutriments
                "nutriments": {},
            }
        ]
    }
    mock_client.get.return_value = mock_resp

    results = await provider.search("soda", client=mock_client)
    assert len(results) == 1
    prod = results[0]
    assert prod.brand is None
    assert prod.ingredients is None
    assert prod.nutritional_values.sugar_per_100ml is None
    assert prod.nutritional_values.calories_per_100ml is None
    assert prod.nutritional_values.sodium_per_100ml is None
    assert prod.nutritional_values.caffeine_per_100ml is None


@pytest.mark.anyio
async def test_off_search_handles_timeout():
    provider = OpenFoodFactsProvider(cache=SimpleTTLCache())
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.TimeoutException("Read timed out")

    results = await provider.search("timeout query", client=mock_client)
    assert results == []


@pytest.mark.anyio
async def test_off_search_handles_rate_limit_429():
    provider = OpenFoodFactsProvider(cache=SimpleTTLCache())
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_client.get.return_value = mock_resp

    results = await provider.search("rate limit query", client=mock_client)
    assert results == []


@pytest.mark.anyio
async def test_off_search_handles_malformed_json():
    provider = OpenFoodFactsProvider(cache=SimpleTTLCache())
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("Invalid JSON")
    mock_client.get.return_value = mock_resp

    results = await provider.search("malformed query", client=mock_client)
    assert results == []


@pytest.mark.anyio
async def test_off_cache_prevents_duplicate_http_request():
    cache = SimpleTTLCache()
    provider = OpenFoodFactsProvider(cache=cache)
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_OFF_SEARCH_RESPONSE
    mock_client.get.return_value = mock_resp

    # First call
    res1 = await provider.search("cola", client=mock_client)
    assert mock_client.get.call_count == 1

    # Second call with same parameters should hit cache
    res2 = await provider.search("cola", client=mock_client)
    assert mock_client.get.call_count == 1
    assert len(res1) == len(res2)


# =====================================================================
# USDAFoodDataProvider Tests (Mocked)
# =====================================================================

MOCK_USDA_SEARCH_RESPONSE = {
    "totalHits": 1,
    "currentPage": 1,
    "totalPages": 1,
    "foods": [
        {
            "fdcId": 171865,
            "description": "Carbonated beverage, cola",
            "dataType": "Foundation",
            "servingSize": 355.0,
            "servingSizeUnit": "MLT",
            "foodNutrients": [
                {"nutrientId": 1008, "nutrientName": "Energy", "value": 41.0, "unitName": "KCAL"},
                {"nutrientId": 2000, "nutrientName": "Sugars, total including NLEA", "value": 10.5, "unitName": "G"},
                {"nutrientId": 1093, "nutrientName": "Sodium, Na", "value": 12.0, "unitName": "MG"},
                {"nutrientId": 1057, "nutrientName": "Caffeine", "value": 11.0, "unitName": "MG"},
            ],
        }
    ],
}


@pytest.mark.anyio
async def test_usda_search_successful_parsing():
    provider = USDAFoodDataProvider(cache=SimpleTTLCache())
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_USDA_SEARCH_RESPONSE
    mock_client.get.return_value = mock_resp

    results = await provider.search("cola", beverage_type="Soft drink", client=mock_client)
    assert len(results) == 1
    prod = results[0]
    assert prod.product_id == "usda:171865"
    assert prod.product_name == "Carbonated beverage, cola"
    # Foundation data in USDA reports per 100g/mL
    assert prod.nutritional_values.calories_per_100ml == 41.0
    assert prod.nutritional_values.sugar_per_100ml == 10.5
    assert prod.nutritional_values.sodium_per_100ml == 12.0
    assert prod.nutritional_values.caffeine_per_100ml == 11.0
    # Foundation foods are laboratory-analyzed reference foods
    assert prod.is_independently_verified is True
    assert prod.verification_status == "independently_verified"


@pytest.mark.anyio
async def test_usda_search_handles_timeout_and_429():
    provider = USDAFoodDataProvider(cache=SimpleTTLCache())
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Test timeout
    mock_client.get.side_effect = httpx.TimeoutException("Read timed out")
    res_timeout = await provider.search("cola", client=mock_client)
    assert res_timeout == []

    # Test 429
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_client.get.side_effect = None
    mock_client.get.return_value = mock_resp_429
    res_429 = await provider.search("cola", client=mock_client)
    assert res_429 == []


# =====================================================================
# ProductProviderManager Tests
# =====================================================================

@pytest.mark.anyio
async def test_provider_manager_scope_rejection_alcoholic():
    """
    Provider manager must strictly reject alcoholic categories (Beer, Wine, Spirits).
    """
    manager = ProductProviderManager()
    with pytest.raises(ScopeRestrictionError, match="strictly disallowed in Step 3"):
        await manager.search_products("Heineken", beverage_type="Beer")

    with pytest.raises(ScopeRestrictionError, match="strictly disallowed in Step 3"):
        await manager.search_products("Chardonnay", beverage_type="Wine")


@pytest.mark.anyio
async def test_provider_manager_searches_both_providers():
    off_mock = AsyncMock(spec=OpenFoodFactsProvider)
    off_mock.search.return_value = []
    usda_mock = AsyncMock(spec=USDAFoodDataProvider)
    usda_mock.search.return_value = []
    usda_mock.is_demo_key.return_value = True

    manager = ProductProviderManager(off_provider=off_mock, usda_provider=usda_mock)
    response = await manager.search_products("energy drink", beverage_type="Energy drink")

    assert response.query == "energy drink"
    assert response.beverage_type_filter == "Energy drink"
    assert off_mock.search.called
    assert usda_mock.search.called
    assert any("DEMO_KEY" in w for w in response.warnings)


def test_provider_manager_data_sources_info():
    manager = ProductProviderManager()
    info = manager.get_data_sources_info()

    assert "Soft drink" in info.supported_categories
    assert "Energy drink" in info.supported_categories
    assert "Beer" in info.disallowed_categories
    assert len(info.data_sources) == 2
    assert any(ds.source_name == "Open Food Facts" for ds in info.data_sources)
    assert any(ds.source_name == "USDA FoodData Central" for ds in info.data_sources)
    assert info.scoring_readiness["composition_score_status"] == "unavailable"
