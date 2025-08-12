"""
API v1 Router
Endpoints para CrystoDolar
"""

from fastapi import APIRouter
from app.api.v1.endpoints import rates, health, admin

api_router = APIRouter()

# Incluir todos los endpoints
api_router.include_router(rates.router, prefix="/rates", tags=["Cotizaciones"])
api_router.include_router(health.router, prefix="/health", tags=["Monitoreo"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administración"])
