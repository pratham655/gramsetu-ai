from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.eligibility import router as eligibility_router
from app.api.v1.kagazcheck import router as kagazcheck_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(eligibility_router)
api_router.include_router(kagazcheck_router)
