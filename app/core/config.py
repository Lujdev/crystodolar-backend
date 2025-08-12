"""
Configuración de la aplicación
Manejo de variables de entorno con Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """
    Configuración de la aplicación usando variables de entorno
    Compatible con Neon.tech y despliegue en producción
    """
    
    # Database (Neon.tech)
    DATABASE_URL: str = "postgresql://localhost/crystodolar"
    NEON_ENDPOINT: Optional[str] = None
    NEON_DATABASE: str = "crystodolar"
    NEON_USERNAME: Optional[str] = None
    NEON_PASSWORD: Optional[str] = None
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True
    API_RELOAD: bool = True
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = "change-this-super-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # External APIs
    BCV_API_URL: str = "http://www.bcv.org.ve/"
    BINANCE_API_URL: str = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    # Cache (Redis - opcional)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_ENABLED: bool = False
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 60
    BURST_LIMIT: int = 10
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://crystodolar.com",
        "https://www.crystodolar.com"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Background Tasks
    SCHEDULER_ENABLED: bool = True
    CLEANUP_HOUR: int = 2
    UPDATE_FREQUENCY_SECONDS: int = 300
    
    # Notifications
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    EMAIL_ENABLED: bool = False
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Data Sources Config
    BCV_UPDATE_INTERVAL: int = 3600  # 1 hora
    BINANCE_UPDATE_INTERVAL: int = 300  # 5 minutos
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 30
    
    # Computed properties
    @property
    def is_production(self) -> bool:
        """Verificar si estamos en producción"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Verificar si estamos en desarrollo"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def database_url_sync(self) -> str:
        """URL de base de datos para conexiones síncronas"""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    
    @property
    def database_url_async(self) -> str:
        """URL de base de datos para conexiones asíncronas"""
        # Para asyncpg, necesitamos limpiar parámetros SSL que no reconoce
        base_url = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        
        # Remover parámetros SSL problemáticos para asyncpg
        if "sslmode" in base_url:
            # Extraer solo la parte principal de la URL
            if "?" in base_url:
                base_url = base_url.split("?")[0]
        
        return base_url
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency injection para obtener configuración
    Útil para testing y override de configuración
    """
    return settings
