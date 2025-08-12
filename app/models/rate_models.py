"""
Modelos para cotizaciones y precios
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base


class RateHistory(Base):
    """
    Histórico de cotizaciones
    """
    __tablename__ = "rate_history"
    
    id = Column(Integer, primary_key=True, index=True)
    exchange_code = Column(String(15), ForeignKey("exchanges.code"), nullable=False, index=True)
    currency_pair = Column(String(20), ForeignKey("currency_pairs.symbol"), nullable=False, index=True)
    
    # Precios
    buy_price = Column(Float, nullable=True)
    sell_price = Column(Float, nullable=True)
    avg_price = Column(Float, nullable=True)
    
    # Volumen y estadísticas
    volume = Column(Float, nullable=True)
    volume_24h = Column(Float, nullable=True)
    
    # Metadatos
    source = Column(String(50), nullable=False)  # 'bcv', 'binance_p2p', etc.
    api_method = Column(String(50), nullable=True)  # 'web_scraping', 'official_api'
    trade_type = Column(String(20), nullable=True)  # 'buy_usdt', 'sell_usdt'
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relaciones
    exchange = relationship("Exchange", back_populates="rates")
    currency_pair_rel = relationship("CurrencyPair", back_populates="rates")
    
    # Índices para consultas rápidas
    __table_args__ = (
        Index('idx_rate_history_exchange_pair_time', 'exchange_code', 'currency_pair', 'timestamp'),
        Index('idx_rate_history_source_time', 'source', 'timestamp'),
    )


class CurrentRate(Base):
    """
    Cotizaciones actuales (vista materializada o tabla)
    """
    __tablename__ = "current_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    exchange_code = Column(String(15), ForeignKey("exchanges.code"), nullable=False, index=True)
    currency_pair = Column(String(20), ForeignKey("currency_pairs.symbol"), nullable=False, index=True)
    
    # Precios actuales
    buy_price = Column(Float, nullable=True)
    sell_price = Column(Float, nullable=True)
    avg_price = Column(Float, nullable=True)
    
    # Estadísticas
    volume_24h = Column(Float, nullable=True)
    variation_24h = Column(Float, nullable=True)
    
    # Metadatos
    source = Column(String(50), nullable=False)
    market_status = Column(String(20), default="active")  # 'active', 'inactive', 'error'
    
    # Timestamps
    last_update = Column(DateTime(timezone=True), default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relaciones
    exchange = relationship("Exchange", back_populates="current_rates")
    currency_pair_rel = relationship("CurrencyPair", back_populates="current_rates")
    
    # Índices
    __table_args__ = (
        Index('idx_current_rates_exchange_pair', 'exchange_code', 'currency_pair', unique=True),
        Index('idx_current_rates_last_update', 'last_update'),
    )
