"""
Modelos para logs de API y auditoría
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class ApiLog(Base):
    """
    Log de todas las operaciones de API
    """
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Información de la petición
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False, index=True)
    
    # Usuario y autenticación
    user_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # Datos de la petición
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    
    # Metadatos
    source = Column(String(50), nullable=True, index=True)  # 'bcv', 'binance_p2p'
    operation_type = Column(String(50), nullable=True)  # 'scraping', 'api_call', 'comparison'
    
    # Performance
    response_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True, index=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Índices para consultas rápidas
    __table_args__ = (
        Index('idx_api_logs_endpoint_time', 'endpoint', 'timestamp'),
        Index('idx_api_logs_source_time', 'source', 'timestamp'),
        Index('idx_api_logs_status_time', 'status_code', 'timestamp'),
        Index('idx_api_logs_success_time', 'success', 'timestamp'),
    )
