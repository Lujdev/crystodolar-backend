"""
Configuración de base de datos con SQLAlchemy + AsyncPG
Compatible con Neon.tech PostgreSQL serverless
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from loguru import logger
from typing import AsyncGenerator
import asyncio

from app.core.config import settings


class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy"""
    pass


# Engine asíncrono para Neon.tech
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.API_DEBUG,  # Log SQL queries en desarrollo
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verificar conexiones antes de usar
    pool_recycle=300,  # Reciclar conexiones cada 5 minutos
    # Configuración específica para Neon.tech y asyncpg
    connect_args={
        "server_settings": {
            "application_name": "crystoapivzla_api",
        }
    }
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener sesión de base de datos
    Se usa en FastAPI endpoints con Depends()
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Inicializar base de datos
    - Verificar conexión
    - Crear tablas si no existen (opcional)
    """
    try:
        # Verificar conexión
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info("✅ Conexión a Neon.tech establecida correctamente")
            
        # Opcional: Crear tablas automáticamente
        # En producción es mejor usar Alembic migrations
        if settings.is_development:
            # async with engine.begin() as conn:
            #     await conn.run_sync(Base.metadata.create_all)
            #     logger.info("✅ Tablas de desarrollo creadas")
            pass
            
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        raise


async def close_db() -> None:
    """
    Cerrar conexiones de base de datos
    Se ejecuta al cerrar la aplicación
    """
    try:
        await engine.dispose()
        logger.info("✅ Conexiones de base de datos cerradas")
    except Exception as e:
        logger.error(f"Error cerrando base de datos: {e}")


async def health_check_db() -> bool:
    """
    Health check de base de datos
    Retorna True si la conexión está activa
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def execute_raw_sql(query: str, params: dict = None) -> any:
    """
    Ejecutar SQL raw de forma segura
    Útil para consultas complejas o funciones específicas
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result
    except Exception as e:
        logger.error(f"Error executing raw SQL: {e}")
        raise


# Funciones de utilidad para Neon.tech

async def get_connection_info() -> dict:
    """
    Obtener información de la conexión actual
    Útil para debugging y monitoreo
    """
    try:
        async with async_session_maker() as session:
            queries = [
                "SELECT current_database() as database",
                "SELECT current_user as user",
                "SELECT inet_server_addr() as server_ip",
                "SELECT version() as postgres_version",
                "SELECT count(*) as active_connections FROM pg_stat_activity",
            ]
            
            info = {}
            for query in queries:
                result = await session.execute(text(query))
                row = result.fetchone()
                if row:
                    info.update(dict(row._mapping))
                    
            return info
    except Exception as e:
        logger.error(f"Error getting connection info: {e}")
        return {"error": str(e)}


async def cleanup_old_data() -> dict:
    """
    Ejecutar limpieza de datos antiguos
    Equivalente a la función cleanup_old_data() del SQL
    """
    try:
        async with async_session_maker() as session:
            # Limpiar rate_history > 90 días
            result1 = await session.execute(text("""
                DELETE FROM rate_history 
                WHERE timestamp < NOW() - INTERVAL '90 days'
            """))
            
            # Limpiar api_logs > 30 días
            result2 = await session.execute(text("""
                DELETE FROM api_logs 
                WHERE timestamp < NOW() - INTERVAL '30 days'
            """))
            
            await session.commit()
            
            return {
                "rate_history_deleted": result1.rowcount,
                "api_logs_deleted": result2.rowcount,
                "timestamp": "now()"
            }
            
    except Exception as e:
        logger.error(f"Error in cleanup_old_data: {e}")
        raise
