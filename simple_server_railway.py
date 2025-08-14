#!/usr/bin/env python3
"""
CrystoAPIVzla - Servidor Simple para Railway
Versión de PRODUCCIÓN - Optimizada y segura

API para cotizaciones USDT/VES en tiempo real con guardado automático en rate_history.
Endpoints principales: /rates/current, /rates/summary, /rates/compare

Copyright 2024 CrystoAPIVzla Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
import warnings
import ssl
from datetime import datetime
from typing import Optional, Dict, Any, List

import asyncpg
from asyncpg.connect_utils import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.services.database_service import DatabaseService

# ==========================================
# Configuración y constantes
# ==========================================

# Configuración de la aplicación
APP_CONFIG = {
    "title": "CrystoAPIVzla API Simple",
    "description": "API simplificada para cotizaciones USDT/VES",
    "version": "1.0.0",
    "docs_url": "/docs",
    "redoc_url": "/redoc"
}

# Configuración de CORS
CORS_CONFIG = {
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE"],
    "allow_headers": ["*"]
}

# Configuración de URLs
BCV_URLS = [
    "https://www.bcv.org.ve/",
    "http://www.bcv.org.ve/"
]

# Configuración de selectores para scraping
USD_SELECTORS = [
    'div[id="dolar"]',
    'div[class*="dolar"]',
    'span[id="dolar"]',
    'span[class*="dolar"]',
    'div:-soup-contains("USD")',
    'span:-soup-contains("USD")'
]

EUR_SELECTORS = [
    'div[id="euro"]',
    'div[class*="euro"]',
    'span[id="euro"]',
    'span[class*="euro"]',
    'div:-soup-contains("EUR")',
    'span:-soup-contains("EUR")'
]

# Configuración de patrones regex
USD_PATTERNS = [
    r'USD[:\s]*([\d,]+\.?\d*)',
    r'Dólar[:\s]*([\d,]+\.?\d*)',
    r'DOLAR[:\s]*([\d,]+\.?\d*)'
]

EUR_PATTERNS = [
    r'EUR[:\s]*([\d,]+\.?\d*)',
    r'Euro[:\s]*([\d,]+\.?\d*)',
    r'EURO[:\s]*([\d,]+\.?\d*)'
]

# ==========================================
# Carga de variables de entorno
# ==========================================

def load_environment():
    """Cargar variables de entorno desde .env."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Archivo .env cargado correctamente")
    except ImportError:
        print("⚠️ python-dotenv no disponible - usando variables de entorno del sistema")
        _load_env_manually()

def _load_env_manually():
    """Carga manual del archivo .env como fallback."""
    try:
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
            print("✅ Archivo .env cargado manualmente")
    except Exception as e:
        print(f"⚠️ No se pudo cargar .env manualmente: {e}")

# Cargar variables de entorno
load_environment()

# ==========================================
# Variables globales y verificación de dependencias
# ==========================================

# Variables globales para disponibilidad de dependencias
DATABASE_AVAILABLE = False
ASYNCPG_AVAILABLE = False
DATABASE_URL = None

def check_dependencies():
    """Verificar disponibilidad de dependencias."""
    global DATABASE_AVAILABLE, ASYNCPG_AVAILABLE, DATABASE_URL
    
    # Verificar DatabaseService
    try:
        from app.services.database_service import DatabaseService
        from app.core.database import get_db_session
        DATABASE_AVAILABLE = True
        print("✅ DatabaseService disponible")
    except ImportError:
        print("⚠️ DatabaseService no disponible - funcionando sin persistencia")
        DATABASE_AVAILABLE = False

    # Verificar asyncpg
    try:
        import asyncpg
        ASYNCPG_AVAILABLE = True
        print("✅ asyncpg disponible")
    except ImportError:
        print("⚠️ asyncpg no disponible - variaciones se calcularán sin BD")
        ASYNCPG_AVAILABLE = False

    # Obtener DATABASE_URL
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        # Ocultar información sensible en producción
        if os.getenv("ENVIRONMENT", "development") == "production":
            print("✅ DATABASE_URL configurado (información oculta en producción)")
        else:
            print(f"✅ DATABASE_URL configurado: {DATABASE_URL[:20]}..." if len(DATABASE_URL) > 20 else f"✅ DATABASE_URL configurado: {DATABASE_URL}")
    else:
        print("⚠️ DATABASE_URL no configurado - verificar archivo .env")

# Verificar dependencias
check_dependencies()

# ==========================================
# Funciones de utilidad
# ==========================================

async def check_rate_changed(exchange_code: str, currency_pair: str, new_price: float, tolerance: float = 0.0001) -> bool:
    """Verificar si una tasa cambió significativamente para evitar duplicados."""
    if not DATABASE_AVAILABLE:
        return True  # Si no hay BD, siempre insertar
    
    try:
        current_rates = await DatabaseService.get_current_rates()
        
        for rate in current_rates:
            if rate["exchange_code"].upper() == exchange_code.upper() and rate["currency_pair"] == currency_pair:
                # Para Binance P2P, comparar con el precio más cercano (buy o sell)
                # LÓGICA ESPECIAL: Como Binance P2P tiene dos precios diferentes,
                # comparamos el nuevo precio con ambos precios existentes y usamos
                # la diferencia más pequeña para determinar si hay cambios significativos
                if exchange_code.upper() == "BINANCE_P2P":
                    current_buy = rate.get("buy_price", 0)
                    current_sell = rate.get("sell_price", 0)
                    
                    # Calcular diferencias con ambos precios
                    buy_diff = abs(new_price - current_buy) / current_buy if current_buy > 0 else 1
                    sell_diff = abs(new_price - current_sell) / current_sell if current_sell > 0 else 1
                    
                    # Usar la diferencia más pequeña para determinar si hay cambios
                    # Esto evita insertar cuando el nuevo precio está dentro del rango existente
                    min_diff = min(buy_diff, sell_diff) if current_buy > 0 and current_sell > 0 else max(buy_diff, sell_diff)
                    
                    if min_diff > tolerance:
                        print(f"🔄 Tasa cambió: {exchange_code} {currency_pair}")
                        print(f"   Precio anterior: Buy={current_buy}, Sell={current_sell}")
                        print(f"   Nuevo precio: {new_price}")
                        print(f"   Diferencia mínima: {min_diff*100:.2f}% (tolerancia: {tolerance*100}%)")
                        return True
                    else:
                        print(f"✅ Tasa sin cambios: {exchange_code} {currency_pair} (tolerancia: {tolerance*100}%)")
                        print(f"   Precio anterior: Buy={current_buy}, Sell={current_sell}")
                        print(f"   Nuevo precio: {new_price}")
                        print(f"   Diferencia mínima: {min_diff*100:.2f}%")
                        return False
                else:
                    # Para otros exchanges (BCV, etc.), usar lógica simple
                    current_price = rate.get("avg_price", rate.get("buy_price", 0))
                    
                    if current_price > 0:
                        price_diff = abs(new_price - current_price) / current_price
                        
                        if price_diff > tolerance:
                            print(f"🔄 Tasa cambió: {exchange_code} {currency_pair}")
                            print(f"   Precio anterior: {current_price} → Nuevo: {new_price}")
                            print(f"   Diferencia: {price_diff*100:.2f}% (tolerancia: {tolerance*100}%)")
                            return True
                        else:
                            print(f"✅ Tasa sin cambios: {exchange_code} {currency_pair} (tolerancia: {tolerance*100}%)")
                            print(f"   Precio anterior: {current_price} → Nuevo: {new_price}")
                            print(f"   Diferencia: {price_diff*100:.2f}%")
                            return False
                    else:
                        # Si no hay precio anterior, insertar
                        print(f"🆕 Nueva tasa sin precio anterior: {exchange_code} {currency_pair}")
                        return True
        
        # Si no existe en current_rates, insertar
        print(f"🆕 Nueva tasa: {exchange_code} {currency_pair}")
        return True
        
    except Exception as e:
        print(f"⚠️ Error verificando cambios de tasa: {e}")
        return True  # En caso de error, insertar por seguridad

# ==========================================
# Configuración de advertencias
# ==========================================

# Suprimir advertencias de SSL para Railway
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# ==========================================
# Funciones de utilidad
# ==========================================

def create_response(status: str, data: Any = None, error: str = None, **kwargs) -> Dict[str, Any]:
    """Crear respuesta estándar para la API."""
    response = {
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    
    # Agregar campos adicionales
    response.update(kwargs)
    
    return response

# ==========================================
# Crear instancia de FastAPI
# ==========================================

app = FastAPI(**APP_CONFIG)

# CORS
app.add_middleware(
    CORSMiddleware,
    **CORS_CONFIG
)

# ==========================================
# Endpoints de la API
# ==========================================

@app.get("/")
async def root():
    """Endpoint raíz de la API."""
    return create_response(
        status="success",
        data={
            "message": "CrystoAPIVzla API Simple",
            "version": "1.0.0",
            "description": "Cotizaciones USDT/VES en tiempo real",
            "sources": ["BCV", "Binance P2P"],
            "docs": "/docs",
            "status": "operational",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    )

@app.get("/health")
async def health_check():
    """Health check para Railway."""
    try:
        return create_response(
            status="success",
            data={
                "status": "healthy",
                "service": "crystoapivzla",
                "message": "Service is running",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "database_url": "configured" if os.getenv("DATABASE_URL") else "not_configured"
            }
        )
    except Exception as e:
        return create_response(
            status="error",
            error=str(e)
        )

@app.get("/api/v1/status")
async def get_status():
    """Estado del sistema."""
    return create_response(
        status="success",
        data={
            "service": "crystoapivzla",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "database_configured": bool(os.getenv("DATABASE_URL"))
        }
    )

@app.get("/api/v1/config")
async def get_config():
    """Configuración del sistema (sin secretos)."""
    return create_response(
        status="success",
        data={
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "api_debug": os.getenv("API_DEBUG", "false"),
            "scheduler_enabled": os.getenv("SCHEDULER_ENABLED", "true"),
            "redis_enabled": os.getenv("REDIS_ENABLED", "false"),
            "bcv_api_url": os.getenv("BCV_API_URL", "not_configured"),
            "binance_api_url": os.getenv("BINANCE_API_URL", "not_configured")
        }
    )

# ==========================================
# ENDPOINTS DE DEBUG ELIMINADOS PARA PRODUCCIÓN
# ==========================================
# Los siguientes endpoints fueron eliminados para mantener la seguridad en producción:
# - /api/v1/debug/bcv
# - /api/v1/debug/database-check  
# - /api/v1/debug/imports-status
# - /api/v1/debug/test-variation
# - /api/v1/debug/ssl-test
# ==========================================

# ==========================================
# Funciones de scraping
# ==========================================

async def scrape_bcv_simple():
    """Scraping del BCV para obtener tasas USD/VES y EUR/VES."""
    try:
        import httpx
        from bs4 import BeautifulSoup
        import re
        
        response = None
        final_url = None
        
        # Intentar con HTTPS primero, luego HTTP
        for url in BCV_URLS:
            try:
                async with httpx.AsyncClient(
                    timeout=30.0,
                    follow_redirects=True,
                    verify=False,  # Deshabilitar verificación SSL para Railway
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    final_url = url
                    break
            except Exception as e:
                print(f"Error con {url}: {str(e)}")
                continue
        
        if not response:
            return create_response(
                status="error",
                error="No se pudo conectar a ninguna URL del BCV",
                data={"urls_tried": BCV_URLS}
            )
            
        # Parsear HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar las cotizaciones con selectores más robustos
        usd_ves = _extract_rate_from_selectors(soup, USD_SELECTORS)
        eur_ves = _extract_rate_from_selectors(soup, EUR_SELECTORS)
        
        # Si no encontramos nada, intentar buscar en todo el HTML
        if usd_ves == 0 or eur_ves == 0:
            html_text = soup.get_text()
            usd_ves = _extract_rate_from_patterns(html_text, USD_PATTERNS)
            eur_ves = _extract_rate_from_patterns(html_text, EUR_PATTERNS)
        
        # Verificar si las tasas cambiaron antes de insertar
        if DATABASE_AVAILABLE and usd_ves > 0:
            await _save_bcv_rates_if_changed(usd_ves, eur_ves, final_url)
        
        # Validar que las tasas sean números válidos
        if usd_ves <= 0:
            print(f"⚠️ BCV: Tasa USD inválida: {usd_ves}")
            usd_ves = 0
            
        if eur_ves <= 0:
            print(f"⚠️ BCV: Tasa EUR inválida: {eur_ves}")
            eur_ves = 0
        
        print(f"✅ BCV: USD={usd_ves}, EUR={eur_ves}")
        
        return create_response(
            status="success",
            data={
                "usd_ves": usd_ves,
                "eur_ves": eur_ves,
                "source": "BCV",
                "url": final_url
            }
        )
    except Exception as e:
        return create_response(
            status="error",
            error=str(e),
            data={"url": "https://www.bcv.org.ve/"}
        )

def _extract_rate_from_selectors(soup, selectors: List[str]) -> float:
    """Extraer tasa usando selectores CSS."""
    for selector in selectors:
        try:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                numbers = re.findall(r'[\d,]+\.?\d*', text)
                if numbers:
                    return float(numbers[0].replace(',', '.'))
        except:
            continue
    return 0

def _extract_rate_from_patterns(text: str, patterns: List[str]) -> float:
    """Extraer tasa usando patrones regex."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', '.'))
    return 0

async def _save_bcv_rates_if_changed(usd_ves: float, eur_ves: float, final_url: str):
    """Guardar tasas BCV si cambiaron."""
    try:
        # Verificar USD/VES
        usd_changed = await check_rate_changed("BCV", "USD/VES", usd_ves)
        
        # Verificar EUR/VES (solo si hay valor)
        eur_changed = False
        if eur_ves > 0:
            eur_changed = await check_rate_changed("BCV", "EUR/VES", eur_ves)
        
        # Solo insertar si hay cambios
        if usd_changed or eur_changed:
            await DatabaseService.save_bcv_rates(usd_ves, eur_ves, {
                "source": "BCV",
                "url": final_url,
                "timestamp": datetime.now().isoformat()
            })
            print("💾 BCV rates INSERTADOS en base de datos (tasas cambiaron)")
        else:
            print("⏭️ BCV rates sin cambios - no se insertan en histórico")
    except Exception as e:
        print(f"⚠️ No se pudieron guardar BCV rates en BD: {e}")

# Función eliminada: fetch_binance_p2p_simple() - Reemplazada por binance_complete para minimizar gasto en BD

# ==========================================
# Funciones auxiliares para Binance P2P (sin guardar en BD)
# ==========================================

# ==========================================
# FUNCIONES ELIMINADAS PARA MINIMIZAR GASTO EN BD
# ==========================================
# Las siguientes funciones fueron eliminadas para evitar inserciones separadas en la base de datos:
# - fetch_binance_p2p_simple() - Insertaba solo buy_price
# - fetch_binance_p2p_sell_simple() - Insertaba solo sell_price  
# - _fetch_binance_p2p_rates_no_save() - Insertaba solo sell_price
# - _fetch_binance_p2p_sell_rates_no_save() - Insertaba solo buy_price
#
# AHORA SE USA ÚNICAMENTE:
# - get_binance_p2p_complete() - Inserta AMBOS precios en UNA SOLA operación de BD
# - save_binance_p2p_complete_rates() - Método unificado para guardar datos completos
# - _fetch_binance_p2p_direct() - Función auxiliar que NO inserta en BD, solo obtiene datos
# ==========================================

# ==========================================
# Funciones adicionales para Binance P2P
# ==========================================

# Función eliminada: fetch_binance_p2p_sell_simple() - Reemplazada por binance_complete para minimizar gasto en BD

# ==========================================
# Servicios y lógica compleja integrada
# ==========================================

class RatesService:
    """Servicio para manejar cotizaciones con base de datos."""
    
    def __init__(self, db_session=None):
        self.db = db_session
    
    async def get_current_rates(self, exchange_code=None, currency_pair=None):
        """Obtener cotizaciones actuales."""
        try:
            # Por ahora, obtener datos en tiempo real
            if exchange_code == "bcv" or exchange_code is None:
                bcv_data = await scrape_bcv_simple()
            else:
                bcv_data = None
                
            if exchange_code == "binance_p2p" or exchange_code is None:
                # Usar binance_complete para obtener datos unificados y minimizar gasto en BD
                try:
                    print("🟡 Obteniendo datos completos de Binance P2P para minimizar gasto en BD...")
                    complete_result = await get_binance_p2p_complete()
                    
                    if complete_result["status"] == "success":
                        complete_data = complete_result["data"]
                        # Construir estructura compatible con el resto del código
                        binance_data = {
                            "status": "success",
                            "data": {
                                "usdt_ves_buy": complete_data["buy_usdt"]["price"],
                                "usdt_ves_sell": complete_data["sell_usdt"]["price"],
                                "usdt_ves_avg": (complete_data["buy_usdt"]["price"] + complete_data["sell_usdt"]["price"]) / 2,
                                "volume_24h": complete_data["market_analysis"]["volume_24h"],
                                "timestamp": complete_data["timestamp"],
                                "source": "binance_p2p",
                                "api_method": "official_api"
                            }
                        }
                        print(f"✅ Binance P2P datos completos obtenidos: Buy={binance_data['data']['usdt_ves_buy']}, Sell={binance_data['data']['usdt_ves_sell']}")
                    else:
                        print(f"⚠️ Error obteniendo datos completos de Binance P2P: {complete_result.get('error', 'Error desconocido')}")
                        binance_data = None
                except Exception as e:
                    print(f"⚠️ Error obteniendo datos completos de Binance P2P: {e}")
                    binance_data = None
            else:
                binance_data = None
            
            rates = []
            
            if bcv_data and bcv_data["status"] == "success":
                print(f"✅ BCV datos válidos, procesando...")
                # Validar estructura de datos BCV
                if "data" not in bcv_data or "usd_ves" not in bcv_data["data"]:
                    print(f"⚠️ Estructura de datos BCV inválida: {bcv_data}")
                    return []
                # Calcular variación para BCV usando base de datos si está disponible
                variation_percentage = "0.00%"  # Por defecto
                variation_1h = "0.00%"
                variation_24h = "0.00%"
                trend_main = "stable"
                
                # Intentar obtener variación desde la base de datos
                if DATABASE_AVAILABLE and ASYNCPG_AVAILABLE and DATABASE_URL:
                    try:
                        conn = await asyncpg.connect(DATABASE_URL)
                        
                        # Obtener los dos últimos precios registrados en rate_history para BCV USD/VES
                        query = """
                            SELECT avg_price FROM rate_history 
                            WHERE exchange_code = 'BCV' AND currency_pair = 'USD/VES'
                            ORDER BY timestamp DESC LIMIT 2
                        """
                        
                        price_rows = await conn.fetch(query)
                        
                        if len(price_rows) >= 2:
                            last_price = float(price_rows[0]['avg_price'])
                            second_last_price = float(price_rows[1]['avg_price'])
                            
                            # Calcular variación entre último y penúltimo valor histórico
                            if second_last_price > 0:
                                variation_raw = ((last_price - second_last_price) / second_last_price) * 100
                                variation_percentage = f"{variation_raw:+.2f}%" if variation_raw != 0 else "0.00%"
                                trend_main = "up" if variation_raw > 0 else "down" if variation_raw < 0 else "stable"
                            else:
                                variation_percentage = "0.00%"
                                trend_main = "stable"
                        else:
                            variation_percentage = "0.00%"
                            trend_main = "stable"
                        
                        await conn.close()
                    except Exception as e:
                        print(f"⚠️ Error calculando variación BCV: {e}")
                elif not ASYNCPG_AVAILABLE:
                    print(f"⚠️ asyncpg no disponible - variación BCV se mantiene en 0.00%")
                elif not DATABASE_URL:
                    print(f"⚠️ DATABASE_URL no configurado - variación BCV se mantiene en 0.00%")
                else:
                    print(f"⚠️ Base de datos no disponible - variación BCV se mantiene en 0.00%")
                
                try:
                    rates.append({
                        "id": 1,
                        "exchange_code": "bcv",
                        "currency_pair": "USD/VES",
                        "base_currency": "USD",
                        "quote_currency": "VES",
                        "buy_price": bcv_data["data"]["usd_ves"],
                        "sell_price": bcv_data["data"]["usd_ves"],
                        "avg_price": bcv_data["data"]["usd_ves"],
                        "volume": None,
                        "volume_24h": None,
                        "source": "bcv",
                        "api_method": "web_scraping",
                        "trade_type": "official",
                        "timestamp": datetime.now().isoformat(),
                        "variation_percentage": variation_percentage,
                        "variation_1h": variation_1h,
                        "variation_24h": variation_24h,
                        "trend_main": trend_main,
                        "trend_1h": "stable",
                        "trend_24h": "stable"
                    })
                    print(f"✅ BCV USD/VES agregado: {bcv_data['data']['usd_ves']}")
                except KeyError as e:
                    print(f"❌ Error accediendo a datos BCV: {e}")
                    print(f"❌ Estructura BCV: {bcv_data}")
                    return []
                
                # Euro
                if bcv_data["data"]["eur_ves"] > 0:
                    # Calcular variación para EUR usando base de datos si está disponible
                    eur_variation_percentage = "0.00%"  # Por defecto
                    eur_trend_main = "stable"
                    
                    # Intentar obtener variación desde la base de datos para EUR
                    if DATABASE_AVAILABLE and ASYNCPG_AVAILABLE and DATABASE_URL:
                        try:
                            conn = await asyncpg.connect(DATABASE_URL)
                            
                            # Obtener los dos últimos precios registrados en rate_history para BCV EUR/VES
                            eur_query = """
                                SELECT avg_price FROM rate_history 
                                WHERE exchange_code = 'BCV' AND currency_pair = 'EUR/VES'
                                ORDER BY timestamp DESC LIMIT 2
                            """
                            
                            eur_price_rows = await conn.fetch(eur_query)
                            
                            if len(eur_price_rows) >= 2:
                                eur_last_price = float(eur_price_rows[0]['avg_price'])
                                eur_second_last_price = float(eur_price_rows[1]['avg_price'])
                                
                                # Calcular variación entre último y penúltimo valor histórico
                                if eur_second_last_price > 0:
                                    eur_variation_raw = ((eur_last_price - eur_second_last_price) / eur_second_last_price) * 100
                                    eur_variation_percentage = f"{eur_variation_raw:+.2f}%" if eur_variation_raw != 0 else "0.00%"
                                    eur_trend_main = "up" if eur_variation_raw > 0 else "down" if eur_variation_raw < 0 else "stable"
                                else:
                                    eur_variation_percentage = "0.00%"
                                    eur_trend_main = "stable"
                            else:
                                eur_variation_percentage = "0.00%"
                                eur_trend_main = "stable"
                            
                            await conn.close()
                        except Exception as e:
                            print(f"⚠️ Error calculando variación BCV EUR: {e}")
                    elif not ASYNCPG_AVAILABLE:
                        print(f"⚠️ asyncpg no disponible - variación BCV EUR se mantiene en 0.00%")
                    elif not DATABASE_URL:
                        print(f"⚠️ DATABASE_URL no configurado - variación BCV EUR se mantiene en 0.00%")
                    else:
                        print(f"⚠️ Base de datos no disponible - variación BCV EUR se mantiene en 0.00%")
                    
                    try:
                        rates.append({
                            "id": 2,
                            "exchange_code": "bcv",
                            "currency_pair": "EUR/VES",
                            "base_currency": "EUR",
                            "quote_currency": "VES",
                            "buy_price": bcv_data["data"]["eur_ves"],
                            "sell_price": bcv_data["data"]["eur_ves"],
                            "avg_price": bcv_data["data"]["eur_ves"],
                            "volume": None,
                            "volume_24h": None,
                            "source": "bcv",
                            "api_method": "web_scraping",
                            "trade_type": "official",
                            "timestamp": datetime.now().isoformat(),
                            "created_at": datetime.now().isoformat(),
                            "variation_percentage": eur_variation_percentage,
                            "trend_main": eur_trend_main
                        })
                        print(f"✅ BCV EUR/VES agregado: {bcv_data['data']['eur_ves']}")
                    except KeyError as e:
                        print(f"❌ Error accediendo a datos BCV EUR: {e}")
                        print(f"❌ Estructura BCV: {bcv_data}")
                        return []
            
            if binance_data and binance_data["status"] == "success":
                print(f"✅ Binance P2P datos válidos, procesando...")
                # Validar estructura de datos Binance
                if "data" not in binance_data or "usdt_ves_buy" not in binance_data["data"]:
                    print(f"⚠️ Estructura de datos Binance inválida: {binance_data}")
                    return []
                # Calcular variación para Binance P2P usando base de datos si está disponible
                variation_percentage = "0.00%"  # Por defecto
                variation_1h = "0.00%"
                variation_24h = "0.00%"
                trend_main = "stable"
                
                # Intentar obtener variación desde la base de datos
                if DATABASE_AVAILABLE and ASYNCPG_AVAILABLE and DATABASE_URL:
                    try:
                        conn = await asyncpg.connect(DATABASE_URL)
                        
                        # Obtener el último precio registrado en rate_history para Binance P2P USDT/VES
                        query = """
                            SELECT avg_price FROM rate_history 
                            WHERE exchange_code = 'BINANCE_P2P' AND currency_pair = 'USDT/VES'
                            ORDER BY timestamp DESC LIMIT 1
                        """
                        
                        last_price_row = await conn.fetchrow(query)
                        
                        if last_price_row and last_price_row['avg_price'] > 0:
                            current_price = binance_data["data"]["usdt_ves_avg"]
                            last_price = last_price_row['avg_price']
                            variation_raw = ((current_price - last_price) / last_price) * 100
                            variation_percentage = f"{variation_raw:+.2f}%" if variation_raw != 0 else "0.00%"
                            trend_main = "up" if variation_raw > 0 else "down" if variation_raw < 0 else "stable"
                        
                        await conn.close()
                    except Exception as e:
                        print(f"⚠️ Error calculando variación Binance P2P: {e}")
                elif not ASYNCPG_AVAILABLE:
                    print(f"⚠️ asyncpg no disponible - variación Binance P2P se mantiene en 0.00%")
                elif not DATABASE_URL:
                    print(f"⚠️ DATABASE_URL no configurado - variación Binance P2P se mantiene en 0.00%")
                else:
                    print(f"⚠️ Base de datos no disponible - variación Binance P2P se mantiene en 0.00%")
                
                try:
                    rates.append({
                        "id": 2,
                        "exchange_code": "binance_p2p",
                        "currency_pair": "USDT/VES",
                        "base_currency": "USDT",
                        "quote_currency": "VES",
                        "buy_price": binance_data["data"]["usdt_ves_buy"],
                        "sell_price": binance_data["data"]["usdt_ves_sell"],  # Ahora tenemos el sell_price real
                        "avg_price": binance_data["data"]["usdt_ves_avg"],
                        "volume": None,
                        "volume_24h": binance_data["data"].get("volume_24h"),
                        "source": "binance_p2p",
                        "api_method": "official_api",
                        "trade_type": "p2p",
                        "timestamp": binance_data["data"]["timestamp"],
                        "variation_percentage": variation_percentage,
                        "variation_1h": variation_1h,
                        "variation_24h": variation_24h,
                        "trend_main": trend_main,
                        "trend_1h": "stable",
                        "trend_24h": "stable"
                    })
                    print(f"✅ Binance P2P USDT/VES agregado: Buy={binance_data['data']['usdt_ves_buy']}, Sell={binance_data['data']['usdt_ves_sell']}")
                except KeyError as e:
                    print(f"❌ Error accediendo a datos Binance: {e}")
                    print(f"❌ Estructura Binance: {binance_data}")
                    return []
            
            print(f"✅ Total de tasas obtenidas: {len(rates)}")
            return rates
            
        except Exception as e:
            print(f"❌ Error en RatesService.get_current_rates: {e}")
            import traceback
            print(f"❌ Traceback completo: {traceback.format_exc()}")
            print(f"❌ Datos BCV: {bcv_data if 'bcv_data' in locals() else 'No disponible'}")
            print(f"❌ Datos Binance: {binance_data if 'binance_data' in locals() else 'No disponible'}")
            return []
    
    async def get_market_summary(self):
        """Resumen del mercado USDT/VES."""
        try:
            rates = await self.get_current_rates()
            
            bcv_usd = next((r for r in rates if r["exchange_code"] == "bcv" and r["currency_pair"] == "USD/VES"), None)
            binance_usdt = next((r for r in rates if r["exchange_code"] == "binance_p2p"), None)
            
            summary = {
                "total_rates": len(rates),
                "exchanges_active": len(set(r["exchange_code"] for r in rates)),
                "last_update": datetime.now().isoformat(),
                "rates": rates
            }
            
            if bcv_usd and binance_usdt:
                spread = binance_usdt["avg_price"] - bcv_usd["avg_price"]
                spread_percentage = (spread / bcv_usd["avg_price"]) * 100 if bcv_usd["avg_price"] > 0 else 0
                
                summary["market_analysis"] = {
                    "bcv_usd": bcv_usd["avg_price"],
                    "binance_usdt": binance_usdt["avg_price"],
                    "spread_ves": round(spread, 4),
                    "spread_percentage": round(spread_percentage, 2),
                    "market_difference": "premium" if spread > 0 else "discount"
                }
            
            return summary
            
        except Exception as e:
            return {
                "total_rates": 0,
                "exchanges_active": 0,
                "last_update": datetime.now().isoformat(),
                "rates": [],
                "error": str(e)
            }
    
    async def compare_exchanges(self, currency_pair="USDT/VES"):
        """Comparar cotizaciones entre exchanges."""
        try:
            rates = await self.get_current_rates()
            
            comparison = {
                "currency_pair": currency_pair,
                "timestamp": datetime.now().isoformat(),
                "exchanges": {}
            }
            
            for rate in rates:
                if rate["exchange_code"] not in comparison["exchanges"]:
                    comparison["exchanges"][rate["exchange_code"]] = []
                
                comparison["exchanges"][rate["exchange_code"]].append({
                    "currency_pair": rate["currency_pair"],
                    "buy_price": rate["buy_price"],
                    "sell_price": rate["sell_price"],
                    "avg_price": rate["avg_price"],
                    "volume_24h": rate["volume_24h"],
                    "last_update": rate["timestamp"]
                })
            
            return comparison
            
        except Exception as e:
            return {
                "currency_pair": currency_pair,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

# Instancia global del servicio
rates_service = RatesService()

# ==========================================
# API Endpoints para Railway
# ==========================================

@app.get("/api/v1/rates/current")
async def get_current_rates(
    exchange_code: str = None,
    currency_pair: str = None
):
    """Obtener cotizaciones actuales de USDT/VES con guardado automático en rate_history."""
    # Siempre obtener datos en tiempo real para incluir variaciones calculadas
    try:
        rates = await rates_service.get_current_rates(
            exchange_code=exchange_code,
            currency_pair=currency_pair
        )
        
        # IMPORTANTE: Guardar automáticamente las tasas obtenidas en rate_history
        # NOTA: Binance P2P ya se guarda automáticamente en get_binance_p2p_complete()
        # por lo que solo guardamos BCV y otros exchanges que no tengan guardado automático
        if rates and DATABASE_AVAILABLE:
            try:
                # Filtrar tasas que ya se guardaron automáticamente
                rates_to_save = []
                for rate in rates:
                    if rate.get('exchange_code') != 'binance_p2p':
                        rates_to_save.append(rate)
                
                if rates_to_save:
                    await _save_current_rates_to_history(rates_to_save)
                    print(f"💾 Tasas adicionales guardadas en rate_history: {len(rates_to_save)} registros (excluyendo Binance P2P)")
                else:
                    print("⏭️ Todas las tasas ya se guardaron automáticamente (incluyendo Binance P2P)")
                    
            except Exception as save_error:
                print(f"⚠️ Error guardando tasas adicionales en rate_history: {save_error}")
                # Continuar sin fallar el endpoint principal
        
        return {
            "status": "success",
            "data": rates,
            "count": len(rates),
            "source": "realtime_with_variations",
            "auto_saved_to_history": DATABASE_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # Si falla el servicio en tiempo real, intentar desde BD como fallback
        if not exchange_code and not currency_pair and DATABASE_AVAILABLE:
            try:
                db_rates = await DatabaseService.get_current_rates()
                if db_rates:
                    return {
                        "status": "success",
                        "data": db_rates,
                        "count": len(db_rates),
                        "source": "database_fallback",
                        "auto_saved_to_history": False,  # Ya están en BD
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as db_error:
                print(f"⚠️ Error obteniendo rates desde BD: {db_error}")
        
        return {
            "status": "error",
            "error": f"Error obteniendo cotizaciones: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def _save_current_rates_to_history(rates: List[Dict[str, Any]]) -> None:
    """Guardar tasas actuales en rate_history (excluyendo Binance P2P para evitar duplicados)."""
    if not rates or not DATABASE_AVAILABLE:
        return
    
    try:
        # Agrupar tasas por exchange_code para evitar duplicados innecesarios
        rates_by_exchange = {}
        for rate in rates:
            exchange_key = f"{rate.get('exchange_code', 'unknown')}_{rate.get('currency_pair', 'unknown')}"
            if exchange_key not in rates_by_exchange:
                rates_by_exchange[exchange_key] = rate
        
        # Guardar cada tasa única en rate_history
        for exchange_key, rate in rates_by_exchange.items():
            try:
                # Verificar si la tasa cambió significativamente antes de insertar
                should_insert = await _should_insert_rate_to_history(rate)
                
                if should_insert:
                    await _insert_single_rate_to_history(rate)
                    print(f"💾 Tasa guardada en rate_history: {rate.get('exchange_code')} {rate.get('currency_pair')}")
                else:
                    print(f"⏭️ Tasa sin cambios significativos: {rate.get('exchange_code')} {rate.get('currency_pair')}")
                    
            except Exception as rate_error:
                print(f"⚠️ Error procesando tasa individual {exchange_key}: {rate_error}")
                continue
                
    except Exception as e:
        print(f"❌ Error general guardando tasas en rate_history: {e}")

async def _should_insert_rate_to_history(rate: Dict[str, Any]) -> bool:
    """Determinar si una tasa debe ser insertada en rate_history."""
    try:
        exchange_code = rate.get('exchange_code')
        currency_pair = rate.get('currency_pair')
        current_price = rate.get('avg_price') or rate.get('buy_price')
        
        if not all([exchange_code, currency_pair, current_price]):
            return True  # Insertar si faltan datos críticos
        
        # Verificar si hay cambios significativos usando la función existente
        return await check_rate_changed(exchange_code, currency_pair, current_price)
        
    except Exception as e:
        print(f"⚠️ Error verificando si insertar tasa: {e}")
        return True  # En caso de error, insertar por seguridad

async def _insert_single_rate_to_history(rate: Dict[str, Any]) -> None:
    """Insertar una tasa en rate_history usando DatabaseService."""
    try:
        exchange_code = rate.get('exchange_code')
        currency_pair = rate.get('currency_pair')
        buy_price = rate.get('buy_price')
        sell_price = rate.get('sell_price')
        avg_price = rate.get('avg_price')
        volume_24h = rate.get('volume_24h')
        source = rate.get('source', exchange_code.lower())
        api_method = rate.get('api_method', 'api_call')
        trade_type = rate.get('trade_type', 'general')
        
        # Validar datos mínimos
        if not all([exchange_code, currency_pair]):
            print(f"⚠️ Datos insuficientes para guardar: {exchange_code} {currency_pair}")
            return
        
        # Si no hay avg_price, calcularlo
        if not avg_price and buy_price and sell_price:
            avg_price = (buy_price + sell_price) / 2
        elif not avg_price and buy_price:
            avg_price = buy_price
        elif not avg_price and sell_price:
            avg_price = sell_price
        
        # Usar el DatabaseService existente para mantener consistencia
        if exchange_code.upper() == "BCV":
            if currency_pair == "USD/VES":
                await DatabaseService.save_bcv_rates(
                    buy_price or avg_price, 
                    rate.get('eur_ves', 0), 
                    {"source": "auto_save_from_current", "timestamp": datetime.now().isoformat()}
                )
            elif currency_pair == "EUR/VES":
                await DatabaseService.save_bcv_rates(
                    rate.get('usd_ves', 0), 
                    sell_price or avg_price, 
                    {"source": "auto_save_from_current", "timestamp": datetime.now().isoformat()}
                )
        elif exchange_code.upper() == "BINANCE_P2P":
            # Crear estructura compatible con save_binance_p2p_complete_rates
            binance_data = {
                "buy_usdt": {"price": buy_price or avg_price, "avg_price": avg_price},
                "sell_usdt": {"price": sell_price or avg_price, "avg_price": avg_price},
                "market_analysis": {"volume_24h": volume_24h or 0},
                "source": source,
                "api_method": api_method
            }
            await DatabaseService.save_binance_p2p_complete_rates(binance_data)
        else:
            # Para otros exchanges, usar inserción directa
            await _insert_generic_rate_to_history(
                exchange_code, currency_pair, buy_price, sell_price, 
                avg_price, volume_24h, source, api_method, trade_type
            )
            
    except Exception as e:
        print(f"❌ Error insertando tasa individual en rate_history: {e}")

async def _insert_generic_rate_to_history(
    exchange_code: str, 
    currency_pair: str, 
    buy_price: float, 
    sell_price: float, 
    avg_price: float, 
    volume_24h: float, 
    source: str, 
    api_method: str, 
    trade_type: str
) -> None:
    """Insertar tasa genérica en rate_history para exchanges no específicos."""
    try:
        async for session in get_db_session():
            from app.models.rate_models import RateHistory
            
            rate_history = RateHistory(
                exchange_code=exchange_code,
                currency_pair=currency_pair,
                buy_price=buy_price,
                sell_price=sell_price,
                avg_price=avg_price,
                volume_24h=volume_24h,
                source=source,
                api_method=api_method,
                trade_type=trade_type,
                timestamp=datetime.now()
            )
            
            session.add(rate_history)
            await session.commit()
            
            print(f"💾 Tasa genérica guardada: {exchange_code} {currency_pair}")
            
    except Exception as e:
        print(f"❌ Error insertando tasa genérica: {e}")

@app.get("/api/v1/rates/history")
async def get_all_rate_history(limit: int = 100):
    """Obtener histórico general desde la base de datos."""
    if not DATABASE_AVAILABLE:
        return {
            "status": "error",
            "message": "Base de datos no disponible en Railway",
            "data": [],
            "count": 0,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        rates = await DatabaseService.get_latest_rates(limit)
        return {
            "status": "success",
            "data": rates,
            "count": len(rates),
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo histórico: {str(e)}",
            "data": [],
            "count": 0,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/summary")
async def get_market_summary():
    """Resumen del mercado USDT/VES con guardado automático en rate_history."""
    try:
        summary = await rates_service.get_market_summary()
        
        # IMPORTANTE: Guardar automáticamente las tasas del resumen en rate_history
        if summary and "rates" in summary and DATABASE_AVAILABLE:
            try:
                await _save_current_rates_to_history(summary["rates"])
                print(f"💾 Tasas del resumen guardadas automáticamente en rate_history: {len(summary['rates'])} registros")
            except Exception as save_error:
                print(f"⚠️ Error guardando tasas del resumen en rate_history: {save_error}")
                # Continuar sin fallar el endpoint principal
        
        return {
            "status": "success",
            "data": summary,
            "auto_saved_to_history": DATABASE_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo resumen: {str(e)}",
            "auto_saved_to_history": False,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/binance-p2p")
async def get_binance_p2p_rates():
    """Cotizaciones Binance P2P en tiempo real."""
    try:
        # Usar binance_complete para obtener datos unificados
        result = await get_binance_p2p_complete()
        if result.get("status") == "success" and result.get("data"):
            # Agregar información de monedas
            result["data"]["exchange_code"] = "binance_p2p"
            result["data"]["currency_pair"] = "USDT/VES"
            result["data"]["base_currency"] = "USDT"
            result["data"]["quote_currency"] = "VES"
        return result
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo Binance P2P: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/binance-p2p/sell")
async def get_binance_p2p_sell_rates():
    """Precios de venta de USDT (comprar USDT con VES)."""
    try:
        # Usar binance_complete para obtener datos unificados
        result = await get_binance_p2p_complete()
        if result.get("status") == "success" and result.get("data"):
            # Agregar información de monedas
            result["data"]["exchange_code"] = "binance_p2p"
            result["data"]["currency_pair"] = "USDT/VES"
            result["data"]["base_currency"] = "USDT"
            result["data"]["quote_currency"] = "VES"
        return result
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo Binance P2P sell: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/binance")
async def get_binance_rate():
    """Cotización de Binance P2P Venezuela (mercado crypto peer-to-peer)."""
    try:
        # Usar binance_complete para obtener datos unificados
        binance_data = await get_binance_p2p_complete()
        if binance_data["status"] == "success":
            return {
                "status": "success",
                "data": {
                    "id": 1,
                    "exchange_code": "binance_p2p",
                    "currency_pair": "USDT/VES",
                    "base_currency": "USDT",
                    "quote_currency": "VES",
                    "buy_price": binance_data["data"]["usdt_ves_buy"],
                    "sell_price": binance_data["data"]["usdt_ves_buy"],
                    "avg_price": binance_data["data"]["usdt_ves_avg"],
                    "volume": binance_data["data"]["volume_24h"],
                    "volume_24h": binance_data["data"]["volume_24h"],
                    "source": "binance_p2p",
                    "api_method": "official_api",
                    "trade_type": "buy_usdt",
                    "timestamp": binance_data["data"]["timestamp"],
                    "created_at": binance_data["data"]["timestamp"]
                }
            }
        else:
            return {
                "status": "error",
                "error": "No se pudo obtener cotización de Binance P2P",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo Binance P2P: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def _fetch_binance_p2p_direct(trade_type: str):
    """Obtener precios de Binance P2P directamente de la API (sin guardar en BD)."""
    try:
        import httpx
        
        # URL de la API de Binance P2P
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        
        # Payload para la consulta
        params = {
            "fiat": "VES",
            "page": 1,
            "rows": 10,
            "transAmount": 500,
            "tradeType": trade_type,  # "BUY" o "SELL"
            "asset": "USDT",
            "countries": [],
            "proMerchantAds": False,
            "shieldMerchantAds": False,
            "filterType": "all",
            "periods": [],
            "additionalKycVerifyFilter": 0,
            "publisherType": "merchant",
            "payTypes": ["PagoMovil"],
            "classifies": ["mass", "profession", "fiat_trade"],
            "tradedWith": False,
            "followed": False
        }
        
        # Configurar cliente con headers más realistas
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json"
            }
        ) as client:
            response = await client.post(url, json=params)
            response.raise_for_status()
            
        data = response.json()
        
        if data.get("success") and data.get("data") and len(data["data"]) > 0:
            try:
                # Obtener el mejor anuncio
                best_ad = data["data"][0]["adv"]
                best_price = float(best_ad["price"])
                
                # Calcular precio promedio de los primeros 5 anuncios
                prices = []
                volumes = []
                for adv in data["data"][:5]:
                    try:
                        price = float(adv["adv"]["price"])
                        prices.append(price)
                        
                        min_amount = float(adv["adv"]["minSingleTransAmount"])
                        max_amount = float(adv["adv"]["maxSingleTransAmount"])
                        avg_amount = (min_amount + max_amount) / 2
                        volumes.append(avg_amount)
                    except (ValueError, KeyError):
                        continue
                
                avg_price = sum(prices) / len(prices) if prices else best_price
                volume_24h = sum(volumes) if volumes else 0
                
                # Información del mejor anuncio
                best_ad_info = {
                    "price": best_price,
                    "min_amount": float(best_ad.get("minSingleTransAmount", 0)),
                    "max_amount": float(best_ad.get("maxSingleTransAmount", 0)),
                    "merchant": best_ad.get("fiatSymbol", "Unknown"),
                    "pay_types": best_ad.get("payTypes", []),
                    "user_type": "merchant" if best_ad.get("userType") == 1 else "user"
                }
                
                # Preparar datos (SIN guardar en BD)
                binance_data = {
                    "usdt_ves_buy": best_price if trade_type == "BUY" else best_price,
                    "usdt_ves_sell": best_price if trade_type == "SELL" else best_price,
                    "usdt_ves_avg": avg_price,
                    "volume_24h": volume_24h,
                    "best_ad": best_ad_info,
                    "total_ads": len(data["data"]),
                    "timestamp": datetime.now().isoformat(),
                    "source": "binance_p2p",
                    "api_method": "official_api",
                    "trade_type": f"{trade_type.lower()}_usdt"
                }
                
                return {
                    "status": "success",
                    "data": binance_data
                }
            except (ValueError, KeyError, IndexError) as e:
                return {
                    "status": "error",
                    "error": f"Error procesando datos de Binance: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "raw_data": str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
                }
        else:
            return {
                "status": "error",
                "error": "No se pudieron obtener datos de Binance",
                "timestamp": datetime.now().isoformat(),
                "response_status": data.get("success", False),
                "data_count": len(data.get("data", []))
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "url": url
        }

@app.get("/api/v1/rates/binance-p2p/complete")
async def get_binance_p2p_complete():
    """Obtener precios de compra y venta de USDT/VES en Binance P2P."""
    try:
        print("🟡 Obteniendo precios completos de Binance P2P...")
        
        # Obtener precios directamente de la API de Binance P2P
        # Precios de venta (SELL en Binance = vender USDT por VES)
        sell_result = await _fetch_binance_p2p_direct("SELL")
        
        # Precios de compra (BUY en Binance = comprar USDT con VES)
        buy_result = await _fetch_binance_p2p_direct("BUY")
        
        if buy_result["status"] == "success" and sell_result["status"] == "success":
            buy_data = buy_result["data"]
            sell_data = sell_result["data"]
            
            # CORREGIR: Asignar precios correctamente
            # buy_price = precio para COMPRAR USDT (más alto)
            # sell_price = precio para VENDER USDT (más bajo)
            buy_price = buy_data["usdt_ves_sell"]  # Precio más alto para comprar USDT
            sell_price = sell_data["usdt_ves_buy"]  # Precio más bajo para vender USDT
            
            # Calcular spread interno de Binance P2P
            spread_internal = buy_price - sell_price
            spread_percentage = (spread_internal / sell_price) * 100 if sell_price > 0 else 0
            
            complete_result = {
                "exchange_code": "binance_p2p",
                "currency_pair": "USDT/VES",
                "base_currency": "USDT",
                "quote_currency": "VES",
                "buy_usdt": {
                    "price": buy_price,  # Precio para COMPRAR USDT
                    "avg_price": buy_data["usdt_ves_avg"],
                    "best_ad": buy_data["best_ad"],
                    "total_ads": buy_data["total_ads"]
                },
                "sell_usdt": {
                    "price": sell_price,  # Precio para VENDER USDT
                    "avg_price": sell_data["usdt_ves_avg"],
                    "best_ad": sell_data["best_ad"],
                    "total_ads": sell_data["total_ads"]
                },
                "market_analysis": {
                    "spread_internal": round(spread_internal, 4),
                    "spread_percentage": round(spread_percentage, 2),
                    "volume_24h": round(buy_data["volume_24h"] + sell_data["volume_24h"], 2),
                    "liquidity_score": "high" if spread_percentage < 2 else "medium" if spread_percentage < 5 else "low"
                },
                "timestamp": datetime.now().isoformat(),
                "source": "binance_p2p",
                "api_method": "official_api"
            }
            
            print(f"✅ Binance P2P completo obtenido: Buy={buy_price} (comprar USDT), Sell={sell_price} (vender USDT)")
            
            # ==========================================
            # GUARDADO INTELIGENTE PARA BINANCE P2P
            # ==========================================
            # IMPORTANTE: Solo guardar UNA vez usando el método específico para datos completos
            # NO guardar usando las funciones individuales para evitar duplicados
            # 
            # LÓGICA DE VERIFICACIÓN:
            # 1. Verificar si buy_price cambió significativamente
            # 2. Verificar si sell_price cambió significativamente  
            # 3. Solo insertar si hay cambios en cualquiera de los dos precios
            # 4. Usar tolerancia configurable (0.01% por defecto)
            # 5. Evitar duplicados innecesarios en rate_history
            # 
            # NOTA: Esta función se ejecuta desde /api/v1/rates/current y ya guarda
            # automáticamente en rate_history, por lo que el endpoint principal NO debe
            # volver a guardar las mismas tasas para evitar duplicados.
            # ==========================================
            try:
                if DATABASE_AVAILABLE:
                    # Verificar si hay cambios significativos en AMBOS precios por separado
                    # Para Binance P2P, necesitamos verificar tanto buy_price como sell_price
                    buy_price_changed = await check_rate_changed("BINANCE_P2P", "USDT/VES", buy_price)
                    sell_price_changed = await check_rate_changed("BINANCE_P2P", "USDT/VES", sell_price)
                    
                    # Solo insertar si hay cambios en cualquiera de los dos precios
                    if buy_price_changed or sell_price_changed:
                        await DatabaseService.save_binance_p2p_complete_rates(complete_result)
                        print("💾 Binance P2P COMPLETE rates INSERTADOS en base de datos (UNA SOLA LÍNEA - tasas cambiaron)")
                        print(f"   Buy price cambió: {buy_price_changed}, Sell price cambió: {sell_price_changed}")
                    else:
                        print("⏭️ Binance P2P COMPLETE rates sin cambios - no se insertan en histórico")
                        print(f"   Buy price sin cambios, Sell price sin cambios")
                else:
                    print("💾 Binance P2P COMPLETE rates obtenidos (sin BD en Railway)")
            except Exception as e:
                print(f"⚠️ No se pudieron guardar Binance P2P COMPLETE rates en BD: {e}")
            
            return {"status": "success", "data": complete_result}
        else:
            errors = []
            if buy_result["status"] != "success":
                errors.append(f"Compra: {buy_result.get('error', 'Error desconocido')}")
            if sell_result["status"] != "success":
                errors.append(f"Venta: {sell_result.get('error', 'Error desconocido')}")
            
            raise Exception(f"Error obteniendo datos completos: {'; '.join(errors)}")
            
    except Exception as e:
        print(f"❌ Error obteniendo datos completos de Binance P2P: {e}")
        return {"status": "error", "error": str(e)}

@app.get("/api/v1/rates/scrape-bcv")
async def scrape_bcv_live():
    """Scraping en tiempo real del BCV."""
    try:
        result = await scrape_bcv_simple()
        
        # Si el scraping fue exitoso, obtener información adicional de la BD
        if result.get("status") == "success":
            try:
                # Verificar si hay conexión a base de datos disponible
                if DATABASE_URL and ASYNCPG_AVAILABLE:
                    conn = await asyncpg.connect(DATABASE_URL)
                    
                    # Consultar exchange_code desde current_rates para BCV
                    current_rate = await conn.fetchrow("""
                        SELECT exchange_code 
                        FROM current_rates 
                        WHERE exchange_code = 'BCV' 
                        LIMIT 1
                    """)
                    
                    # Consultar base_currency desde currency_pairs para USD/VES
                    currency_pair = await conn.fetchrow("""
                        SELECT base_currency 
                        FROM currency_pairs 
                        WHERE symbol = 'USD/VES' 
                        LIMIT 1
                    """)
                    
                    await conn.close()
                    
                    exchange_code = current_rate["exchange_code"] if current_rate else "bcv"
                    base_currency = currency_pair["base_currency"] if currency_pair else "USD"
                    
                    # Agregar la información de la BD al resultado
                    if result.get("data"):
                        result["data"]["exchange_code"] = exchange_code
                        result["data"]["base_currency"] = base_currency
                        result["data"]["database_info"] = {
                            "exchange_code": exchange_code,
                            "base_currency": base_currency,
                            "source": "database"
                        }
                else:
                    # Si no hay BD disponible, usar valores por defecto
                    if result.get("data"):
                        result["data"]["exchange_code"] = "bcv"
                        result["data"]["base_currency"] = "USD"
                        result["data"]["database_info"] = {
                            "exchange_code": "bcv",
                            "base_currency": "USD",
                            "source": "default_values"
                        }
                
            except Exception as db_error:
                # Si hay error en la BD, continuar sin esa información
                if result.get("data"):
                    result["data"]["exchange_code"] = "bcv"
                    result["data"]["base_currency"] = "USD"
                    result["data"]["database_info"] = {
                        "error": f"Error consultando BD: {str(db_error)}",
                        "source": "scraping_only"
                    }
        
        return result
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error en scraping del BCV: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/bcv")
async def get_bcv_rate():
    """Cotización oficial del BCV (Banco Central de Venezuela)."""
    try:
        bcv_data = await scrape_bcv_simple()
        if bcv_data["status"] == "success":
            # Validar estructura de datos BCV
            if "data" not in bcv_data or "usd_ves" not in bcv_data["data"]:
                return {
                    "status": "error",
                    "error": "Estructura de datos BCV inválida",
                    "timestamp": datetime.now().isoformat()
                }
            return {
                "status": "success",
                "data": {
                    "id": 1,
                    "exchange_code": "bcv",
                    "currency_pair": "USD/VES",
                    "base_currency": "USD",
                    "quote_currency": "VES",
                    "buy_price": bcv_data["data"]["usd_ves"],
                    "sell_price": bcv_data["data"]["usd_ves"],
                    "avg_price": bcv_data["data"]["usd_ves"],
                    "volume": None,
                    "volume_24h": None,
                    "source": "bcv",
                    "api_method": "web_scraping",
                    "trade_type": "official",
                    "timestamp": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat()
                }
            }
        else:
            return {
                "status": "error",
                "error": "No se pudo obtener cotización del BCV",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo BCV: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/exchanges")
async def get_exchanges():
    """Lista de exchanges disponibles."""
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
    """Comparar cotizaciones entre BCV y Binance P2P con guardado automático en rate_history."""
    try:
        # Obtener datos del BCV
        bcv_data = await scrape_bcv_simple()
        
        # Obtener datos de Binance P2P usando binance_complete (datos unificados)
        binance_complete = await get_binance_p2p_complete()
        
        if bcv_data["status"] == "success" and binance_complete["status"] == "success":
            # Validar estructura de datos BCV
            if "data" not in bcv_data or "usd_ves" not in bcv_data["data"]:
                return {
                    "status": "error",
                    "error": "Estructura de datos BCV inválida",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Validar estructura de datos Binance
            if "data" not in binance_complete or "buy_usdt" not in binance_complete["data"] or "sell_usdt" not in binance_complete["data"]:
                return {
                    "status": "error",
                    "error": "Estructura de datos Binance completa inválida",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Calcular spread entre BCV y Binance P2P
            bcv_usd = bcv_data["data"]["usd_ves"]
            binance_avg = (binance_complete["data"]["buy_usdt"]["price"] + binance_complete["data"]["sell_usdt"]["price"]) / 2
            
            spread_bcv_binance = bcv_usd - binance_avg
            spread_percentage = (spread_bcv_binance / binance_avg) * 100 if binance_avg > 0 else 0
            
            # IMPORTANTE: Guardar automáticamente las tasas de comparación en rate_history
            if DATABASE_AVAILABLE:
                try:
                    # Crear estructura de tasas para guardar
                    comparison_rates = [
                        {
                            "exchange_code": "bcv",
                            "currency_pair": "USD/VES",
                            "buy_price": bcv_usd,
                            "sell_price": bcv_usd,
                            "avg_price": bcv_usd,
                            "source": "bcv",
                            "api_method": "web_scraping",
                            "trade_type": "official"
                        },
                        {
                            "exchange_code": "binance_p2p",
                            "currency_pair": "USDT/VES",
                            "buy_price": binance_complete["data"]["buy_usdt"]["price"],
                            "sell_price": binance_complete["data"]["sell_usdt"]["price"],
                            "avg_price": binance_avg,
                            "source": "binance_p2p",
                            "api_method": "official_api",
                            "trade_type": "p2p"
                        }
                    ]
                    
                    await _save_current_rates_to_history(comparison_rates)
                    print(f"💾 Tasas de comparación guardadas automáticamente en rate_history: {len(comparison_rates)} registros")
                except Exception as save_error:
                    print(f"⚠️ Error guardando tasas de comparación en rate_history: {save_error}")
                    # Continuar sin fallar el endpoint principal
            
            return {
                "status": "success",
                "data": {
                    "bcv": {
                        "exchange_code": "bcv",
                        "currency_pair": "USD/VES",
                        "base_currency": "USD",
                        "quote_currency": "VES",
                        "usd_ves": bcv_data["data"]["usd_ves"],
                        "eur_ves": bcv_data["data"]["eur_ves"],
                        "timestamp": datetime.now().isoformat()
                    },
                    "binance_p2p": {
                        "exchange_code": "binance_p2p",
                        "currency_pair": "USDT/VES",
                        "base_currency": "USDT",
                        "quote_currency": "VES",
                        "usdt_ves_buy": binance_complete["data"]["buy_usdt"]["price"],
                        "usdt_ves_sell": binance_complete["data"]["sell_usdt"]["price"],
                        "usdt_ves_avg": binance_avg,
                        "timestamp": binance_complete["data"]["timestamp"]
                    },
                    "analysis": {
                        "spread_bcv_binance": round(spread_bcv_binance, 4),
                        "spread_percentage": round(spread_percentage, 2),
                        "timestamp": datetime.now().isoformat()
                    }
                },
                "auto_saved_to_history": DATABASE_AVAILABLE,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "error": "No se pudieron obtener todas las cotizaciones",
                "auto_saved_to_history": False,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error comparando exchanges: {str(e)}",
            "auto_saved_to_history": False,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/status")
async def get_rates_status():
    """Estado de las cotizaciones y fuentes de datos."""
    try:
        rates = await rates_service.get_current_rates()
        
        status = {
            "total_rates": len(rates),
            "exchanges_status": {},
            "last_update": datetime.now().isoformat(),
            "data_sources": {
                "bcv": {"status": "active", "last_check": datetime.now().isoformat()},
                "binance_p2p": {"status": "active", "last_check": datetime.now().isoformat()}
            }
        }
        
        # Agrupar por exchange
        for rate in rates:
            if rate["exchange_code"] not in status["exchanges_status"]:
                status["exchanges_status"][rate["exchange_code"]] = {
                    "rates_count": 0,
                    "last_update": rate["timestamp"],
                    "currency_pairs": []
                }
            
            status["exchanges_status"][rate["exchange_code"]]["rates_count"] += 1
            status["exchanges_status"][rate["exchange_code"]]["currency_pairs"].append(rate["currency_pair"])
        
        return {
            "status": "success",
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo estado: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/v1/rates/refresh")
async def refresh_rates(exchange_code: str = None):
    """Forzar actualización de cotizaciones."""
    try:
        # Forzar actualización de datos
        if exchange_code == "bcv" or exchange_code is None:
            bcv_result = await scrape_bcv_simple()
        else:
            bcv_result = None
            
        if exchange_code == "binance_p2p" or exchange_code is None:
            # Usar binance_complete para obtener datos unificados
            binance_result = await get_binance_p2p_complete()
        else:
            binance_result = None
        
        exchanges_updated = []
        if bcv_result and bcv_result["status"] == "success":
            exchanges_updated.append("bcv")
        if binance_result and binance_result["status"] == "success":
            exchanges_updated.append("binance_p2p")
        
        return {
            "status": "success",
            "data": {
                "message": "Actualización iniciada",
                "exchanges_updated": exchanges_updated,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error actualizando cotizaciones: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/auto-save-status")
async def get_auto_save_status():
    """Estado del guardado automático en rate_history."""
    try:
        if not DATABASE_AVAILABLE:
            return {
                "status": "error",
                "error": "Base de datos no disponible",
                "auto_save_enabled": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Obtener estadísticas del historial
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Contar total de registros en rate_history
        total_count = await conn.fetchval("SELECT COUNT(*) FROM rate_history")
        
        # Contar registros por exchange
        exchange_stats = await conn.fetch("""
            SELECT exchange_code, COUNT(*) as count, 
                   MAX(timestamp) as last_update,
                   MIN(timestamp) as first_update
            FROM rate_history 
            GROUP BY exchange_code 
            ORDER BY count DESC
        """)
        
        # Últimos 10 registros
        latest_records = await conn.fetch("""
            SELECT exchange_code, currency_pair, avg_price, timestamp, source
            FROM rate_history 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        
        # Estadísticas por día (últimos 7 días)
        daily_stats = await conn.fetch("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as records_count,
                COUNT(DISTINCT exchange_code) as exchanges_count
            FROM rate_history 
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """)
        
        await conn.close()
        
        # Formatear estadísticas
        formatted_exchange_stats = []
        for stat in exchange_stats:
            formatted_exchange_stats.append({
                "exchange_code": stat["exchange_code"],
                "total_records": stat["count"],
                "last_update": stat["last_update"].isoformat() if stat["last_update"] else None,
                "first_update": stat["first_update"].isoformat() if stat["first_update"] else None
            })
        
        formatted_latest_records = []
        for record in latest_records:
            formatted_latest_records.append({
                "exchange_code": record["exchange_code"],
                "currency_pair": record["currency_pair"],
                "avg_price": float(record["avg_price"]) if record["avg_price"] else None,
                "timestamp": record["timestamp"].isoformat() if record["timestamp"] else None,
                "source": record["source"]
            })
        
        formatted_daily_stats = []
        for stat in daily_stats:
            formatted_daily_stats.append({
                "date": stat["date"].isoformat() if stat["date"] else None,
                "records_count": stat["records_count"],
                "exchanges_count": stat["exchanges_count"]
            })
        
        return {
            "status": "success",
            "data": {
                "auto_save_enabled": True,
                "database_available": True,
                "total_records_in_history": total_count,
                "exchange_statistics": formatted_exchange_stats,
                "latest_records": formatted_latest_records,
                "daily_statistics": formatted_daily_stats,
                "auto_save_endpoints": [
                    "/api/v1/rates/current",
                    "/api/v1/rates/summary", 
                    "/api/v1/rates/compare"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo estado del guardado automático: {str(e)}",
            "auto_save_enabled": False,
            "timestamp": datetime.now().isoformat()
        }

# ==========================================
# Configuración de inicio del servidor
# ==========================================

def get_server_config():
    """Obtener configuración del servidor."""
    return {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8000)),
        "reload": False,  # False para producción
        "log_level": "warning" if os.getenv("ENVIRONMENT", "development") == "production" else "info"
    }

def print_startup_info():
    """Imprimir información de inicio del servidor."""
    config = get_server_config()
    
    print("🚀 Iniciando CrystoAPIVzla Simple Server para Railway...")
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"📊 Database URL: {'configured' if os.getenv('DATABASE_URL') else 'not_configured'}")
    print(f"🌐 Host: {config['host']}")
    print(f"🔌 Port: {config['port']}")
    
    # Información adicional para producción
    if os.getenv("ENVIRONMENT", "development") == "production":
        print("🛡️ Modo PRODUCCIÓN activado - Endpoints de debug deshabilitados")
        print("🔒 Información sensible ocultada por seguridad")

if __name__ == "__main__":
    """Ejecutar servidor."""
    print_startup_info()
    
    config = get_server_config()
    uvicorn.run(
        "simple_server_railway:app",
        **config
    )
