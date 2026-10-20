"""
FastAPI route handlers for non-alcoholic beverage product search, details, and data source metadata.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.products import (
    ProductRecord,
    ProductSearchResponse,
    DataSourcesResponse,
)
from app.providers import ProductProviderManager
from app.engine.data_quality import ScopeRestrictionError

router = APIRouter(prefix="", tags=["Products & Data Sources"])

provider_manager = ProductProviderManager()


@router.get(
    "/products/search",
    response_model=ProductSearchResponse,
    summary="Search Packaged Beverage Products",
)
async def search_products(
    q: str = Query(..., min_length=1, description="Search query string for beverage name or brand"),
    beverage_type: Optional[str] = Query(
        None,
        description="Filter by beverage category. Restricted strictly to 'Soft drink' or 'Energy drink'.",
    ),
    source: Optional[str] = Query(
        "all",
        description="Data provider filter: 'all', 'open_food_facts', or 'usda'.",
    ),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
) -> ProductSearchResponse:
    """
    Search Open Food Facts and USDA FoodData Central for non-alcoholic beverages.
    
    Constraints:
    - Scoped exclusively to soft drinks and energy drinks.
    - Alcoholic beverage search (Beer, Wine, Spirits) is strictly disallowed.
    - Missing nutritional values are preserved as null.
    """
    try:
        response = await provider_manager.search_products(
            query=q,
            beverage_type=beverage_type,
            source=source,
            page=page,
            page_size=page_size,
        )
        return response
    except ScopeRestrictionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/products/{product_id}",
    response_model=ProductRecord,
    summary="Retrieve Beverage Product Details",
)
async def get_product_details(product_id: str) -> ProductRecord:
    """
    Retrieve single product record by unique identifier (e.g., 'off:049000000443' or 'usda:123456').
    """
    product = await provider_manager.get_product_by_id(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' was not found in active data providers.",
        )
    return product


@router.get(
    "/data-sources",
    response_model=DataSourcesResponse,
    summary="List Data Sources and Operational Status",
)
async def get_data_sources() -> DataSourcesResponse:
    """
    Return operational metadata, licensing, rate limits, caching policies,
    and scoring readiness of integrated external data sources.
    """
    return provider_manager.get_data_sources_info()
