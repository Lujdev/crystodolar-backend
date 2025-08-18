"""
Servicio para operaciones de base de datos
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from loguru import logger
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.core.database import get_db_session
from app.models.rate_models import RateHistory, CurrentRate
from app.models.exchange_models import Exchange, CurrencyPair
from app.models.api_models import ApiLog


class DatabaseService:
    """
    Servicio para operaciones CRUD en la base de datos
    """
    
    @staticmethod
    async def save_bcv_rates(usd_ves: float, eur_ves: float, source_data: Dict[str, Any]) -> bool:
        """
        Guardar cotizaciones del BCV
        """
        try:
            async for session in get_db_session():
                # Guardar en historial
                rate_history = RateHistory(
                    exchange_code="BCV",
                    currency_pair="USD/VES",
                    buy_price=usd_ves,
                    sell_price=usd_ves,  # BCV tiene un solo precio
                    avg_price=usd_ves,
                    source="bcv",
                    api_method="web_scraping",
                    timestamp=datetime.now()
                )
                session.add(rate_history)
                
                # Guardar EUR también
                eur_history = RateHistory(
                    exchange_code="BCV",
                    currency_pair="EUR/VES",
                    buy_price=eur_ves,
                    sell_price=eur_ves,
                    avg_price=eur_ves,
                    source="bcv",
                    api_method="web_scraping",
                    timestamp=datetime.now()
                )
                session.add(eur_history)
                
                # Actualizar cotizaciones actuales
                await DatabaseService._update_current_rate(
                    session, "BCV", "USD/VES", usd_ves, usd_ves, usd_ves
                )
                await DatabaseService._update_current_rate(
                    session, "BCV", "EUR/VES", eur_ves, eur_ves, eur_ves
                )
                
                await session.commit()
                logger.info(f"✅ BCV rates guardados: USD={usd_ves}, EUR={eur_ves}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error guardando BCV rates: {e}")
            return False
    
    @staticmethod
    async def save_binance_p2p_rates(binance_data: Dict[str, Any]) -> bool:
        """
        Guardar cotizaciones de Binance P2P (un precio a la vez)
        """
        try:
            async for session in get_db_session():
                # Extraer datos
                buy_price = binance_data.get("usdt_ves_buy")
                sell_price = binance_data.get("usdt_ves_sell")
                avg_price = binance_data.get("usdt_ves_avg")
                volume = binance_data.get("volume_24h")
                source = binance_data.get("source", "binance_p2p")
                
                if buy_price:
                    # Guardar precio de compra
                    buy_history = RateHistory(
                        exchange_code="BINANCE_P2P",
                        currency_pair="USDT/VES",
                        buy_price=buy_price,
                        sell_price=None,
                        avg_price=avg_price,
                        volume_24h=volume,
                        source=source,
                        api_method="official_api",
                        trade_type="buy_usdt",
                        timestamp=datetime.now()
                    )
                    session.add(buy_history)
                
                if sell_price:
                    # Guardar precio de venta
                    sell_history = RateHistory(
                        exchange_code="BINANCE_P2P",
                        currency_pair="USDT/VES",
                        buy_price=None,
                        sell_price=sell_price,
                        avg_price=avg_price,
                        volume_24h=volume,
                        source=source,
                        api_method="official_api",
                        trade_type="sell_usdt",
                        timestamp=datetime.now()
                    )
                    session.add(sell_history)
                
                # Actualizar cotizaciones actuales
                # Si solo tenemos un precio, usarlo para ambos campos temporalmente
                if buy_price or sell_price:
                    # Si solo tenemos buy_price, usarlo como sell_price también
                    # Si solo tenemos sell_price, usarlo como buy_price también
                    final_buy_price = buy_price if buy_price else sell_price
                    final_sell_price = sell_price if sell_price else buy_price
                    
                    await DatabaseService._update_current_rate(
                        session, "BINANCE_P2P", "USDT/VES", final_buy_price, final_sell_price, avg_price, volume
                    )
                
                await session.commit()
                logger.info(f"✅ Binance P2P rates guardados: Buy={buy_price}, Sell={sell_price}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error guardando Binance P2P rates: {e}")
            return False

    @staticmethod
    async def save_binance_p2p_complete_rates(binance_data: Dict[str, Any]) -> bool:
        """
        Guardar cotizaciones COMPLETAS de Binance P2P (ambos precios simultáneamente)
        """
        try:
            async for session in get_db_session():
                # Extraer datos del endpoint complete
                buy_data = binance_data.get("buy_usdt", {})
                sell_data = binance_data.get("sell_usdt", {})
                market_analysis = binance_data.get("market_analysis", {})
                
                # Precios
                buy_price = buy_data.get("price")
                sell_price = sell_data.get("price")
                buy_avg = buy_data.get("avg_price")
                sell_avg = sell_data.get("avg_price")
                
                # Volumen combinado
                volume_24h = market_analysis.get("volume_24h", 0)
                source = binance_data.get("source", "binance_p2p")
                
                # Guardar UNA SOLA LÍNEA con ambos precios
                if buy_price and sell_price:
                    complete_history = RateHistory(
                        exchange_code="BINANCE_P2P",
                        currency_pair="USDT/VES",
                        buy_price=buy_price,
                        sell_price=sell_price,
                        avg_price=(buy_price + sell_price) / 2,  # Promedio de ambos precios
                        volume_24h=volume_24h,
                        source=source,
                        api_method="official_api",
                        trade_type="complete_usdt",  # Indicar que es un registro completo
                        timestamp=datetime.now()
                    )
                    session.add(complete_history)
                    
                    logger.info(f"✅ Registro COMPLETO guardado: Buy={buy_price}, Sell={sell_price}")
                else:
                    logger.warning(f"⚠️ No se pudieron obtener ambos precios para guardar registro completo")
                
                # Actualizar cotizaciones actuales con AMBOS precios
                if buy_price and sell_price:
                    # Calcular precio promedio general
                    general_avg = (buy_price + sell_price) / 2
                    
                    await DatabaseService._update_current_rate(
                        session, "BINANCE_P2P", "USDT/VES", 
                        buy_price, sell_price, general_avg, volume_24h
                    )
                    
                    logger.info(f"✅ Binance P2P COMPLETE rates guardados: Buy={buy_price}, Sell={sell_price}, Avg={general_avg}")
                else:
                    logger.warning(f"⚠️ No se pudieron obtener ambos precios para actualizar current_rates")
                
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Error guardando Binance P2P COMPLETE rates: {e}")
            return False
    
    @staticmethod
    async def _update_current_rate(
        session: AsyncSession, 
        exchange_code: str, 
        currency_pair: str, 
        buy_price: float, 
        sell_price: float, 
        avg_price: float,
        volume_24h: Optional[float] = None
    ) -> None:
        """
        Actualizar o crear cotización actual
        """
        # Buscar si ya existe
        stmt = select(CurrentRate).where(
            CurrentRate.exchange_code == exchange_code,
            CurrentRate.currency_pair == currency_pair
        )
        result = await session.execute(stmt)
        current_rate = result.scalar_one_or_none()
        
        if current_rate:
            # Actualizar existente
            current_rate.buy_price = buy_price
            current_rate.sell_price = sell_price
            current_rate.avg_price = avg_price
            if volume_24h:
                current_rate.volume_24h = volume_24h
            current_rate.last_update = datetime.now()
            current_rate.market_status = "active"
        else:
            # Crear nuevo
            current_rate = CurrentRate(
                exchange_code=exchange_code,
                currency_pair=currency_pair,
                buy_price=buy_price,
                sell_price=sell_price,
                avg_price=avg_price,
                volume_24h=volume_24h,
                source=exchange_code.lower(),
                market_status="active",
                last_update=datetime.now()
            )
            session.add(current_rate)
    
    @staticmethod
    async def get_latest_rates(limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtener las últimas cotizaciones
        """
        try:
            async for session in get_db_session():
                stmt = select(RateHistory).order_by(
                    RateHistory.timestamp.desc()
                ).limit(limit)
                
                result = await session.execute(stmt)
                rates = result.scalars().all()
                
                return [
                    {
                        "id": rate.id,
                        "exchange_code": rate.exchange_code,
                        "currency_pair": rate.currency_pair,
                        "buy_price": rate.buy_price,
                        "sell_price": rate.sell_price,
                        "avg_price": rate.avg_price,
                        "volume_24h": rate.volume_24h,
                        "source": rate.source,
                        "trade_type": rate.trade_type,
                        "timestamp": rate.timestamp.isoformat() if rate.timestamp else None
                    }
                    for rate in rates
                ]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo latest rates: {e}")
            return []
    
    @staticmethod
    async def get_current_rates() -> List[Dict[str, Any]]:
        """
        Obtener cotizaciones actuales
        """
        try:
            async for session in get_db_session():
                stmt = select(CurrentRate).options(
                    selectinload(CurrentRate.exchange),
                    selectinload(CurrentRate.currency_pair_rel)
                ).where(CurrentRate.market_status == "active")
                
                result = await session.execute(stmt)
                current_rates = result.scalars().all()
                
                rates_with_variation = []
                for rate in current_rates:
                    # Calcular variación avanzada con diferentes períodos de tiempo
                    variation_data = await DatabaseService._calculate_variation_advanced(
                        session, rate.exchange_code, rate.currency_pair, rate.avg_price
                    )
                    
                    # Formatear variaciones como porcentajes con símbolo %
                    variation_main_formatted = f"{variation_data['variation_main']:+.2f}%" if variation_data['variation_main'] != 0 else "0.00%"
                    variation_1h_formatted = f"{variation_data['variation_1h']:+.2f}%" if variation_data['variation_1h'] != 0 else "0.00%"
                    variation_24h_formatted = f"{variation_data['variation_24h']:+.2f}%" if variation_data['variation_24h'] != 0 else "0.00%"
                    
                    rates_with_variation.append({
                        "exchange_code": rate.exchange_code,
                        "currency_pair": rate.currency_pair,
                        "base_currency": rate.currency_pair_rel.base_currency if rate.currency_pair_rel else None,
                        "quote_currency": rate.currency_pair_rel.quote_currency if rate.currency_pair_rel else None,
                        "buy_price": rate.buy_price,
                        "sell_price": rate.sell_price,
                        "avg_price": rate.avg_price,
                        "volume_24h": rate.volume_24h,
                        "source": rate.source,
                        "last_update": rate.last_update.isoformat() if rate.last_update else None,
                        "market_status": rate.market_status,
                        "variation_percentage": variation_main_formatted,  # Usar la variación principal (último valor registrado)
                        "variation_1h": variation_1h_formatted,
                        "variation_24h": variation_24h_formatted,
                        "variation_main_raw": variation_data["variation_main"],  # Valor numérico para cálculos
                        "variation_1h_raw": variation_data["variation_1h"],  # Valor numérico para cálculos
                        "variation_24h_raw": variation_data["variation_24h"],  # Valor numérico para cálculos
                        "trend_main": variation_data["trend_main"],  # Tendencia principal
                        "trend_1h": variation_data["trend_1h"],
                        "trend_24h": variation_data["trend_24h"]
                    })
                
                return rates_with_variation
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo current rates: {e}")
            return []
    
    @staticmethod
    async def _calculate_variation_percentage(session, exchange_code: str, currency_pair: str, current_price: float) -> float:
        """
        Calcular el porcentaje de variación basado en la diferencia entre los dos últimos valores de rate_history
        """
        try:
            from sqlalchemy import select, func
            from app.models.rate_models import RateHistory
            
            # Obtener los dos últimos precios registrados en rate_history para este exchange y currency_pair
            stmt = select(RateHistory.avg_price).where(
                RateHistory.exchange_code == exchange_code,
                RateHistory.currency_pair == currency_pair
            ).order_by(RateHistory.timestamp.desc()).limit(2)
            
            result = await session.execute(stmt)
            price_rows = result.fetchall()
            
            if len(price_rows) >= 2:
                last_price = float(price_rows[0][0])  # Primer precio (más reciente)
                second_last_price = float(price_rows[1][0])  # Segundo precio (penúltimo)
                
                if second_last_price > 0:
                    # Calcular variación porcentual entre los dos últimos valores
                    variation = ((last_price - second_last_price) / second_last_price) * 100
                    return round(variation, 4)
            
            return 0.0
                
        except Exception as e:
            logger.error(f"❌ Error calculando variación para {exchange_code} {currency_pair}: {e}")
            return 0.0
    
    @staticmethod
    async def _calculate_variation_advanced(session, exchange_code: str, currency_pair: str, current_price: float) -> dict:
        """
        Calcular variación avanzada comparando con el penúltimo valor registrado en rate_history
        """
        try:
            from sqlalchemy import select, func
            from app.models.rate_models import RateHistory
            from datetime import datetime, timedelta
            
            # Obtener los dos últimos precios registrados en rate_history para este exchange y currency_pair
            # Ordenar por timestamp descendente para obtener el más reciente
            stmt_last = select(RateHistory.avg_price).where(
                RateHistory.exchange_code == exchange_code,
                RateHistory.currency_pair == currency_pair
            ).order_by(RateHistory.timestamp.desc()).limit(2)
            
            result_last = await session.execute(stmt_last)
            price_rows = result_last.fetchall()
            
            # Calcular variación principal (comparando entre los dos últimos valores registrados)
            variation_main = 0.0
            if len(price_rows) >= 2:
                last_price = float(price_rows[0][0])  # Primer precio (más reciente)
                second_last_price = float(price_rows[1][0])  # Segundo precio (penúltimo)
                
                if second_last_price > 0:
                    variation_main = ((last_price - second_last_price) / second_last_price) * 100
                    variation_main = round(variation_main, 4)
            
            # Para mantener compatibilidad, también calculamos variaciones por tiempo
            # pero solo si hay datos suficientes
            now = datetime.utcnow()
            
            # Variación en la última hora (si hay datos)
            one_hour_ago = now - timedelta(hours=1)
            stmt_1h = select(RateHistory.avg_price).where(
                RateHistory.exchange_code == exchange_code,
                RateHistory.currency_pair == currency_pair,
                RateHistory.timestamp >= one_hour_ago
            ).order_by(RateHistory.timestamp.desc()).limit(1)
            
            result_1h = await session.execute(stmt_1h)
            price_1h = result_1h.scalar()
            
            # Variación en las últimas 24 horas (si hay datos)
            one_day_ago = now - timedelta(days=1)
            stmt_24h = select(RateHistory.avg_price).where(
                RateHistory.exchange_code == exchange_code,
                RateHistory.currency_pair == currency_pair,
                RateHistory.timestamp >= one_day_ago
            ).order_by(RateHistory.timestamp.desc()).limit(1)
            
            result_24h = await session.execute(stmt_24h)
            price_24h = result_24h.scalar()
            
            # Calcular variaciones por tiempo
            variation_1h = 0.0
            variation_24h = 0.0
            
            if price_1h and current_price and price_1h > 0:
                variation_1h = ((current_price - price_1h) / price_1h) * 100
                variation_1h = round(variation_1h, 4)
            
            if price_24h and current_price and price_24h > 0:
                variation_24h = ((current_price - price_24h) / price_24h) * 100
                variation_24h = round(variation_24h, 4)
            
            return {
                "variation_main": variation_main,  # Nueva variación principal
                "variation_1h": variation_1h,
                "variation_24h": variation_24h,
                "trend_main": "up" if variation_main > 0 else "down" if variation_main < 0 else "stable",
                "trend_1h": "up" if variation_1h > 0 else "down" if variation_1h < 0 else "stable",
                "trend_24h": "up" if variation_24h > 0 else "down" if variation_24h < 0 else "stable"
            }
                
        except Exception as e:
            logger.error(f"❌ Error calculando variación avanzada para {exchange_code} {currency_pair}: {e}")
            return {
                "variation_1h": 0.0,
                "variation_24h": 0.0,
                "trend_1h": "stable",
                "trend_24h": "stable"
            }
    
    @staticmethod
    async def log_api_call(
        endpoint: str,
        method: str,
        status_code: int,
        source: Optional[str] = None,
        operation_type: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None
    ) -> None:
        """
        Registrar llamada a la API
        """
        try:
            async for session in get_db_session():
                api_log = ApiLog(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    source=source,
                    operation_type=operation_type,
                    response_time_ms=response_time_ms,
                    request_data=request_data,
                    response_data=response_data,
                    success=status_code < 400,
                    timestamp=datetime.now()
                )
                
                session.add(api_log)
                await session.commit()
                
        except Exception as e:
            logger.error(f"❌ Error loggeando API call: {e}")
    
    @staticmethod
    async def cleanup_old_data() -> Dict[str, int]:
        """
        Limpiar datos antiguos
        """
        try:
            async for session in get_db_session():
                # Limpiar rate_history > 90 días
                stmt = delete(RateHistory).where(
                    RateHistory.timestamp < datetime.now() - timedelta(days=90)
                )
                result1 = await session.execute(stmt)
                
                # Limpiar api_logs > 30 días
                stmt2 = delete(ApiLog).where(
                    ApiLog.timestamp < datetime.now() - timedelta(days=30)
                )
                result2 = await session.execute(stmt2)
                
                await session.commit()
                
                return {
                    "rate_history_deleted": result1.rowcount,
                    "api_logs_deleted": result2.rowcount,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error en cleanup: {e}")
            return {"error": str(e)}
