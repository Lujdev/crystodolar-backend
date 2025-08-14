#!/usr/bin/env python3
"""
CrystoAPIVzla - Servidor Simple
FastAPI + Neon.tech PostgreSQL
Versión simplificada para testing
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncpg
from dotenv import load_dotenv
import os
from loguru import logger
from datetime import datetime
import sys

# Configurar logging a archivos
logger.remove()  # Remover configuración por defecto

# Logs a consola
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

# Logs a archivo (todos los niveles)
logger.add("logs/crystoapivzla.log", 
          format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
          rotation="1 day",  # Rotar cada día
          retention="30 days",  # Mantener 30 días
          compression="zip")  # Comprimir archivos antiguos

# Logs de errores a archivo separado
logger.add("logs/errors.log", 
          format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
          level="ERROR",  # Solo errores
          rotation="1 day",
          retention="90 days",  # Mantener errores por más tiempo
          compression="zip")

# Importar la función de scraping del BCV
from app.services.data_fetcher import (
    scrape_bcv_rates, 
    scrape_bcv_rates_no_save,  # Versión que NO guarda en BD
    fetch_binance_p2p_rates, 
    fetch_binance_p2p_sell_rates, 
    fetch_binance_p2p_complete,
    _fetch_binance_p2p_rates_no_save,  # Versión que NO guarda en BD
    _fetch_binance_p2p_sell_rates_no_save  # Versión que NO guarda en BD
)

# Cargar variables de entorno
load_dotenv()

# Crear instancia de FastAPI
app = FastAPI(
    title="CrystoAPIVzla API Simple",
    description="API simplificada para cotizaciones USDT/VES",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Variable global para la conexión
DATABASE_URL = os.getenv("DATABASE_URL")


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "CrystoAPIVzla API Simple",
        "version": "1.0.0",
        "description": "Cotizaciones USDT/VES en tiempo real",
        "sources": ["BCV", "Binance P2P"],
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check simple para Railway"""
    try:
        # Health check básico sin verificar BD
        return {
            "status": "healthy",
            "service": "crystoapivzla",
            "timestamp": datetime.now().isoformat(),
            "message": "Service is running"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/api/v1/rates/scrape-bcv")
async def scrape_bcv_live():
    """
    Hacer scraping en tiempo real del BCV
    
    Endpoint para probar el web scraping del Banco Central de Venezuela
    Retorna las cotizaciones del dólar y euro obtenidas directamente del sitio web
    """
    try:
        result = await scrape_bcv_rates()
        return result
    except Exception as e:
        logger.error(f"Error en scraping del BCV: {e}")
        raise HTTPException(status_code=500, detail=f"Error en scraping del BCV: {str(e)}")


@app.get("/api/v1/rates/binance-p2p")
async def get_binance_p2p_rates():
    """
    Consultar la API de Binance P2P para obtener precios de compra de USDT con VES
    
    Endpoint para obtener el precio de compra de USDT con VES desde Binance P2P
    Retorna el mejor precio disponible y estadísticas del mercado
    """
    try:
        result = await fetch_binance_p2p_rates()
        return result
    except Exception as e:
        logger.error(f"Error consultando Binance P2P: {e}")
        raise HTTPException(status_code=500, detail=f"Error consultando Binance P2P: {str(e)}")


@app.get("/api/v1/rates/binance-p2p/sell")
async def get_binance_p2p_sell_rates():
    """
    Consultar la API de Binance P2P para obtener precios de venta de USDT por VES
    
    Endpoint para obtener el precio de venta de USDT por VES desde Binance P2P
    Retorna el mejor precio disponible para vender USDT y recibir bolívares
    """
    try:
        result = await fetch_binance_p2p_sell_rates()
        return result
    except Exception as e:
        logger.error(f"Error consultando Binance P2P para venta: {e}")
        raise HTTPException(status_code=500, detail=f"Error consultando Binance P2P para venta: {str(e)}")


@app.get("/api/v1/rates/binance-p2p/complete")
async def get_binance_p2p_complete():
    """
    Obtener precios completos de Binance P2P (compra y venta de USDT)
    
    Endpoint para obtener tanto precios de compra como de venta de USDT/VES
    Incluye análisis de spread interno y liquidez del mercado
    """
    try:
        result = await fetch_binance_p2p_complete()
        return result
    except Exception as e:
        logger.error(f"Error obteniendo datos completos de Binance P2P: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos completos de Binance P2P: {str(e)}")


@app.get("/api/v1/rates/compare")
async def compare_rates():
    """
    Comparar cotizaciones del BCV vs Binance P2P
    
    Endpoint para comparar las cotizaciones oficiales del BCV con el mercado P2P
    Útil para calcular spreads y diferencias entre mercados
    """
    try:
        # Obtener ambas cotizaciones SIN guardar en BD (para evitar duplicados)
        bcv_result = await scrape_bcv_rates_no_save()
        binance_result = await _fetch_binance_p2p_rates_no_save()
        
        if bcv_result["status"] == "success" and binance_result["status"] == "success":
            bcv_data = bcv_result["data"]
            binance_data = binance_result["data"]
            
            # Calcular spread (diferencia entre BCV y Binance P2P)
            # Para comparar, convertimos USDT a USD (aproximadamente 1:1)
            usd_bcv = bcv_data["usd_ves"]
            usdt_binance = binance_data["usdt_ves_buy"]
            
            spread = usdt_binance - usd_bcv
            spread_percentage = (spread / usd_bcv) * 100 if usd_bcv > 0 else 0
            
            comparison = {
                "status": "success",
                "data": {
                    "bcv": {
                        "usd_ves": bcv_data["usd_ves"],
                        "eur_ves": bcv_data["eur_ves"],
                        "source": "bcv",
                        "timestamp": bcv_data["timestamp"]
                    },
                    "binance_p2p": {
                        "usdt_ves_buy": binance_data["usdt_ves_buy"],
                        "usdt_ves_avg": binance_data["usdt_ves_avg"],
                        "volume_24h": binance_data["volume_24h"],
                        "source": "binance_p2p",
                        "timestamp": binance_data["timestamp"]
                    },
                    "analysis": {
                        "spread_ves": round(spread, 4),
                        "spread_percentage": round(spread_percentage, 2),
                        "market_difference": "premium" if spread > 0 else "discount",
                        "comparison_timestamp": datetime.now().isoformat()
                    }
                }
            }
            
            logger.info(f"✅ Comparación exitosa: Spread = {spread} VES ({spread_percentage}%)")
            return comparison
        else:
            errors = []
            if bcv_result["status"] != "success":
                errors.append(f"BCV: {bcv_result.get('error', 'Error desconocido')}")
            if binance_result["status"] != "success":
                errors.append(f"Binance: {binance_result.get('error', 'Error desconocido')}")
            
            raise Exception(f"Error obteniendo cotizaciones: {'; '.join(errors)}")
            
    except Exception as e:
        logger.error(f"Error comparando cotizaciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error comparando cotizaciones: {str(e)}")


@app.get("/api/v1/rates/current")
async def get_current_rates():
    """Obtener cotizaciones actuales desde la BD"""
    logger.info("📊 Endpoint /api/v1/rates/current ejecutado")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Consultar las tablas reales: current_rates con joins a exchanges y currency_pairs
        rates = await conn.fetch("""
            SELECT 
                e.name as exchange_name,
                cr.exchange_code,
                e.type as exchange_type,
                cr.currency_pair,
                cr.buy_price,
                cr.sell_price,
                cr.variation_24h,
                cr.volume_24h,
                cr.last_update,
                cr.market_status
            FROM current_rates cr
            JOIN exchanges e ON cr.exchange_code = e.code
            JOIN currency_pairs cp ON cr.currency_pair = cp.symbol
            WHERE cr.market_status = 'active'
            ORDER BY e.type, e.name
        """)
        
        await conn.close()
        
        # Convertir a lista de diccionarios
        result = []
        for rate in rates:
            result.append({
                "exchange": {
                    "name": rate["exchange_name"],
                    "code": rate["exchange_code"], 
                    "type": rate["exchange_type"]
                },
                "pair": rate["currency_pair"],
                "prices": {
                    "buy": float(rate["buy_price"]) if rate["buy_price"] else None,
                    "sell": float(rate["sell_price"]) if rate["sell_price"] else None,
                },
                "variation_24h": float(rate["variation_24h"]) if rate["variation_24h"] else 0,
                "volume_24h": float(rate["volume_24h"]) if rate["volume_24h"] else 0,
                "last_update": rate["last_update"],
                "market_status": rate["market_status"]
            })
            
        return {
            "status": "success",
            "data": result,
            "count": len(result),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting current rates: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting rates: {e}")


@app.get("/api/v1/rates/history")
async def get_all_rate_history(limit: int = 100):
    """Obtener histórico general de todas las cotizaciones"""
    logger.info(f"📊 Endpoint /api/v1/rates/history ejecutado con limit={limit}")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Consultar histórico desde rate_history con joins para obtener nombres
        history = await conn.fetch("""
            SELECT 
                rh.buy_price,
                rh.sell_price,
                rh.avg_price,
                rh.volume,
                rh.timestamp,
                e.name as exchange_name,
                e.code as exchange_code,
                cp.symbol as currency_pair,
                cp.base_currency,
                cp.quote_currency
            FROM rate_history rh
            JOIN exchanges e ON rh.exchange_code = e.code
            JOIN currency_pairs cp ON rh.currency_pair = cp.symbol
            ORDER BY rh.timestamp DESC
            LIMIT $1
        """, limit)
        
        await conn.close()
        
        # Convertir a lista
        result = []
        for record in history:
            result.append({
                "buy_price": float(record["buy_price"]) if record["buy_price"] else None,
                "sell_price": float(record["sell_price"]) if record["sell_price"] else None,
                "avg_price": float(record["avg_price"]) if record["avg_price"] else None,
                "volume": float(record["volume"]) if record["volume"] else None,
                "timestamp": record["timestamp"],
                "exchange_name": record["exchange_name"],
                "exchange_code": record["exchange_code"],
                "currency_pair": record["currency_pair"],
                "base_currency": record["base_currency"],
                "quote_currency": record["quote_currency"]
            })
            
        return {
            "status": "success",
            "data": result,
            "count": len(result),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting history: {e}")


@app.get("/api/v1/rates/history/{exchange_code}/{pair}")
async def get_rate_history_by_exchange(exchange_code: str, pair: str, limit: int = 100):
    """Obtener histórico de cotizaciones por exchange y par específico"""
    logger.info(f"📊 Endpoint /api/v1/rates/history/{exchange_code}/{pair} ejecutado con limit={limit}")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Consultar histórico desde rate_history
        history = await conn.fetch("""
            SELECT 
                buy_price,
                sell_price,
                avg_price,
                volume,
                timestamp
            FROM rate_history
            WHERE exchange_code = $1 AND currency_pair = $2
            ORDER BY timestamp DESC
            LIMIT $3
        """, exchange_code, pair, limit)
        
        await conn.close()
        
        # Convertir a lista
        result = []
        for record in history:
            result.append({
                "buy_price": float(record["buy_price"]) if record["buy_price"] else None,
                "sell_price": float(record["sell_price"]) if record["sell_price"] else None,
                "avg_price": float(record["avg_price"]) if record["avg_price"] else None,
                "volume": float(record["volume"]) if record["volume"] else None,
                "timestamp": record["timestamp"]
            })
            
        return {
            "status": "success",
            "data": result,
            "count": len(result),
            "exchange": exchange_code,
            "pair": pair
        }
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting history: {e}")


@app.get("/api/v1/exchanges")
async def get_exchanges():
    """Obtener lista de exchanges disponibles"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        exchanges = await conn.fetch("""
            SELECT 
                name, 
                code, 
                type, 
                description, 
                is_active,
                operating_hours,
                update_frequency
            FROM exchanges
            WHERE is_active = true
            ORDER BY type, name
        """)
        
        await conn.close()
        
        result = []
        for exchange in exchanges:
            result.append({
                "name": exchange["name"],
                "code": exchange["code"],
                "type": exchange["type"],
                "description": exchange["description"],
                "is_active": exchange["is_active"],
                "operating_hours": exchange["operating_hours"],
                "update_frequency": exchange["update_frequency"]
            })
            
        return {
            "status": "success",
            "data": result,
            "count": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting exchanges: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting exchanges: {e}")


@app.get("/api/v1/database/stats")
async def get_database_stats():
    """Estadísticas de la base de datos"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Contar registros en cada tabla
        stats = {}
        tables = ["exchanges", "currency_pairs", "current_rates", "rate_history", "api_logs"]
        
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            stats[table] = count
            
        # Info adicional
        db_info = await conn.fetchrow("""
            SELECT 
                current_database() as database,
                current_user as user,
                version() as postgres_version
        """)
        
        await conn.close()
        
        return {
            "status": "success",
            "database_info": {
                "database": db_info["database"],
                "user": db_info["user"],
                "postgres_version": db_info["postgres_version"][:100]
            },
            "table_counts": stats,
            "total_records": sum(stats.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting database stats: {e}")


if __name__ == "__main__":
    """Ejecutar servidor"""
    logger.info("🚀 Iniciando CrystoAPIVzla Simple Server...")
    logger.info(f"📊 Database URL: {DATABASE_URL[:50]}...")
    
    # Usar variable de entorno PORT para Railway, o 8000 por defecto
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # False para producción
        log_level="info"
    )
