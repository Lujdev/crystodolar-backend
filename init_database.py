#!/usr/bin/env python3
"""
Script para inicializar la base de datos de CrystoAPIVzla
Ejecutar: python3.12 init_database.py
"""

import asyncio
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_db, engine
from app.models import RateHistory, CurrentRate, Exchange, CurrencyPair, ApiLog
from app.core.database import Base
from loguru import logger


async def create_tables():
    """Crear todas las tablas"""
    try:
        logger.info("🏗️ Creando tablas de la base de datos...")
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Todas las tablas creadas exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {e}")
        return False


async def insert_initial_data():
    """Insertar datos iniciales"""
    try:
        logger.info("📝 Insertando datos iniciales...")
        
        from app.core.database import async_session_maker
        
        async with async_session_maker() as session:
            # Insertar exchanges
            exchanges = [
                Exchange(
                    code="BCV",
                    name="Banco Central de Venezuela",
                    type="centralized",
                    description="Banco central oficial de Venezuela",
                    operating_hours="24/7",
                    update_frequency="daily",
                    website="https://www.bcv.org.ve/"
                ),
                Exchange(
                    code="BINANCE_P2P",
                    name="Binance P2P",
                    type="p2p",
                    description="Plataforma P2P de Binance para Venezuela",
                    operating_hours="24/7",
                    update_frequency="realtime",
                    website="https://p2p.binance.com/"
                )
            ]
            
            for exchange in exchanges:
                session.add(exchange)
            
            # Insertar pares de divisas
            currency_pairs = [
                CurrencyPair(
                    symbol="USD/VES",
                    base_currency="USD",
                    quote_currency="VES",
                    description="Dólar estadounidense vs Bolívar venezolano",
                    precision=4
                ),
                CurrencyPair(
                    symbol="EUR/VES",
                    base_currency="EUR",
                    quote_currency="VES",
                    description="Euro vs Bolívar venezolano",
                    precision=4
                ),
                CurrencyPair(
                    symbol="USDT/VES",
                    base_currency="USDT",
                    quote_currency="VES",
                    description="Tether vs Bolívar venezolano",
                    precision=4
                )
            ]
            
            for pair in currency_pairs:
                session.add(pair)
            
            await session.commit()
            logger.info("✅ Datos iniciales insertados exitosamente")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error insertando datos iniciales: {e}")
        return False


async def main():
    """Función principal"""
    logger.info("🚀 Iniciando inicialización de base de datos...")
    
    try:
        # 1. Inicializar conexión
        await init_db()
        
        # 2. Crear tablas
        if not await create_tables():
            logger.error("❌ No se pudieron crear las tablas")
            return
        
        # 3. Insertar datos iniciales
        if not await insert_initial_data():
            logger.error("❌ No se pudieron insertar los datos iniciales")
            return
        
        logger.info("🎉 Base de datos inicializada completamente!")
        logger.info("📊 Estructura creada:")
        logger.info("   • Tabla: exchanges")
        logger.info("   • Tabla: currency_pairs")
        logger.info("   • Tabla: rate_history")
        logger.info("   • Tabla: current_rates")
        logger.info("   • Tabla: api_logs")
        
    except Exception as e:
        logger.error(f"❌ Error en inicialización: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
