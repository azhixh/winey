"""
Open Food Facts API provider for packaged non-alcoholic beverage products.

API Documentation:
- Search API: https://world.openfoodfacts.org/cgi/search.pl or https://world.openfoodfacts.org/api/v2/search
- Product API: https://world.openfoodfacts.org/api/v2/product/{barcode}
- Terms of Use: Requires descriptive User-Agent header; strictly limits request rates.
"""

import re
import datetime
import logging
from typing import Optional, Any
import httpx
from app.schemas.products import (
    ProductRecord,
    NutritionalValues,
    NonAlcoholicCategory,
)
from app.engine.data_quality import (
    assess_product_data_quality,
    validate_beverage_scope,
    ScopeRestrictionError,
)
from app.providers.cache import SimpleTTLCache

logger = logging.getLogger(__name__)

OFF_BASE_URL = "https://world.openfoodfacts.org"
DEFAULT_USER_AGENT = "BQAS-BeverageAnalysis/1.0 (https://github.com/bqas; bqas-backend@local)"
DEFAULT_TIMEOUT_SECONDS = 8.0

# Fields requested to minimize network payload
REQUESTED_FIELDS = "code,product_name,brands,ingredients_text,nutriments,serving_size,url,categories_tags"


class OpenFoodFactsProvider:
    """
    Asynchronous client for Open Food Facts API.
    """

    def __init__(
        self,
        base_url: str = OFF_BASE_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        cache: Optional[SimpleTTLCache] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout = timeout
        self.cache = cache or SimpleTTLCache(default_ttl_seconds=3600)

    def _get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

    def _parse_serving_size(self, serving_str: Optional[str]) -> tuple[Optional[float], Optional[str]]:
        """Extract numeric value and unit from serving size string (e.g., '330 ml', '12 fl oz')."""
        if not serving_str:
            return None, None
        match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z_\s]+)", serving_str)
        if match:
            try:
                val = float(match.group(1))
                unit = match.group(2).strip().lower()
                return val, unit
            except (ValueError, TypeError):
                pass
        return None, None

    def _parse_product_record(self, raw_prod: dict[str, Any]) -> Optional[ProductRecord]:
        """Normalize raw Open Food Facts JSON item into structured ProductRecord."""
        barcode = str(raw_prod.get("code") or "").strip()
        name = str(raw_prod.get("product_name") or "").strip()
        if not name or not barcode:
            return None

        brand = raw_prod.get("brands")
        if brand:
            brand = brand.strip()

        ingredients = raw_prod.get("ingredients_text")
        if ingredients:
            ingredients = ingredients.strip()

        nutriments = raw_prod.get("nutriments") or {}
        serving_raw = raw_prod.get("serving_size")
        serv_val, serv_unit = self._parse_serving_size(serving_raw)

        # Detect beverage type from categories or product name
        categories = [c.lower() for c in raw_prod.get("categories_tags") or []]
        name_lower = name.lower()
        if any("energy" in c for c in categories) or "energy drink" in name_lower or "energy" in name_lower:
            bev_type = NonAlcoholicCategory.ENERGY_DRINK.value
        else:
            bev_type = NonAlcoholicCategory.SOFT_DRINK.value

        # Extract nutrients per 100g/100ml and per serving
        sugar_100 = nutriments.get("sugars_100g")
        sugar_serv = nutriments.get("sugars_serving")

        cal_100 = nutriments.get("energy-kcal_100g")
        if cal_100 is None:
            # Fallback from kJ if kcal omitted (1 kcal = 4.184 kJ)
            kj_100 = nutriments.get("energy-kj_100g")
            if kj_100 is not None:
                cal_100 = round(float(kj_100) / 4.184, 2)
        cal_serv = nutriments.get("energy-kcal_serving")

        # Sodium: OFF reports in grams or mg. Standardize to mg.
        sodium_g_100 = nutriments.get("sodium_100g")
        sodium_100 = round(float(sodium_g_100) * 1000.0, 2) if sodium_g_100 is not None else None
        sodium_g_serv = nutriments.get("sodium_serving")
        sodium_serv = round(float(sodium_g_serv) * 1000.0, 2) if sodium_g_serv is not None else None

        # Caffeine: convert to mg if present
        caffeine_100_raw = nutriments.get("caffeine_100g")
        caffeine_100 = None
        if caffeine_100_raw is not None:
            # If in grams (< 1), convert to mg
            val = float(caffeine_100_raw)
            caffeine_100 = round(val * 1000.0, 2) if val < 1.0 else round(val, 2)

        caffeine_serv_raw = nutriments.get("caffeine_serving")
        caffeine_serv = None
        if caffeine_serv_raw is not None:
            val = float(caffeine_serv_raw)
            caffeine_serv = round(val * 1000.0, 2) if val < 1.0 else round(val, 2)

        nutritional_vals = NutritionalValues(
            serving_size_value=serv_val,
            serving_size_unit=serv_unit,
            serving_size_raw=serving_raw,
            sugar_per_100ml=round(float(sugar_100), 2) if sugar_100 is not None else None,
            sugar_per_serving=round(float(sugar_serv), 2) if sugar_serv is not None else None,
            calories_per_100ml=round(float(cal_100), 2) if cal_100 is not None else None,
            calories_per_serving=round(float(cal_serv), 2) if cal_serv is not None else None,
            sodium_per_100ml=sodium_100,
            sodium_per_serving=sodium_serv,
            caffeine_per_100ml=caffeine_100,
            caffeine_per_serving=caffeine_serv,
            alcohol_percentage=0.0,
        )

        source_url = raw_prod.get("url") or f"{self.base_url}/product/{barcode}"

        # Evaluate data quality notices
        quality_warnings = assess_product_data_quality(
            product_name=name,
            beverage_type=bev_type,
            serving_size_value=serv_val,
            serving_size_unit=serv_unit,
            sugar_per_100ml=nutritional_vals.sugar_per_100ml,
            sugar_per_serving=nutritional_vals.sugar_per_serving,
            calories_per_100ml=nutritional_vals.calories_per_100ml,
            calories_per_serving=nutritional_vals.calories_per_serving,
            sodium_per_100ml=nutritional_vals.sodium_per_100ml,
            sodium_per_serving=nutritional_vals.sodium_per_serving,
            caffeine_per_100ml=nutritional_vals.caffeine_per_100ml,
            caffeine_per_serving=nutritional_vals.caffeine_per_serving,
            ingredients=ingredients,
            is_independently_verified=False,
            source_name="Open Food Facts",
        )

        return ProductRecord(
            product_id=f"off:{barcode}",
            product_name=name,
            brand=brand,
            beverage_type=bev_type,
            ingredients=ingredients,
            nutritional_values=nutritional_vals,
            source_name="Open Food Facts",
            source_url=source_url,
            retrieval_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            verification_status="unverified_provider_data",
            is_independently_verified=False,
            data_quality_warnings=quality_warnings,
        )

    async def search(
        self,
        query: str,
        beverage_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> list[ProductRecord]:
        """
        Search Open Food Facts for packaged beverage products.
        """
        # 1. Scope restriction
        clean_category = validate_beverage_scope(beverage_type)

        cache_key = f"off:search:{query}:{clean_category}:{page}:{page_size}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Prepare parameters
        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page": page,
            "page_size": page_size,
            "fields": REQUESTED_FIELDS,
        }

        # Filter by category if specified
        if clean_category == NonAlcoholicCategory.ENERGY_DRINK.value:
            params["tagtype_0"] = "categories"
            params["tag_contains_0"] = "contains"
            params["tag_0"] = "energy-drinks"
        elif clean_category == NonAlcoholicCategory.SOFT_DRINK.value:
            params["tagtype_0"] = "categories"
            params["tag_contains_0"] = "contains"
            params["tag_0"] = "soft-drinks"

        url = f"{self.base_url}/cgi/search.pl"
        headers = self._get_headers()

        close_client = False
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout)
            close_client = True

        try:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 429:
                logger.warning("Open Food Facts rate limit reached (HTTP 429).")
                return []
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException:
            logger.warning("Timeout connecting to Open Food Facts API.")
            return []
        except (httpx.HTTPError, ValueError) as err:
            logger.warning(f"Error querying Open Food Facts: {err}")
            return []
        finally:
            if close_client:
                await client.aclose()

        raw_products = data.get("products") or []
        results: list[ProductRecord] = []
        for raw in raw_products:
            parsed = self._parse_product_record(raw)
            if parsed:
                # Disallow alcoholic products if any slipped through
                cats = [c.lower() for c in raw.get("categories_tags") or []]
                if any(alc in cats for alc in ["en:alcoholic-beverages", "en:beers", "en:wines", "en:spirits"]):
                    continue
                results.append(parsed)

        self.cache.set(cache_key, results)
        return results

    async def get_by_id(
        self,
        barcode: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Optional[ProductRecord]:
        """
        Fetch single product by barcode from Open Food Facts.
        """
        clean_code = barcode.replace("off:", "").strip()
        cache_key = f"off:product:{clean_code}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/api/v2/product/{clean_code}.json"
        params = {"fields": REQUESTED_FIELDS}
        headers = self._get_headers()

        close_client = False
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout)
            close_client = True

        try:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code in (404, 400):
                return None
            if resp.status_code == 429:
                logger.warning("Open Food Facts rate limit reached (HTTP 429).")
                return None
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException:
            logger.warning("Timeout fetching product from Open Food Facts.")
            return None
        except (httpx.HTTPError, ValueError) as err:
            logger.warning(f"Error fetching from Open Food Facts: {err}")
            return None
        finally:
            if close_client:
                await client.aclose()

        if data.get("status") != 1 or "product" not in data:
            return None

        record = self._parse_product_record(data["product"])
        if record:
            self.cache.set(cache_key, record)
        return record
