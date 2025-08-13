#!/usr/bin/env python3
"""
CrystoDolar - Servidor Simple para Railway
Versión simplificada sin dependencias complejas
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from datetime import datetime
import sys

# Crear instancia de FastAPI
app = FastAPI(
    title="CrystoDolar API Simple",
    description="API simplificada para cotizaciones USDT/VES",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes en producción
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "CrystoDolar API Simple",
        "version": "1.0.0",
        "description": "Cotizaciones USDT/VES en tiempo real",
        "sources": ["BCV", "Binance P2P"],
        "docs": "/docs",
        "status": "operational",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/health")
async def health_check():
    """Health check simple para Railway"""
    try:
        return {
            "status": "healthy",
            "service": "crystodolar-backend",
            "timestamp": datetime.now().isoformat(),
            "message": "Service is running",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "database_url": os.getenv("DATABASE_URL", "not_configured")[:50] + "..." if os.getenv("DATABASE_URL") else "not_configured"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/status")
async def get_status():
    """Endpoint de estado del sistema"""
    return {
        "status": "success",
        "data": {
            "service": "crystodolar-backend",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "database_configured": bool(os.getenv("DATABASE_URL")),
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/api/v1/config")
async def get_config():
    """Endpoint para ver configuración (sin secretos)"""
    return {
        "status": "success",
        "data": {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "api_debug": os.getenv("API_DEBUG", "false"),
            "scheduler_enabled": os.getenv("SCHEDULER_ENABLED", "true"),
            "redis_enabled": os.getenv("REDIS_ENABLED", "false"),
            "bcv_api_url": os.getenv("BCV_API_URL", "not_configured"),
            "binance_api_url": os.getenv("BINANCE_API_URL", "not_configured")
        }
    }

# ==========================================
# API Endpoints para Railway
# ==========================================

@app.get("/api/v1/rates/current")
async def get_current_rates():
    """Obtener cotizaciones actuales (placeholder para Railway)"""
    return {
        "status": "success",
        "message": "Endpoint en desarrollo para Railway",
        "data": [],
        "count": 0,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/rates/history")
async def get_all_rate_history(limit: int = 100):
    """Obtener histórico general (placeholder para Railway)"""
    return {
        "status": "success",
        "message": "Endpoint en desarrollo para Railway",
        "data": [],
        "count": 0,
        "limit": limit,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/rates/binance-p2p")
async def get_binance_p2p_rates():
    """Cotizaciones Binance P2P (placeholder para Railway)"""
    return {
        "status": "success",
        "message": "Endpoint en desarrollo para Railway",
        "data": {
            "usdt_ves_buy": 0,
            "usdt_ves_sell": 0,
            "volume_24h": 0,
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/api/v1/rates/binance-p2p/complete")
async def get_binance_p2p_complete():
    """Cotizaciones completas Binance P2P (placeholder para Railway)"""
    return {
        "status": "success",
        "message": "Endpoint en desarrollo para Railway",
        "data": {
            "buy": {"price": 0, "volume": 0},
            "sell": {"price": 0, "volume": 0},
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/api/v1/rates/scrape-bcv")
async def scrape_bcv_live():
    """Scraping BCV (placeholder para Railway)"""
    return {
        "status": "success",
        "message": "Endpoint en desarrollo para Railway",
        "data": {
            "usd_ves": 0,
            "eur_ves": 0,
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/api/v1/exchanges")
async def get_exchanges():
    """Lista de exchanges (placeholder para Railway)"""
    return {
        "status": "success",
        "message": "Endpoint en desarrollo para Railway",
        "data": [],
        "count": 0
    }

if __name__ == "__main__":
    """Ejecutar servidor"""
    print("🚀 Iniciando CrystoDolar Simple Server para Railway...")
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"📊 Database URL: {os.getenv('DATABASE_URL', 'not_configured')[:50]}..." if os.getenv("DATABASE_URL") else "📊 Database URL: not_configured")
    
    # Usar variable de entorno PORT para Railway, o 8000 por defecto
    port = int(os.getenv("PORT", 8000))
    
    print(f"🌐 Host: 0.0.0.0")
    print(f"🔌 Port: {port}")
    
    uvicorn.run(
        "simple_server_railway:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # False para producción
        log_level="info"
    )
