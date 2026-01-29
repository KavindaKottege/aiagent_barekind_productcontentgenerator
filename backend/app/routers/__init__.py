from app.routers.auth import router as auth_router
from app.routers.clients import router as clients_router
from app.routers.debug import router as debug_router
from app.routers.export import router as export_router
from app.routers.generation import router as generation_router
from app.routers.products import router as products_router
from app.routers.regeneration import router as regeneration_router
from app.routers.review import router as review_router
from app.routers.settings import router as settings_router

__all__ = [
    "auth_router",
    "settings_router",
    "clients_router",
    "products_router",
    "generation_router",
    "review_router",
    "regeneration_router",
    "export_router",
    "debug_router",
]
