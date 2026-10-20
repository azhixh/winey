"""
API route modules for BQAS backend.
"""

from .health import router as health_router
from .beverages import router as beverages_router
from .products import router as products_router
from .wine import router as wine_router
from .scoring import router as scoring_router

__all__ = ["health_router", "beverages_router", "products_router", "wine_router", "scoring_router"]

