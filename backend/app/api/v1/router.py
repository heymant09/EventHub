from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.registrations import router as registrations_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.reviews import router as reviews_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(events_router)
router.include_router(registrations_router)
router.include_router(categories_router)
router.include_router(reviews_router)