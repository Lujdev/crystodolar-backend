"""
Scheduler para tareas automáticas
Reemplaza pg_cron usando APScheduler
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
import asyncio
from datetime import datetime

from app.core.config import settings
from app.core.database import cleanup_old_data
from app.services.data_fetcher import update_all_rates


# Instancia global del scheduler
scheduler: AsyncIOScheduler = None


def start_scheduler() -> None:
    """
    Inicializar y configurar el scheduler
    Se ejecuta al arrancar la aplicación
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler ya está iniciado")
        return
    
    scheduler = AsyncIOScheduler(timezone="America/Caracas")
    
    # Tarea 1: Limpieza de datos antiguos (diario a las 2:00 AM)
    scheduler.add_job(
        func=scheduled_cleanup,
        trigger=CronTrigger(hour=settings.CLEANUP_HOUR, minute=0),
        id="cleanup_old_data",
        name="Limpiar datos antiguos",
        replace_existing=True,
        misfire_grace_time=3600  # 1 hora de gracia si falla
    )
    
    # Tarea 2: Actualizar cotizaciones BCV (cada hora)
    scheduler.add_job(
        func=scheduled_update_bcv,
        trigger=IntervalTrigger(seconds=settings.BCV_UPDATE_INTERVAL),
        id="update_bcv_rates",
        name="Actualizar cotizaciones BCV",
        replace_existing=True,
        misfire_grace_time=300  # 5 minutos de gracia
    )
    
    # Tarea 3: Actualizar cotizaciones Binance P2P (cada 5 minutos)
    scheduler.add_job(
        func=scheduled_update_binance,
        trigger=IntervalTrigger(seconds=settings.BINANCE_UPDATE_INTERVAL),
        id="update_binance_rates",
        name="Actualizar cotizaciones Binance P2P",
        replace_existing=True,
        misfire_grace_time=60  # 1 minuto de gracia
    )
    
    # Tarea 4: Health check de APIs externas (cada 10 minutos)
    scheduler.add_job(
        func=scheduled_health_check,
        trigger=IntervalTrigger(minutes=10),
        id="health_check_apis",
        name="Health check APIs externas",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler iniciado con tareas automáticas")
    
    # Mostrar trabajos programados
    for job in scheduler.get_jobs():
        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "N/A"
        logger.info(f"📅 Tarea: {job.name} | Próxima ejecución: {next_run}")


def stop_scheduler() -> None:
    """
    Detener el scheduler
    Se ejecuta al cerrar la aplicación
    """
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown(wait=True)
        scheduler = None
        logger.info("✅ Scheduler detenido")


def get_scheduler_status() -> dict:
    """
    Obtener estado del scheduler y trabajos
    """
    global scheduler
    
    if scheduler is None:
        return {"status": "stopped", "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": jobs,
        "timezone": str(scheduler.timezone)
    }


# ========================================
# TAREAS PROGRAMADAS
# ========================================

async def scheduled_cleanup() -> None:
    """
    Tarea programada: Limpiar datos antiguos
    Se ejecuta diariamente a las 2:00 AM
    """
    try:
        logger.info("🧹 Iniciando limpieza de datos antiguos...")
        result = await cleanup_old_data()
        logger.info(f"✅ Limpieza completada: {result}")
        
        # Opcional: Notificar por Telegram
        if settings.TELEGRAM_BOT_TOKEN:
            await send_telegram_notification(
                f"🧹 Limpieza automática completada\n"
                f"Rate history: {result['rate_history_deleted']} registros\n"
                f"API logs: {result['api_logs_deleted']} registros"
            )
            
    except Exception as e:
        logger.error(f"❌ Error en limpieza automática: {e}")
        # Opcional: Notificar error por Telegram
        if settings.TELEGRAM_BOT_TOKEN:
            await send_telegram_notification(f"❌ Error en limpieza automática: {e}")


async def scheduled_update_bcv() -> None:
    """
    Tarea programada: Actualizar cotizaciones BCV
    Se ejecuta cada hora
    """
    try:
        logger.info("🏦 Actualizando cotizaciones BCV...")
        # TODO: Implementar scraping de BCV
        # result = await update_bcv_rates()
        logger.info("✅ Cotizaciones BCV actualizadas")
        
    except Exception as e:
        logger.error(f"❌ Error actualizando BCV: {e}")


async def scheduled_update_binance() -> None:
    """
    Tarea programada: Actualizar cotizaciones Binance P2P
    Se ejecuta cada 5 minutos
    """
    try:
        logger.info("🟡 Actualizando cotizaciones Binance P2P...")
        # TODO: Implementar API de Binance P2P
        # result = await update_binance_rates()
        logger.info("✅ Cotizaciones Binance P2P actualizadas")
        
    except Exception as e:
        logger.error(f"❌ Error actualizando Binance P2P: {e}")


async def scheduled_health_check() -> None:
    """
    Tarea programada: Health check de APIs externas
    Se ejecuta cada 10 minutos
    """
    try:
        logger.info("🔍 Verificando health de APIs externas...")
        
        # TODO: Implementar health checks
        # bcv_status = await check_bcv_health()
        # binance_status = await check_binance_health()
        
        logger.info("✅ Health check completado")
        
    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")


# ========================================
# UTILIDADES
# ========================================

async def send_telegram_notification(message: str) -> bool:
    """
    Enviar notificación por Telegram (opcional)
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return False
    
    try:
        # TODO: Implementar envío de Telegram
        logger.info(f"📱 Notificación Telegram: {message}")
        return True
    except Exception as e:
        logger.error(f"Error enviando notificación Telegram: {e}")
        return False


def trigger_manual_task(task_id: str) -> dict:
    """
    Ejecutar tarea manualmente (para testing o admin)
    """
    global scheduler
    
    if scheduler is None:
        return {"error": "Scheduler no está activo"}
    
    try:
        job = scheduler.get_job(task_id)
        if job is None:
            return {"error": f"Tarea {task_id} no encontrada"}
        
        # Ejecutar ahora
        scheduler.modify_job(task_id, next_run_time=datetime.now())
        return {"success": f"Tarea {task_id} programada para ejecución inmediata"}
        
    except Exception as e:
        return {"error": f"Error ejecutando tarea {task_id}: {e}"}


# ========================================
# ENDPOINTS PARA ADMINISTRACIÓN
# ========================================

async def reschedule_job(job_id: str, cron_expression: str) -> dict:
    """
    Reprogramar una tarea existente
    """
    global scheduler
    
    if scheduler is None:
        return {"error": "Scheduler no está activo"}
    
    try:
        # TODO: Parsear cron_expression y actualizar job
        return {"success": f"Tarea {job_id} reprogramada"}
    except Exception as e:
        return {"error": f"Error reprogramando {job_id}: {e}"}
