"""
Endpoints para cotizaciones USDT/VES
BCV (fiat) y Binance P2P (crypto)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db_session
from app.schemas.rates import (
    RateResponse, 
    RateHistoryResponse, 
    MarketSummaryResponse,
    RateCreate
)
from app.services.rates_service import RatesService
from app.services.data_fetcher import scrape_bcv_rates

router = APIRouter()


@router.get("/", response_model=List[RateResponse])
async def get_current_rates(
    exchange_code: Optional[str] = Query(None, description="Filtrar por exchange (bcv, binance_p2p)"),
    currency_pair: Optional[str] = Query(None, description="Filtrar por par (USDT/VES)"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Obtener cotizaciones actuales de USDT/VES
    
    - **exchange_code**: Filtrar por exchange específico
    - **currency_pair**: Filtrar por par de monedas
    """
    rates_service = RatesService(db)
    
    try:
        rates = await rates_service.get_current_rates(
            exchange_code=exchange_code,
            currency_pair=currency_pair
        )
        return rates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo cotizaciones: {str(e)}")


@router.get("/scrape-bcv")
async def scrape_bcv_live(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Hacer scraping en tiempo real del BCV
    
    Endpoint para probar el web scraping del Banco Central de Venezuela
    Retorna las cotizaciones del dólar y euro obtenidas directamente del sitio web
    Incluye exchange_code de current_rates y base_currency de currency_pairs
    """
    try:
        # Obtener datos del scraping del BCV
        result = await scrape_bcv_rates()
        
        # Si el scraping fue exitoso, obtener información adicional de la BD
        if result.get("status") == "success":
            try:
                # Consultar exchange_code desde current_rates y base_currency desde currency_pairs
                from sqlalchemy import select
                from app.models.rate_models import CurrentRate
                from app.models.exchange_models import CurrencyPair
                
                # Buscar el exchange_code para BCV en current_rates
                stmt_current = select(CurrentRate.exchange_code).where(
                    CurrentRate.exchange_code == "bcv"
                ).limit(1)
                
                # Buscar el base_currency para USD/VES en currency_pairs
                stmt_currency = select(CurrencyPair.base_currency).where(
                    CurrencyPair.symbol == "USD/VES"
                ).limit(1)
                
                # Ejecutar consultas
                result_current = await db.execute(stmt_current)
                result_currency = await db.execute(stmt_currency)
                
                exchange_code = result_current.scalar()
                base_currency = result_currency.scalar()
                
                # Agregar la información de la BD al resultado
                if result.get("data"):
                    result["data"]["exchange_code"] = exchange_code
                    result["data"]["base_currency"] = base_currency
                    result["data"]["database_info"] = {
                        "exchange_code": exchange_code,
                        "base_currency": base_currency,
                        "source": "database"
                    }
                
            except Exception as db_error:
                # Si hay error en la BD, continuar sin esa información
                if result.get("data"):
                    result["data"]["database_info"] = {
                        "error": f"Error consultando BD: {str(db_error)}",
                        "source": "scraping_only"
                    }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en scraping del BCV: {str(e)}")


@router.get("/summary", response_model=MarketSummaryResponse)
async def get_market_summary(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Resumen del mercado USDT/VES
    
    Incluye:
    - Todas las cotizaciones actuales
    - Spread entre BCV y Binance P2P
    - Variaciones 24h
    - Estado del mercado
    """
    rates_service = RatesService(db)
    
    try:
        summary = await rates_service.get_market_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen: {str(e)}")


@router.get("/history", response_model=List[RateHistoryResponse])
async def get_rate_history(
    exchange_code: str = Query(..., description="Exchange (bcv, binance_p2p)"),
    currency_pair: str = Query("USDT/VES", description="Par de monedas"),
    timeframe: str = Query("7d", description="Periodo (1d, 7d, 1m, 3m, 6m, 1y)"),
    interval: str = Query("1h", description="Intervalo (15m, 1h, 4h, 1d)"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Obtener histórico de cotizaciones para gráficas
    
    - **exchange_code**: Exchange específico
    - **currency_pair**: Par de monedas (USDT/VES)
    - **timeframe**: Periodo de tiempo
    - **interval**: Intervalo entre puntos
    """
    rates_service = RatesService(db)
    
    try:
        history = await rates_service.get_rate_history(
            exchange_code=exchange_code,
            currency_pair=currency_pair,
            timeframe=timeframe,
            interval=interval
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo histórico: {str(e)}")


@router.get("/compare")
async def compare_exchanges(
    currency_pair: str = Query("USDT/VES", description="Par de monedas"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Comparar cotizaciones entre diferentes exchanges
    
    Útil para calcular el spread y diferencias entre:
    - BCV (oficial)
    - Binance P2P (mercado crypto)
    """
    rates_service = RatesService(db)
    
    try:
        comparison = await rates_service.compare_exchanges(currency_pair)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparando exchanges: {str(e)}")


@router.get("/bcv", response_model=RateResponse)
async def get_bcv_rate(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Obtener cotización oficial del BCV
    
    Tasa oficial del Banco Central de Venezuela
    """
    rates_service = RatesService(db)
    
    try:
        rate = await rates_service.get_bcv_rate()
        if not rate:
            raise HTTPException(status_code=404, detail="Cotización BCV no encontrada")
        return rate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo BCV: {str(e)}")


@router.get("/binance", response_model=RateResponse)
async def get_binance_rate(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Obtener cotización de Binance P2P Venezuela
    
    Mercado crypto peer-to-peer
    """
    rates_service = RatesService(db)
    
    try:
        rate = await rates_service.get_binance_rate()
        if not rate:
            raise HTTPException(status_code=404, detail="Cotización Binance P2P no encontrada")
        return rate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo Binance P2P: {str(e)}")


@router.post("/", response_model=RateResponse)
async def create_rate(
    rate_data: RateCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Crear nueva cotización (admin)
    
    Solo para testing y admin manual
    """
    rates_service = RatesService(db)
    
    try:
        rate = await rates_service.create_rate(rate_data)
        return rate
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando cotización: {str(e)}")


@router.get("/status")
async def get_rates_status(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Estado de las cotizaciones y fuentes de datos
    
    Información útil para monitoreo:
    - Última actualización por exchange
    - Estado de conexión a APIs externas
    - Número de cotizaciones disponibles
    """
    rates_service = RatesService(db)
    
    try:
        status = await rates_service.get_rates_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")


@router.post("/refresh")
async def refresh_rates(
    exchange_code: Optional[str] = Query(None, description="Exchange específico a actualizar"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Forzar actualización de cotizaciones
    
    Útil para refrescar datos manualmente
    """
    rates_service = RatesService(db)
    
    try:
        result = await rates_service.refresh_rates(exchange_code)
        return {
            "message": "Actualización iniciada",
            "exchanges_updated": result.get("exchanges", []),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando cotizaciones: {str(e)}")


# WebSocket endpoint para real-time (futuro)
# @router.websocket("/ws")
# async def websocket_rates(websocket: WebSocket):
#     """
#     WebSocket para cotizaciones en tiempo real
#     """
#     await websocket.accept()
#     try:
#         while True:
#             # TODO: Enviar updates de cotizaciones
#             await asyncio.sleep(5)
#     except WebSocketDisconnect:
#         pass
