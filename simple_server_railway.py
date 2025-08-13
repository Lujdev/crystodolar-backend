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
# Funciones de scraping simplificadas para Railway
# ==========================================

async def scrape_bcv_simple():
    """Scraping simplificado del BCV sin dependencias complejas"""
    try:
        import httpx
        from bs4 import BeautifulSoup
        
        # URL del BCV
        url = "http://www.bcv.org.ve/"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
        # Parsear HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar las cotizaciones (esto puede cambiar según la estructura del sitio)
        usd_element = soup.find('div', {'id': 'dolar'})
        eur_element = soup.find('div', {'id': 'euro'})
        
        usd_ves = float(usd_element.text.strip().replace(',', '.')) if usd_element else 0
        eur_ves = float(eur_element.text.strip().replace(',', '.')) if eur_element else 0
        
        return {
            "status": "success",
            "data": {
                "usd_ves": usd_ves,
                "eur_ves": eur_ves,
                "timestamp": datetime.now().isoformat(),
                "source": "BCV"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def fetch_binance_p2p_simple():
    """Consulta simplificada a Binance P2P sin dependencias complejas"""
    try:
        import httpx
        
        # URL de la API de Binance P2P
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        
        # Parámetros para USDT/VES
        params = {
            "page": 1,
            "rows": 10,
            "payTypes": [],
            "asset": "USDT",
            "tradeType": "BUY",
            "fiat": "VES",
            "publisherType": None
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=params)
            response.raise_for_status()
            
        data = response.json()
        
        if data.get("success") and data.get("data"):
            # Obtener el mejor precio
            best_price = float(data["data"][0]["adv"]["price"])
            volume_24h = sum(float(adv["adv"]["minSingleTransAmount"]) for adv in data["data"][:5])
            
            return {
                "status": "success",
                "data": {
                    "usdt_ves_buy": best_price,
                    "usdt_ves_avg": best_price,
                    "volume_24h": volume_24h,
                    "timestamp": datetime.now().isoformat(),
                    "source": "Binance P2P"
                }
            }
        else:
            return {
                "status": "error",
                "error": "No se pudieron obtener datos de Binance",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
    """Cotizaciones Binance P2P en tiempo real"""
    return await fetch_binance_p2p_simple()

@app.get("/api/v1/rates/binance-p2p/complete")
async def get_binance_p2p_complete():
    """Cotizaciones completas Binance P2P en tiempo real"""
    try:
        # Obtener datos de compra y venta
        buy_data = await fetch_binance_p2p_simple()
        
        # Para venta, cambiar el parámetro tradeType
        import httpx
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        sell_params = {
            "page": 1,
            "rows": 10,
            "payTypes": [],
            "asset": "USDT",
            "tradeType": "SELL",
            "fiat": "VES",
            "publisherType": None
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=sell_params)
            response.raise_for_status()
            
        sell_data = response.json()
        
        sell_price = 0
        if sell_data.get("success") and sell_data.get("data"):
            sell_price = float(sell_data["data"][0]["adv"]["price"])
        
        return {
            "status": "success",
            "data": {
                "buy": {
                    "price": buy_data.get("data", {}).get("usdt_ves_buy", 0),
                    "volume": buy_data.get("data", {}).get("volume_24h", 0)
                },
                "sell": {
                    "price": sell_price,
                    "volume": 0
                },
                "timestamp": datetime.now().isoformat(),
                "source": "Binance P2P"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/scrape-bcv")
async def scrape_bcv_live():
    """Scraping en tiempo real del BCV"""
    return await scrape_bcv_simple()

@app.get("/api/v1/exchanges")
async def get_exchanges():
    """Lista de exchanges disponibles"""
    return {
        "status": "success",
        "data": [
            {
                "name": "Banco Central de Venezuela",
                "code": "BCV",
                "type": "official",
                "description": "Cotizaciones oficiales del gobierno",
                "is_active": True
            },
            {
                "name": "Binance P2P",
                "code": "BINANCE_P2P",
                "type": "crypto",
                "description": "Mercado P2P de criptomonedas",
                "is_active": True
            }
        ],
        "count": 2
    }

@app.get("/api/v1/rates/compare")
async def compare_rates():
    """Comparar cotizaciones del BCV vs Binance P2P"""
    try:
        # Obtener ambas cotizaciones
        bcv_result = await scrape_bcv_simple()
        binance_result = await fetch_binance_p2p_simple()
        
        if bcv_result["status"] == "success" and binance_result["status"] == "success":
            bcv_data = bcv_result["data"]
            binance_data = binance_result["data"]
            
            # Calcular spread
            usd_bcv = bcv_data["usd_ves"]
            usdt_binance = binance_data["usdt_ves_buy"]
            
            spread = usdt_binance - usd_bcv
            spread_percentage = (spread / usd_bcv) * 100 if usd_bcv > 0 else 0
            
            return {
                "status": "success",
                "data": {
                    "bcv": {
                        "usd_ves": usd_bcv,
                        "eur_ves": bcv_data["eur_ves"],
                        "source": "BCV"
                    },
                    "binance_p2p": {
                        "usdt_ves_buy": usdt_binance,
                        "usdt_ves_avg": binance_data["usdt_ves_avg"],
                        "volume_24h": binance_data["volume_24h"],
                        "source": "Binance P2P"
                    },
                    "analysis": {
                        "spread_ves": round(spread, 4),
                        "spread_percentage": round(spread_percentage, 2),
                        "market_difference": "premium" if spread > 0 else "discount"
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "error": "No se pudieron obtener todas las cotizaciones",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
