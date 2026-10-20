"""
USDA FoodData Central API provider for nutritional reference and branded beverage data.

Documentation:
- FoodData Central API: https://fdc.nal.usda.gov/api-guide.html
- Search Endpoint: https://api.nal.usda.gov/fdc/v1/foods/search
- Food Details: https://api.nal.usda.gov/fdc/v1/food/{fdcId}
- Authentication: Configurable via USDA_API_KEY environment variable (defaults to 'DEMO_KEY').
"""

import os
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

USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
DEFAULT_TIMEOUT_SECONDS = 8.0

# USDA Nutrient ID Constants
NUTRIENT_ID_ENERGY_KCAL = 1008
NUTRIENT_ID_SUGARS_TOTAL = 2000
NUTRIENT_ID_SODIUM = 1093
NUTRIENT_ID_CAFFEINE = 1057


class USDAFoodDataProvider:
    """
    Asynchronous client for USDA FoodData Central API.
    """

    def __init__(
        self,
        base_url: str = USDA_BASE_URL,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        cache: Optional[SimpleTTLCache] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("USDA_API_KEY", "DEMO_KEY")
        self.timeout = timeout
        self.cache = cache or SimpleTTLCache(default_ttl_seconds=3600)

    def is_demo_key(self) -> bool:
        """Check if provider is operating under DEMO_KEY with strict hourly limits."""
        return self.api_key == "DEMO_KEY"

    def _extract_nutrients(self, food_nutrients: list[dict[str, Any]]) -> dict[str, Optional[float]]:
        """
        Extract sugar, energy, sodium, and caffeine from USDA nutrient array.
        Preserves missing nutrients strictly as None.
        """
        sugar = None
        calories = None
        sodium = None
        caffeine = None

        for n in food_nutrients:
            # Check nutrientId or nutrientName / nutrient.name
            nid = n.get("nutrientId") or n.get("nutrient", {}).get("id")
            name = (n.get("nutrientName") or n.get("nutrient", {}).get("name") or "").lower()
            val = n.get("value") or n.get("amount")

            if val is None:
                continue

            try:
                num = float(val)
            except (ValueError, TypeError):
                continue

            # Calories / Energy (kcal)
            if nid == NUTRIENT_ID_ENERGY_KCAL or ("energy" in name and n.get("unitName", "").upper() == "KCAL"):
                calories = round(num, 2)
            # Sugars, total
            elif nid == NUTRIENT_ID_SUGARS_TOTAL or "sugars, total" in name or "total sugars" in name:
                sugar = round(num, 2)
            # Sodium (mg)
            elif nid == NUTRIENT_ID_SODIUM or "sodium" in name:
                sodium = round(num, 2)
            # Caffeine (mg)
            elif nid == NUTRIENT_ID_CAFFEINE or "caffeine" in name:
                caffeine = round(num, 2)

        return {
            "sugar": sugar,
            "calories": calories,
            "sodium": sodium,
            "caffeine": caffeine,
        }

    def _parse_product_record(self, raw_food: dict[str, Any]) -> Optional[ProductRecord]:
        """Convert raw USDA FoodData Central item into unified ProductRecord."""
        fdc_id = str(raw_food.get("fdcId") or "").strip()
        description = str(raw_food.get("description") or "").strip()
        if not fdc_id or not description:
            return None

        brand = raw_food.get("brandOwner") or raw_food.get("brandName")
        if brand:
            brand = brand.strip()

        ingredients = raw_food.get("ingredients")
        if ingredients:
            ingredients = ingredients.strip()

        # Serving size parsing
        serving_val = raw_food.get("servingSize")
        serving_unit = raw_food.get("servingSizeUnit")
        serving_raw = f"{serving_val} {serving_unit}".strip() if serving_val is not None else None

        nutrients = self._extract_nutrients(raw_food.get("foodNutrients") or [])

        # Categorize beverage type
        desc_lower = description.lower()
        if "energy" in desc_lower or "energy drink" in desc_lower:
            bev_type = NonAlcoholicCategory.ENERGY_DRINK.value
        else:
            bev_type = NonAlcoholicCategory.SOFT_DRINK.value

        # In USDA Branded foods: nutrient values are typically reported per serving or per 100g.
        # Check householdServingFullText or servingSize to standardize.
        data_type = str(raw_food.get("dataType") or "")
        is_foundation = "Foundation" in data_type or "SR Legacy" in data_type

        # Construct NutritionalValues
        nutritional_vals = NutritionalValues(
            serving_size_value=float(serving_val) if serving_val is not None else None,
            serving_size_unit=str(serving_unit).strip() if serving_unit else None,
            serving_size_raw=serving_raw,
            sugar_per_100ml=nutrients["sugar"] if is_foundation else None,
            sugar_per_serving=nutrients["sugar"] if not is_foundation else None,
            calories_per_100ml=nutrients["calories"] if is_foundation else None,
            calories_per_serving=nutrients["calories"] if not is_foundation else None,
            sodium_per_100ml=nutrients["sodium"] if is_foundation else None,
            sodium_per_serving=nutrients["sodium"] if not is_foundation else None,
            caffeine_per_100ml=nutrients["caffeine"] if is_foundation else None,
            caffeine_per_serving=nutrients["caffeine"] if not is_foundation else None,
            alcohol_percentage=0.0,
        )

        source_url = f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{fdc_id}/nutrients"

        quality_warnings = assess_product_data_quality(
            product_name=description,
            beverage_type=bev_type,
            serving_size_value=nutritional_vals.serving_size_value,
            serving_size_unit=nutritional_vals.serving_size_unit,
            sugar_per_100ml=nutritional_vals.sugar_per_100ml,
            sugar_per_serving=nutritional_vals.sugar_per_serving,
            calories_per_100ml=nutritional_vals.calories_per_100ml,
            calories_per_serving=nutritional_vals.calories_per_serving,
            sodium_per_100ml=nutritional_vals.sodium_per_100ml,
            sodium_per_serving=nutritional_vals.sodium_per_serving,
            caffeine_per_100ml=nutritional_vals.caffeine_per_100ml,
            caffeine_per_serving=nutritional_vals.caffeine_per_serving,
            ingredients=ingredients,
            is_independently_verified=is_foundation,
            source_name="USDA FoodData Central",
        )

        return ProductRecord(
            product_id=f"usda:{fdc_id}",
            product_name=description,
            brand=brand,
            beverage_type=bev_type,
            ingredients=ingredients,
            nutritional_values=nutritional_vals,
            source_name="USDA FoodData Central",
            source_url=source_url,
            retrieval_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            verification_status="independently_verified" if is_foundation else "unverified_provider_data",
            is_independently_verified=is_foundation,
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
        Search USDA FoodData Central for beverage records.
        """
        clean_category = validate_beverage_scope(beverage_type)

        cache_key = f"usda:search:{query}:{clean_category}:{page}:{page_size}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Construct query combining term and category context
        search_query = query
        if clean_category:
            search_query = f"{query} {clean_category}"

        url = f"{self.base_url}/foods/search"
        params = {
            "query": search_query,
            "dataType": ["Branded", "Foundation", "Survey (FNDDS)"],
            "pageSize": page_size,
            "pageNumber": page,
            "api_key": self.api_key,
        }

        close_client = False
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout)
            close_client = True

        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                logger.warning(
                    "USDA FoodData Central rate limit exceeded (HTTP 429). "
                    "Consider setting USDA_API_KEY environment variable for higher request limits."
                )
                return []
            if resp.status_code == 403:
                logger.warning("USDA API key invalid or unauthorized (HTTP 403).")
                return []
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException:
            logger.warning("Timeout connecting to USDA FoodData Central.")
            return []
        except (httpx.HTTPError, ValueError) as err:
            logger.warning(f"Error querying USDA FoodData Central: {err}")
            return []
        finally:
            if close_client:
                await client.aclose()

        raw_foods = data.get("foods") or []
        results: list[ProductRecord] = []
        for food in raw_foods:
            parsed = self._parse_product_record(food)
            if parsed:
                # Exclude alcoholic items if matching description
                desc = (parsed.product_name or "").lower()
                if any(alc in desc for alc in ["beer", "wine", "spirit", "liqueur", "vodka", "whiskey"]):
                    continue
                results.append(parsed)

        self.cache.set(cache_key, results)
        return results

    async def get_by_id(
        self,
        fdc_id: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Optional[ProductRecord]:
        """
        Fetch single food item by FDC ID from USDA FoodData Central.
        """
        clean_id = fdc_id.replace("usda:", "").strip()
        cache_key = f"usda:food:{clean_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/food/{clean_id}"
        params = {"api_key": self.api_key}

        close_client = False
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout)
            close_client = True

        try:
            resp = await client.get(url, params=params)
            if resp.status_code in (404, 400):
                return None
            if resp.status_code == 429:
                logger.warning("USDA FoodData Central rate limit exceeded (HTTP 429).")
                return None
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException:
            logger.warning("Timeout fetching food from USDA FoodData Central.")
            return None
        except (httpx.HTTPError, ValueError) as err:
            logger.warning(f"Error fetching from USDA FoodData Central: {err}")
            return None
        finally:
            if close_client:
                await client.aclose()

        record = self._parse_product_record(data)
        if record:
            self.cache.set(cache_key, record)
        return record
