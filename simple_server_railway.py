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
import warnings
import ssl

# Importar servicios de base de datos
try:
    from app.services.database_service import DatabaseService
    from app.core.database import get_db_session
    DATABASE_AVAILABLE = True
except ImportError:
    print("⚠️ DatabaseService no disponible - funcionando sin persistencia")
    DATABASE_AVAILABLE = False

# Suprimir advertencias de SSL para Railway
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

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

@app.get("/api/v1/debug/bcv")
async def debug_bcv():
    """Endpoint de debug para probar el scraping del BCV"""
    try:
        import httpx
        
        # Probar diferentes URLs
        urls_to_test = [
            "https://www.bcv.org.ve/",
            "https://www.bcv.org.ve",
            "http://www.bcv.org.ve/",
            "http://www.bcv.org.ve"
        ]
        
        results = []
        
        for url in urls_to_test:
            try:
                async with httpx.AsyncClient(
                    timeout=10.0,
                    follow_redirects=True,
                    verify=False,  # Deshabilitar verificación SSL para Railway
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                ) as client:
                    response = await client.get(url)
                    results.append({
                        "url": url,
                        "status_code": response.status_code,
                        "final_url": str(response.url),
                        "content_length": len(response.text),
                        "content_preview": response.text[:500] + "..." if len(response.text) > 500 else response.text
                    })
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "data": {
                "test_results": results,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/debug/ssl-test")
async def test_ssl_connection():
    """Endpoint específico para probar conexiones SSL"""
    try:
        import httpx
        
        test_urls = [
            {"url": "https://www.bcv.org.ve/", "description": "BCV HTTPS"},
            {"url": "http://www.bcv.org.ve/", "description": "BCV HTTP"},
            {"url": "https://httpbin.org/get", "description": "HTTPBin HTTPS (control)"}
        ]
        
        results = []
        
        for test in test_urls:
            try:
                # Probar con SSL habilitado
                try:
                    async with httpx.AsyncClient(
                        timeout=10.0,
                        verify=True,  # SSL habilitado
                        headers={"User-Agent": "Mozilla/5.0"}
                    ) as client:
                        response = await client.get(test["url"])
                        results.append({
                            "url": test["url"],
                            "description": test["description"],
                            "ssl_enabled": True,
                            "status_code": response.status_code,
                            "success": True,
                            "error": None
                        })
                except Exception as ssl_error:
                    # Si falla SSL, probar sin verificación
                    try:
                        async with httpx.AsyncClient(
                            timeout=10.0,
                            verify=False,  # SSL deshabilitado
                            headers={"User-Agent": "Mozilla/5.0"}
                        ) as client:
                            response = await client.get(test["url"])
                            results.append({
                                "url": test["url"],
                                "description": test["description"],
                                "ssl_enabled": False,
                                "status_code": response.status_code,
                                "success": True,
                                "error": f"SSL falló, pero funcionó sin verificación: {str(ssl_error)}"
                            })
                    except Exception as no_ssl_error:
                        results.append({
                            "url": test["url"],
                            "description": test["description"],
                            "ssl_enabled": False,
                            "status_code": None,
                            "success": False,
                            "error": f"Falló incluso sin SSL: {str(no_ssl_error)}"
                        })
                        
            except Exception as e:
                results.append({
                    "url": test["url"],
                    "description": test["description"],
                    "ssl_enabled": None,
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "data": {
                "ssl_test_results": results,
                "timestamp": datetime.now().isoformat(),
                "note": "SSL deshabilitado para Railway por problemas de certificados"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ==========================================
# Funciones de scraping simplificadas para Railway
# ==========================================

async def scrape_bcv_simple():
    """Scraping simplificado del BCV sin dependencias complejas"""
    try:
        import httpx
        from bs4 import BeautifulSoup
        
        # URLs a probar (HTTPS primero, luego HTTP como fallback)
        urls_to_try = [
            "https://www.bcv.org.ve/",
            "http://www.bcv.org.ve/"
        ]
        
        response = None
        final_url = None
        
        # Intentar con HTTPS primero, luego HTTP
        for url in urls_to_try:
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
            return {
                "status": "error",
                "error": "No se pudo conectar a ninguna URL del BCV",
                "timestamp": datetime.now().isoformat(),
                "urls_tried": urls_to_try
            }
            
        # Parsear HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar las cotizaciones con selectores más robustos
        usd_ves = 0
        eur_ves = 0
        
        # Intentar diferentes selectores para el dólar
        usd_selectors = [
            'div[id="dolar"]',
            'div[class*="dolar"]',
            'span[id="dolar"]',
            'span[class*="dolar"]',
            'div:contains("USD")',
            'span:contains("USD")'
        ]
        
        for selector in usd_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Extraer solo números y punto decimal
                    import re
                    numbers = re.findall(r'[\d,]+\.?\d*', text)
                    if numbers:
                        usd_ves = float(numbers[0].replace(',', '.'))
                        break
            except:
                continue
        
        # Intentar diferentes selectores para el euro
        eur_selectors = [
            'div[id="euro"]',
            'div[class*="euro"]',
            'span[id="euro"]',
            'span[class*="euro"]',
            'div:contains("EUR")',
            'span:contains("EUR")'
        ]
        
        for selector in eur_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Extraer solo números y punto decimal
                    import re
                    numbers = re.findall(r'[\d,]+\.?\d*', text)
                    if numbers:
                        eur_ves = float(numbers[0].replace(',', '.'))
                        break
            except:
                continue
        
        # Si no encontramos nada, intentar buscar en todo el HTML
        if usd_ves == 0 or eur_ves == 0:
            # Buscar patrones de cotización en el texto
            html_text = soup.get_text()
            import re
            
            # Buscar patrones como "USD: 35,50" o "Dólar: 35.50"
            usd_patterns = [
                r'USD[:\s]*([\d,]+\.?\d*)',
                r'Dólar[:\s]*([\d,]+\.?\d*)',
                r'DOLAR[:\s]*([\d,]+\.?\d*)'
            ]
            
            for pattern in usd_patterns:
                match = re.search(pattern, html_text, re.IGNORECASE)
                if match:
                    usd_ves = float(match.group(1).replace(',', '.'))
                    break
            
            # Buscar patrones para euro
            eur_patterns = [
                r'EUR[:\s]*([\d,]+\.?\d*)',
                r'Euro[:\s]*([\d,]+\.?\d*)',
                r'EURO[:\s]*([\d,]+\.?\d*)'
            ]
            
            for pattern in eur_patterns:
                match = re.search(pattern, html_text, re.IGNORECASE)
                if match:
                    eur_ves = float(match.group(1).replace(',', '.'))
                    break
        
        # Guardar en base de datos si está disponible
        if DATABASE_AVAILABLE and usd_ves > 0:
            try:
                await DatabaseService.save_bcv_rates(usd_ves, eur_ves, {
                    "source": "BCV",
                    "url": final_url,
                    "timestamp": datetime.now().isoformat()
                })
                print("💾 BCV rates guardados en base de datos")
            except Exception as e:
                print(f"⚠️ No se pudieron guardar BCV rates en BD: {e}")
        
        return {
            "status": "success",
            "data": {
                "usd_ves": usd_ves,
                "eur_ves": eur_ves,
                "timestamp": datetime.now().isoformat(),
                "source": "BCV",
                "url": final_url
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "url": "https://www.bcv.org.ve/"
        }

async def fetch_binance_p2p_simple():
    """Consulta a Binance P2P para vender USDT por VES (comprar USDT)"""
    try:
        import httpx
        
        # URL de la API de Binance P2P
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        
        # Payload para la consulta (Compras USDT con Bolivares)
        params = {
            "fiat": "VES",
            "page": 1,
            "rows": 10,
            "transAmount": 500,
            "tradeType": "BUY",  # Compras USDT por Bs
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
                
                # Preparar datos para guardar en BD
                binance_data = {
                    "usdt_ves_buy": best_price,  # Precio para COMPRAR USDT con VES
                    "usdt_ves_avg": avg_price,
                    "volume_24h": volume_24h,
                    "best_ad": best_ad_info,
                    "total_ads": len(data["data"]),
                    "timestamp": datetime.now().isoformat(),
                    "source": "binance_p2p",
                    "api_method": "official_api",
                    "trade_type": "buy_usdt"
                }
                
                # Guardar en base de datos si está disponible
                if DATABASE_AVAILABLE:
                    try:
                        await DatabaseService.save_binance_p2p_rates(binance_data)
                        print("💾 Binance P2P rates guardados en base de datos")
                    except Exception as e:
                        print(f"⚠️ No se pudieron guardar Binance P2P rates en BD: {e}")
                
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

# ==========================================
# Funciones auxiliares para Binance P2P (sin guardar en BD)
# ==========================================

async def _fetch_binance_p2p_rates_no_save():
    """Obtener precios de venta (SELL en Binance = vender USDT por VES) - SIN guardar en BD"""
    try:
        import httpx
        
        # URL de la API de Binance P2P
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        
        # Payload para la consulta (Vendes USDT por Bolivares)
        params = {
            "fiat": "VES",
            "page": 1,
            "rows": 10,
            "transAmount": 500,
            "tradeType": "SELL",  # Vendes USDT a Bs
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
                
                # Preparar datos para guardar en BD
                binance_data = {
                    "usdt_ves_buy": best_price,  # Precio más bajo para vender USDT
                    "usdt_ves_avg": avg_price,
                    "volume_24h": volume_24h,
                    "best_ad": best_ad_info,
                    "total_ads": len(data["data"]),
                    "timestamp": datetime.now().isoformat(),
                    "source": "binance_p2p",
                    "api_method": "official_api",
                    "trade_type": "sell_usdt"
                }
                
                # Guardar en base de datos si está disponible
                if DATABASE_AVAILABLE:
                    try:
                        await DatabaseService.save_binance_p2p_rates(binance_data)
                        print("💾 Binance P2P rates (sell) guardados en base de datos")
                    except Exception as e:
                        print(f"⚠️ No se pudieron guardar Binance P2P rates (sell) en BD: {e}")
                
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

async def _fetch_binance_p2p_sell_rates_no_save():
    """Obtener precios de compra (BUY en Binance = comprar USDT con VES) - SIN guardar en BD"""
    try:
        import httpx
        
        # URL de la API de Binance P2P
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        
        # Payload para la consulta (Compras USDT con Bolivares)
        params = {
            "fiat": "VES",
            "page": 1,
            "rows": 10,
            "transAmount": 500,
            "tradeType": "BUY",  # Compras USDT por Bs
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
                
                # Preparar datos para guardar en BD
                binance_data = {
                    "usdt_ves_sell": best_price,  # Precio más alto para comprar USDT
                    "usdt_ves_avg": avg_price,
                    "volume_24h": volume_24h,
                    "best_ad": best_ad_info,
                    "total_ads": len(data["data"]),
                    "timestamp": datetime.now().isoformat(),
                    "source": "binance_p2p",
                    "api_method": "official_api",
                    "trade_type": "buy_usdt"
                }
                
                # Guardar en base de datos si está disponible
                if DATABASE_AVAILABLE:
                    try:
                        await DatabaseService.save_binance_p2p_rates(binance_data)
                        print("💾 Binance P2P rates (buy) guardados en base de datos")
                    except Exception as e:
                        print(f"⚠️ No se pudieron guardar Binance P2P rates (buy) en BD: {e}")
                
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

# ==========================================
# Funciones adicionales para Binance P2P
# ==========================================

async def fetch_binance_p2p_sell_simple():
    """Consulta a Binance P2P para comprar USDT con VES (vender USDT)"""
    return await _fetch_binance_p2p_sell_rates_no_save()

# ==========================================
# Servicios y lógica compleja integrada
# ==========================================

class RatesService:
    """Servicio para manejar cotizaciones con base de datos"""
    
    def __init__(self, db_session=None):
        self.db = db_session
    
    async def get_current_rates(self, exchange_code=None, currency_pair=None):
        """Obtener cotizaciones actuales"""
        try:
            # Por ahora, obtener datos en tiempo real
            if exchange_code == "bcv" or exchange_code is None:
                bcv_data = await scrape_bcv_simple()
            else:
                bcv_data = None
                
            if exchange_code == "binance_p2p" or exchange_code is None:
                binance_data = await fetch_binance_p2p_simple()
            else:
                binance_data = None
            
            rates = []
            
            if bcv_data and bcv_data["status"] == "success":
                rates.append({
                    "id": 1,
                    "exchange_code": "bcv",
                    "currency_pair": "USD/VES",
                    "buy_price": bcv_data["data"]["usd_ves"],
                    "sell_price": bcv_data["data"]["usd_ves"],
                    "avg_price": bcv_data["data"]["usd_ves"],
                    "volume": None,
                    "volume_24h": None,
                    "source": "bcv",
                    "api_method": "web_scraping",
                    "trade_type": "official",
                    "timestamp": bcv_data["data"]["timestamp"],
                    "created_at": bcv_data["data"]["timestamp"]
                })
                
                # Euro
                if bcv_data["data"]["eur_ves"] > 0:
                    rates.append({
                        "id": 2,
                        "exchange_code": "bcv",
                        "currency_pair": "EUR/VES",
                        "buy_price": bcv_data["data"]["eur_ves"],
                        "sell_price": bcv_data["data"]["eur_ves"],
                        "avg_price": bcv_data["data"]["eur_ves"],
                        "volume": None,
                        "volume_24h": None,
                        "source": "bcv",
                        "api_method": "web_scraping",
                        "trade_type": "official",
                        "timestamp": bcv_data["data"]["timestamp"],
                        "created_at": bcv_data["data"]["timestamp"]
                    })
            
            if binance_data and binance_data["status"] == "success":
                rates.append({
                    "id": 3,
                    "exchange_code": "binance_p2p",
                    "currency_pair": "USDT/VES",
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
                })
            
            return rates
            
        except Exception as e:
            return []
    
    async def get_market_summary(self):
        """Resumen del mercado USDT/VES"""
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
        """Comparar cotizaciones entre exchanges"""
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
    """
    Obtener cotizaciones actuales de USDT/VES
    
    - **exchange_code**: Filtrar por exchange (bcv, binance_p2p)
    - **currency_pair**: Filtrar por par de monedas
    """
    # Si no hay filtros, intentar obtener desde BD primero
    if not exchange_code and not currency_pair and DATABASE_AVAILABLE:
        try:
            db_rates = await DatabaseService.get_current_rates()
            if db_rates:
                return {
                    "status": "success",
                    "data": db_rates,
                    "count": len(db_rates),
                    "source": "database",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"⚠️ Error obteniendo rates desde BD: {e}")
    
    # Si no hay BD o no hay datos, obtener en tiempo real
    try:
        rates = await rates_service.get_current_rates(
            exchange_code=exchange_code,
            currency_pair=currency_pair
        )
        return {
            "status": "success",
            "data": rates,
            "count": len(rates),
            "source": "realtime",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo cotizaciones: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/history")
async def get_all_rate_history(limit: int = 100):
    """Obtener histórico general desde la base de datos"""
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
    """
    Resumen del mercado USDT/VES
    
    Incluye:
    - Todas las cotizaciones actuales
    - Spread entre BCV y Binance P2P
    - Variaciones 24h
    - Estado del mercado
    """
    try:
        summary = await rates_service.get_market_summary()
        return {
            "status": "success",
            "data": summary
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo resumen: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/binance-p2p")
async def get_binance_p2p_rates():
    """Cotizaciones Binance P2P en tiempo real"""
    return await fetch_binance_p2p_simple()

@app.get("/api/v1/rates/binance-p2p/sell")
async def get_binance_p2p_sell_rates():
    """
    Precios de Venta de USDT (Comprar USDT con VES)
    
    Descripción: Obtiene el mejor precio para comprar USDT con VES
    """
    return await fetch_binance_p2p_sell_simple()

@app.get("/api/v1/rates/binance")
async def get_binance_rate():
    """
    Obtener cotización de Binance P2P Venezuela
    
    Mercado crypto peer-to-peer
    """
    try:
        binance_data = await fetch_binance_p2p_simple()
        if binance_data["status"] == "success":
            return {
                "status": "success",
                "data": {
                    "id": 1,
                    "exchange_code": "binance_p2p",
                    "currency_pair": "USDT/VES",
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

@app.get("/api/v1/rates/binance-p2p/complete")
async def get_binance_p2p_complete():
    """
    Obtener tanto precios de compra como de venta de USDT/VES en Binance P2P
    """
    try:
        print("🟡 Obteniendo precios completos de Binance P2P...")
        
        # Obtener precios de venta (SELL en Binance = vender USDT por VES)
        # IMPORTANTE: NO guardar en BD, solo obtener datos
        sell_result = await _fetch_binance_p2p_rates_no_save()
        
        # Obtener precios de compra (BUY en Binance = comprar USDT con VES)
        # IMPORTANTE: NO guardar en BD, solo obtener datos
        buy_result = await _fetch_binance_p2p_sell_rates_no_save()
        
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
            
            # IMPORTANTE: Solo guardar UNA vez usando el método específico para datos completos
            # NO guardar usando las funciones individuales para evitar duplicados
            try:
                if DATABASE_AVAILABLE:
                    await DatabaseService.save_binance_p2p_complete_rates(complete_result)
                    print("💾 Binance P2P COMPLETE rates guardados en base de datos (UNA SOLA LÍNEA)")
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
    """Scraping en tiempo real del BCV"""
    return await scrape_bcv_simple()

@app.get("/api/v1/rates/bcv")
async def get_bcv_rate():
    """
    Obtener cotización oficial del BCV
    
    Tasa oficial del Banco Central de Venezuela
    """
    try:
        bcv_data = await scrape_bcv_simple()
        if bcv_data["status"] == "success":
            return {
                "status": "success",
                "data": {
                    "id": 1,
                    "exchange_code": "bcv",
                    "currency_pair": "USD/VES",
                    "buy_price": bcv_data["data"]["usd_ves"],
                    "sell_price": bcv_data["data"]["usd_ves"],
                    "avg_price": bcv_data["data"]["usd_ves"],
                    "volume": None,
                    "volume_24h": None,
                    "source": "bcv",
                    "api_method": "web_scraping",
                    "trade_type": "official",
                    "timestamp": bcv_data["data"]["timestamp"],
                    "created_at": bcv_data["data"]["timestamp"]
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
    """
    Comparación de Fuentes
    
    Descripción: Compara cotizaciones entre diferentes fuentes (BCV vs Binance P2P)
    """
    try:
        # Obtener datos del BCV
        bcv_data = await scrape_bcv_simple()
        
        # Obtener datos de Binance P2P (compra y venta)
        binance_buy = await fetch_binance_p2p_simple()
        binance_sell = await fetch_binance_p2p_sell_simple()
        
        if bcv_data["status"] == "success" and binance_buy["status"] == "success" and binance_sell["status"] == "success":
            # Calcular spread entre BCV y Binance P2P
            bcv_usd = bcv_data["data"]["usd_ves"]
            binance_avg = (binance_buy["data"]["usdt_ves_buy"] + binance_sell["data"]["usdt_ves_sell"]) / 2
            
            spread_bcv_binance = bcv_usd - binance_avg
            spread_percentage = (spread_bcv_binance / binance_avg) * 100 if binance_avg > 0 else 0
            
            return {
                "status": "success",
                "data": {
                    "bcv": {
                        "usd_ves": bcv_data["data"]["usd_ves"],
                        "eur_ves": bcv_data["data"]["eur_ves"],
                        "timestamp": bcv_data["data"]["timestamp"]
                    },
                    "binance_p2p": {
                        "usdt_ves_buy": binance_buy["data"]["usdt_ves_buy"],
                        "usdt_ves_sell": binance_sell["data"]["usdt_ves_sell"],
                        "usdt_ves_avg": binance_avg,
                        "timestamp": binance_buy["data"]["timestamp"]
                    },
                    "analysis": {
                        "spread_bcv_binance": round(spread_bcv_binance, 4),
                        "spread_percentage": round(spread_percentage, 2),
                        "timestamp": datetime.now().isoformat()
                    }
                }
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
            "error": f"Error comparando exchanges: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/rates/status")
async def get_rates_status():
    """
    Estado de las cotizaciones y fuentes de datos
    
    Información útil para monitoreo:
    - Última actualización por exchange
    - Estado de conexión a APIs externas
    - Número de cotizaciones disponibles
    """
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
            "data": status
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error obteniendo estado: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/v1/rates/refresh")
async def refresh_rates(exchange_code: str = None):
    """
    Forzar actualización de cotizaciones
    
    Útil para refrescar datos manualmente
    """
    try:
        # Forzar actualización de datos
        if exchange_code == "bcv" or exchange_code is None:
            bcv_result = await scrape_bcv_simple()
        else:
            bcv_result = None
            
        if exchange_code == "binance_p2p" or exchange_code is None:
            binance_result = await fetch_binance_p2p_simple()
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
