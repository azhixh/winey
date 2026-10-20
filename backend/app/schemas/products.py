"""
Pydantic schemas for packaged beverage products, nutritional providers, and data sources.
Scoped exclusively to non-alcoholic beverages: Soft drinks and Energy drinks.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class NonAlcoholicCategory(str, Enum):
    """
    Non-alcoholic beverage categories supported by Step 3 product providers.
    """
    SOFT_DRINK = "Soft drink"
    ENERGY_DRINK = "Energy drink"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            clean_val = value.strip().lower()
            for member in cls:
                if member.value.lower() == clean_val:
                    return member
        return None


class NutritionalValues(BaseModel):
    """
    Normalized nutritional values per 100 mL and per serving.
    Preserves missing values as null (never defaults to zero).
    """
    serving_size_value: Optional[float] = Field(default=None, description="Parsed serving size volume/mass")
    serving_size_unit: Optional[str] = Field(default=None, description="Serving size unit (e.g., mL, fl oz, g)")
    serving_size_raw: Optional[str] = Field(default=None, description="Raw unparsed serving size text from provider")

    sugar_per_100ml: Optional[float] = Field(default=None, description="Sugar content in grams per 100 mL (g/100 mL)")
    sugar_per_serving: Optional[float] = Field(default=None, description="Sugar content in grams per serving (g)")

    calories_per_100ml: Optional[float] = Field(default=None, description="Energy in kcal per 100 mL")
    calories_per_serving: Optional[float] = Field(default=None, description="Energy in kcal per serving")

    sodium_per_100ml: Optional[float] = Field(default=None, description="Sodium content in mg per 100 mL")
    sodium_per_serving: Optional[float] = Field(default=None, description="Sodium content in mg per serving")

    caffeine_per_100ml: Optional[float] = Field(default=None, description="Caffeine content in mg per 100 mL")
    caffeine_per_serving: Optional[float] = Field(default=None, description="Caffeine content in mg per serving")

    alcohol_percentage: Optional[float] = Field(default=None, description="ABV percentage (strictly null or 0.0 for non-alcoholic)")

    units: dict[str, str] = Field(
        default_factory=lambda: {
            "sugar": "g",
            "calories": "kcal",
            "sodium": "mg",
            "caffeine": "mg",
            "alcohol": "%",
        },
        description="Standard measurement units for nutritional values",
    )


class ProductRecord(BaseModel):
    """
    Standardized product record retrieved from a nutritional provider.
    Clearly distinguishes provider-supplied information from independently verified data.
    """
    product_id: str = Field(..., description="Unique product identifier (e.g., 'off:049000000443' or 'usda:123456')")
    product_name: str = Field(..., description="Product commercial name")
    brand: Optional[str] = Field(default=None, description="Brand name or manufacturer")
    beverage_type: Optional[str] = Field(default=None, description="Categorized beverage type (Soft drink or Energy drink)")
    ingredients: Optional[str] = Field(default=None, description="Ingredients list text if provided by source")
    nutritional_values: NutritionalValues = Field(..., description="Normalized nutritional metrics")
    source_name: str = Field(..., description="Provider source name (e.g. 'Open Food Facts', 'USDA FoodData Central')")
    source_url: Optional[str] = Field(default=None, description="Direct URL to product record at the provider")
    retrieval_timestamp: str = Field(..., description="ISO 8601 UTC timestamp of retrieval")
    verification_status: str = Field(
        default="unverified_provider_data",
        description="Verification state of the data ('unverified_provider_data' vs 'independently_verified')",
    )
    is_independently_verified: bool = Field(
        default=False,
        description="Whether values were confirmed through third-party laboratory verification",
    )
    data_quality_warnings: list[str] = Field(
        default_factory=list,
        description="Data quality notices (e.g., missing nutrients, unverified claims, missing serving size)",
    )


class ProductSearchResponse(BaseModel):
    """
    Paginated search response for non-alcoholic beverage products.
    """
    query: str = Field(..., description="Original search query text")
    beverage_type_filter: Optional[str] = Field(default=None, description="Applied beverage type filter")
    source_filter: Optional[str] = Field(default=None, description="Applied data source filter")
    total_results: int = Field(..., description="Total count of products matching query")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=10, description="Items per page")
    results: list[ProductRecord] = Field(default_factory=list, description="List of matching product records")
    warnings: list[str] = Field(default_factory=list, description="General or provider-specific warnings")


class DataSourceInfo(BaseModel):
    """
    Metadata, license, and operational details for an integrated data provider.
    """
    source_name: str = Field(..., description="Provider name")
    provider_key: str = Field(..., description="Internal provider identifier ('open_food_facts', 'usda')")
    api_endpoint: str = Field(..., description="Base API endpoint URL")
    auth_type: str = Field(..., description="Authentication mechanism")
    auth_status: str = Field(..., description="Operational status of authentication")
    rate_limits: str = Field(..., description="Provider rate limit guidelines")
    supported_beverage_types: list[str] = Field(..., description="Categories supported (Soft drink, Energy drink)")
    license_or_terms: str = Field(..., description="Data license and terms of use")
    caching_policy: str = Field(..., description="Cache TTL and expiration policy")
    notes: str = Field(..., description="Operational considerations and constraints")


class DataSourcesResponse(BaseModel):
    """
    Overview of active data sources, scope limitations, and scoring readiness.
    """
    supported_categories: list[str] = Field(
        default=["Soft drink", "Energy drink"],
        description="Beverage categories supported for product search and nutritional retrieval",
    )
    disallowed_categories: list[str] = Field(
        default=["Beer", "Wine", "Spirits"],
        description="Beverage categories explicitly excluded from external product lookup",
    )
    data_sources: list[DataSourceInfo] = Field(..., description="List of integrated nutritional data providers")
    scoring_readiness: dict[str, Any] = Field(
        ...,
        description="Explanation of why composition_score and health_impact_score remain unavailable",
    )
