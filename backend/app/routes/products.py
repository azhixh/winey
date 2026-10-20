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
from app.engine.scoring_engine import load_reference_ranges

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


@router.get(
    "/product-search",
    response_model=ProductSearchResponse,
    summary="Search Packaged Beverage Products (Alias for /products/search)",
)
async def product_search_alias(
    q: str = Query(..., min_length=1, description="Search query string for beverage name or brand"),
    beverage_type: Optional[str] = Query(None),
    source: Optional[str] = Query("all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
) -> ProductSearchResponse:
    """Search beverage products across Open Food Facts and USDA FoodData Central."""
    return await search_products(q=q, beverage_type=beverage_type, source=source, page=page, page_size=page_size)


@router.get(
    "/product/{barcode}",
    response_model=ProductRecord,
    summary="Retrieve Beverage Product by Barcode",
)
async def get_product_by_barcode(barcode: str) -> ProductRecord:
    """
    Retrieve product by numerical barcode (e.g., '049000000443' or 'off:049000000443').
    """
    clean_barcode = barcode.strip()
    product_id = clean_barcode if clean_barcode.startswith(("off:", "usda:")) else f"off:{clean_barcode}"
    product = await provider_manager.get_product_by_id(product_id)
    if product is None:
        clean_code = clean_barcode.replace("off:", "").replace("usda:", "").strip()
        product = await provider_manager.open_food_facts.get_product_by_barcode(clean_code)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with barcode '{barcode}' was not found in active data providers.",
        )
    return product


@router.get(
    "/reference/{category}",
    summary="Retrieve Benchmark Ranges and Percentiles for Beverage Category",
)
async def get_category_reference(category: str):
    """
    Retrieve benchmark ranges, percentiles, sample sizes, and dataset metadata for a given category.
    Supported category identifiers:
    - soft-drinks / Soft drink
    - beer / Beer
    - energy-drinks / Energy drink
    - wine / Wine / Wine_red / Wine_white
    - alcohol / Spirits / Alcohol
    """
    data = load_reference_ranges()
    categories_dict = data.get("categories", {})

    clean = category.strip().lower().replace("_", "-").replace(" ", "-")
    cat_key = None
    if clean in ("soft-drinks", "soft-drink", "softdrink"):
        cat_key = "Soft drink"
    elif clean in ("beer", "beers", "beer-ales"):
        cat_key = "Beer"
    elif clean in ("energy-drinks", "energy-drink", "energydrink"):
        cat_key = "Energy drink"
    elif clean in ("wine-red", "red-wine"):
        cat_key = "Wine_red"
    elif clean in ("wine-white", "white-wine"):
        cat_key = "Wine_white"
    elif clean in ("wine", "wines"):
        cat_key = "Wine_red"
    elif clean in ("alcohol", "spirits", "liquor", "distilled"):
        cat_key = "Alcohol"
    elif category in categories_dict:
        cat_key = category

    if not cat_key or cat_key not in categories_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference benchmarks for category '{category}' not found.",
        )

    return {
        "category": cat_key,
        "dataset_version": data.get("dataset_version", "1.0.0"),
        "generated_at": data.get("generated_at", "2026-10-20"),
        "benchmarks": categories_dict[cat_key],
    }
