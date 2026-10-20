"""
Nutritional data providers layer for BQAS backend.
Integrates Open Food Facts and USDA FoodData Central for non-alcoholic beverages.
"""

from typing import Optional, Any
import httpx
from .cache import SimpleTTLCache
from .open_food_facts import OpenFoodFactsProvider
from .usda_food_data import USDAFoodDataProvider
from app.schemas.products import (
    ProductRecord,
    ProductSearchResponse,
    DataSourceInfo,
    DataSourcesResponse,
)
from app.engine.data_quality import validate_beverage_scope, ScopeRestrictionError


class ProductProviderManager:
    """
    Unified coordinator for external nutritional product data sources.
    Keeps provider records separate unless exact barcode identity and unit matching can be verified.
    """

    def __init__(
        self,
        off_provider: Optional[OpenFoodFactsProvider] = None,
        usda_provider: Optional[USDAFoodDataProvider] = None,
        cache: Optional[SimpleTTLCache] = None,
    ):
        shared_cache = cache or SimpleTTLCache(default_ttl_seconds=3600)
        self.off = off_provider or OpenFoodFactsProvider(cache=shared_cache)
        self.usda = usda_provider or USDAFoodDataProvider(cache=shared_cache)
        self.cache = shared_cache

    async def search_products(
        self,
        query: str,
        beverage_type: Optional[str] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        client: Optional[httpx.AsyncClient] = None,
    ) -> ProductSearchResponse:
        """
        Search across active providers with non-alcoholic scope filtering.
        """
        # Validates scope - raises ScopeRestrictionError if alcoholic beverage is requested
        clean_category = validate_beverage_scope(beverage_type)

        results: list[ProductRecord] = []
        warnings: list[str] = []

        clean_source = (source or "all").strip().lower()

        # Query Open Food Facts
        if clean_source in ("all", "off", "open_food_facts", "openfoodfacts"):
            try:
                off_results = await self.off.search(
                    query=query,
                    beverage_type=clean_category,
                    page=page,
                    page_size=page_size,
                    client=client,
                )
                results.extend(off_results)
            except Exception as e:
                warnings.append(f"Open Food Facts search encountered an error: {str(e)}")

        # Query USDA FoodData Central
        if clean_source in ("all", "usda", "usda_food_data", "fdc"):
            try:
                usda_results = await self.usda.search(
                    query=query,
                    beverage_type=clean_category,
                    page=page,
                    page_size=page_size,
                    client=client,
                )
                results.extend(usda_results)
            except Exception as e:
                warnings.append(f"USDA FoodData Central search encountered an error: {str(e)}")

        if self.usda.is_demo_key() and clean_source in ("all", "usda"):
            warnings.append(
                "USDA FoodData Central is operating under default DEMO_KEY with strict hourly limits. Set USDA_API_KEY environment variable for higher quotas."
            )

        # Slice results to page size
        total_found = len(results)
        paginated_results = results[:page_size]

        return ProductSearchResponse(
            query=query,
            beverage_type_filter=clean_category,
            source_filter=source,
            total_results=total_found,
            page=page,
            page_size=page_size,
            results=paginated_results,
            warnings=warnings,
        )

    async def get_product_by_id(
        self,
        product_id: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Optional[ProductRecord]:
        """
        Retrieve single product by unique ID (e.g. 'off:049000000443' or 'usda:123456').
        """
        clean_id = product_id.strip()

        if clean_id.startswith("off:"):
            return await self.off.get_by_id(clean_id, client=client)
        elif clean_id.startswith("usda:"):
            return await self.usda.get_by_id(clean_id, client=client)
        else:
            # Attempt OFF first (numeric barcodes), then USDA
            off_res = await self.off.get_by_id(clean_id, client=client)
            if off_res:
                return off_res
            return await self.usda.get_by_id(clean_id, client=client)

    def get_data_sources_info(self) -> DataSourcesResponse:
        """
        Return operational status, licensing, and scoring readiness of data providers.
        """
        usda_auth_status = "Custom API Key Configured" if not self.usda.is_demo_key() else "Default DEMO_KEY (Low Rate Limit)"

        sources = [
            DataSourceInfo(
                source_name="Open Food Facts",
                provider_key="open_food_facts",
                api_endpoint="https://world.openfoodfacts.org",
                auth_type="None (Public API with User-Agent Identification)",
                auth_status="Operational",
                rate_limits="Standard community rate limit (~1-2 req/sec)",
                supported_beverage_types=["Soft drink", "Energy drink"],
                license_or_terms="Open Database License (ODbL) / Database Contents License (DbCL)",
                caching_policy="In-memory TTL cache (3600 seconds / 1 hour)",
                notes="Community-contributed commercial product data. Values are manufacturer-declared and unverified by independent lab testing.",
            ),
            DataSourceInfo(
                source_name="USDA FoodData Central",
                provider_key="usda",
                api_endpoint="https://api.nal.usda.gov/fdc/v1",
                auth_type="API Key query parameter (via USDA_API_KEY environment variable)",
                auth_status=usda_auth_status,
                rate_limits="DEMO_KEY: 30 requests/hour, 50 requests/day; Registered Key: 1,000 requests/hour",
                supported_beverage_types=["Soft drink", "Energy drink"],
                license_or_terms="U.S. Public Domain / National Agricultural Library",
                caching_policy="In-memory TTL cache (3600 seconds / 1 hour)",
                notes="Contains Branded food submissions and Foundation/SR Legacy analytical data.",
            ),
        ]

        scoring_readiness = {
            "composition_score_status": "unavailable",
            "health_impact_score_status": "unavailable",
            "explanation": (
                "Composition Score requires at least 100 quality-checked records per beverage type. "
                "Current product endpoints provide exploratory individual product lookups. "
                "Aggregated reference datasets have not yet reached the 100-record threshold per category. "
                "Health Impact Score remains unavailable until consensus clinical guidelines and evidence rubrics are integrated."
            ),
            "sample_size_requirement": 100,
            "current_soft_drinks_reference_samples": 0,
            "current_energy_drinks_reference_samples": 0,
        }

        return DataSourcesResponse(
            supported_categories=["Soft drink", "Energy drink"],
            disallowed_categories=["Beer", "Wine", "Spirits"],
            data_sources=sources,
            scoring_readiness=scoring_readiness,
        )


__all__ = [
    "SimpleTTLCache",
    "OpenFoodFactsProvider",
    "USDAFoodDataProvider",
    "ProductProviderManager",
]
