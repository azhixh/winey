"""
Comprehensive automated test suite for BQAS backend:
- Server health endpoint (GET /api/health)
- Beverage categories endpoint (GET /api/beverage-types)
- Valid and invalid analysis requests (POST /api/analyze)
- Missing-value preservation (strictly null, never default to zero)
- Physical ethanol calculations (~0.789 g/mL density)
- Unassigned score safeguards (composition_score and health_impact_score remain null)
- CORS header configuration for local frontend
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SUPPORTED_BEVERAGE_TYPES = [
    "Soft drink",
    "Beer",
    "Wine",
    "Spirits",
    "Energy drink",
]


# =====================================================================
# 1. Health & Root Endpoint Tests
# =====================================================================

def test_health_endpoint_success():
    """
    Test GET /api/health returns 200 OK with server status, application name, and version.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert data["version"] == "0.1.0"


def test_root_endpoint_success():
    """
    Test GET / returns 200 OK with links to documentation and endpoints.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs_url" in data
    assert "health_url" in data
    assert any("/api/health" in ep for ep in data["supported_endpoints"])
    assert any("/api/beverage-types" in ep for ep in data["supported_endpoints"])
    assert any("/api/analyze" in ep for ep in data["supported_endpoints"])


def test_health_with_custom_env(monkeypatch):
    """
    Test GET /api/health dynamically reflects environment variable updates.
    """
    monkeypatch.setenv("APP_NAME", "Custom BQAS Service")
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.setenv("ENVIRONMENT", "staging")

    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "Custom BQAS Service"
    assert data["version"] == "1.2.3"
    assert data["environment"] == "staging"


# =====================================================================
# 2. Beverage Types Endpoint Tests
# =====================================================================

def test_get_beverage_types_returns_all_five_categories():
    """
    Test GET /api/beverage-types returns exactly the five required categories.
    """
    response = client.get("/api/beverage-types")
    assert response.status_code == 200
    data = response.json()

    assert "beverage_types" in data
    assert data["total"] == 5
    assert sorted(data["beverage_types"]) == sorted(SUPPORTED_BEVERAGE_TYPES)


# =====================================================================
# 3. Analysis Endpoint - Valid Requests & Missing Value Preservation
# =====================================================================

def test_analyze_full_valid_request():
    """
    Test POST /api/analyze with all fields provided.
    """
    payload = {
        "beverage_type": "Beer",
        "serving_size_ml": 500.0,
        "sugar_g": 12.0,
        "calories": 210.0,
        "sodium_mg": 15.0,
        "caffeine_mg": 0.0,
        "alcohol_percentage": 5.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    # Verify input echo
    assert data["input_data"]["beverage_type"] == "Beer"
    assert data["input_data"]["serving_size_ml"] == 500.0
    assert data["input_data"]["sugar_g"] == 12.0
    assert data["input_data"]["calories"] == 210.0
    assert data["input_data"]["sodium_mg"] == 15.0
    assert data["input_data"]["caffeine_mg"] == 0.0
    assert data["input_data"]["alcohol_percentage"] == 5.0

    # Verify calculation: 500 * 0.05 * 0.789 = 19.725 -> 19.73
    assert data["calculations"]["alcohol_grams"] == 19.73
    assert data["calculations"]["ethanol_density_used_g_ml"] == 0.789

    # Verify scores are strictly null
    assert data["composition_score"] is None
    assert data["health_impact_score"] is None

    # Verify warnings exist and explain scores
    assert any("remain null" in w for w in data["warnings"])


def test_analyze_missing_optional_fields_preserves_null():
    """
    Test that omitted fields are NEVER silently replaced with zero,
    and remain strictly null in the returned payload.
    """
    payload = {
        "beverage_type": "Soft drink",
        "serving_size_ml": 330.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    input_data = data["input_data"]
    assert input_data["beverage_type"] == "Soft drink"
    assert input_data["serving_size_ml"] == 330.0
    assert input_data["sugar_g"] is None
    assert input_data["calories"] is None
    assert input_data["sodium_mg"] is None
    assert input_data["caffeine_mg"] is None
    assert input_data["alcohol_percentage"] is None

    # Alcohol calculation must be None when alcohol_percentage is omitted
    assert data["calculations"]["alcohol_grams"] is None

    # Warnings must mention preserved nulls
    assert any("omitted and preserved as null" in w for w in data["warnings"])
    assert any("Alcohol percentage was not provided" in w for w in data["warnings"])


def test_analyze_partially_provided_metrics():
    """
    Test providing some nutritional values (sugar and caffeine) while omitting others.
    """
    payload = {
        "beverage_type": "Energy drink",
        "serving_size_ml": 250.0,
        "sugar_g": 27.5,
        "caffeine_mg": 80.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    input_data = data["input_data"]
    assert input_data["sugar_g"] == 27.5
    assert input_data["caffeine_mg"] == 80.0
    # Omitted must remain null
    assert input_data["calories"] is None
    assert input_data["sodium_mg"] is None
    assert input_data["alcohol_percentage"] is None
    assert data["calculations"]["alcohol_grams"] is None


# =====================================================================
# 4. Alcohol Grams Calculation Tests
# =====================================================================

def test_alcohol_calculation_beer():
    """
    Test alcohol calculation for beer: 500 mL at 5.0% ABV.
    500 * (5.0 / 100) * 0.789 = 25 * 0.789 = 19.725 -> 19.73 g
    """
    payload = {
        "beverage_type": "Beer",
        "serving_size_ml": 500.0,
        "alcohol_percentage": 5.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["calculations"]["alcohol_grams"] == 19.73


def test_alcohol_calculation_wine():
    """
    Test alcohol calculation for wine: 150 mL at 12.5% ABV.
    150 * (12.5 / 100) * 0.789 = 18.75 * 0.789 = 14.79375 -> 14.79 g
    """
    payload = {
        "beverage_type": "Wine",
        "serving_size_ml": 150.0,
        "alcohol_percentage": 12.5,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["calculations"]["alcohol_grams"] == 14.79


def test_alcohol_calculation_spirits():
    """
    Test alcohol calculation for spirits shot: 45 mL at 40.0% ABV.
    45 * (40.0 / 100) * 0.789 = 18.0 * 0.789 = 14.202 -> 14.2 g
    """
    payload = {
        "beverage_type": "Spirits",
        "serving_size_ml": 45.0,
        "alcohol_percentage": 40.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["calculations"]["alcohol_grams"] == 14.2


def test_alcohol_calculation_zero_percent():
    """
    Test alcohol calculation when alcohol_percentage is explicitly 0.0%.
    Should return 0.0 grams (valid non-null calculation).
    """
    payload = {
        "beverage_type": "Soft drink",
        "serving_size_ml": 355.0,
        "alcohol_percentage": 0.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["calculations"]["alcohol_grams"] == 0.0


# =====================================================================
# 5. Input Normalization and Aliases
# =====================================================================

def test_case_insensitive_beverage_type():
    """
    Test that beverage type accepts lowercase or mixed-case string inputs.
    """
    payload = {
        "beverage_type": "energy drink",
        "serving_size_ml": 250.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["input_data"]["beverage_type"] == "Energy drink"


def test_field_aliases_accepted():
    """
    Test that common aliases (serving_size, sugar, calories_kcal, abv) are correctly mapped.
    """
    payload = {
        "beverage_type": "Beer",
        "serving_size": 330.0,
        "sugar": 10.0,
        "abv": 4.5,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["input_data"]["serving_size_ml"] == 330.0
    assert data["input_data"]["sugar_g"] == 10.0
    assert data["input_data"]["alcohol_percentage"] == 4.5


# =====================================================================
# 6. Validation and Error Handling Tests
# =====================================================================

@pytest.mark.parametrize("invalid_type", ["Soda", "Cocktail", "Water", "Whiskey", ""])
def test_invalid_beverage_type_fails(invalid_type):
    """
    Test that non-whitelisted beverage types trigger 422 Unprocessable Entity.
    """
    payload = {
        "beverage_type": invalid_type,
        "serving_size_ml": 250.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "Validation Error"
    assert "detail" in data


def test_zero_serving_size_fails():
    """
    Serving size must be strictly positive (gt=0).
    """
    payload = {
        "beverage_type": "Beer",
        "serving_size_ml": 0.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_negative_serving_size_fails():
    """
    Negative serving size must fail.
    """
    payload = {
        "beverage_type": "Beer",
        "serving_size_ml": -250.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_excessive_serving_size_fails():
    """
    Serving size > 5000 mL exceeds reasonable single serving limit.
    """
    payload = {
        "beverage_type": "Beer",
        "serving_size_ml": 10000.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_negative_composition_values_fail():
    """
    Nonnegative check: negative sugar, calories, sodium, caffeine, alcohol must fail.
    """
    # Negative sugar
    res = client.post("/api/analyze", json={"beverage_type": "Beer", "serving_size_ml": 330, "sugar_g": -1.0})
    assert res.status_code == 422

    # Negative calories
    res = client.post("/api/analyze", json={"beverage_type": "Beer", "serving_size_ml": 330, "calories": -50.0})
    assert res.status_code == 422

    # Negative sodium
    res = client.post("/api/analyze", json={"beverage_type": "Beer", "serving_size_ml": 330, "sodium_mg": -5.0})
    assert res.status_code == 422

    # Negative caffeine
    res = client.post("/api/analyze", json={"beverage_type": "Beer", "serving_size_ml": 330, "caffeine_mg": -10.0})
    assert res.status_code == 422

    # Negative alcohol percentage
    res = client.post("/api/analyze", json={"beverage_type": "Beer", "serving_size_ml": 330, "alcohol_percentage": -2.0})
    assert res.status_code == 422


def test_alcohol_percentage_over_100_fails():
    """
    Alcohol percentage cannot physically exceed 100%.
    """
    payload = {
        "beverage_type": "Spirits",
        "serving_size_ml": 50.0,
        "alcohol_percentage": 105.0,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


# =====================================================================
# 7. CORS Headers Test
# =====================================================================

def test_cors_headers_frontend_origin():
    """
    Verify CORS configuration permits frontend origin http://localhost:5173.
    """
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
