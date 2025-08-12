"""
Modelos para exchanges y pares de divisas
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Exchange(Base):
    """
    Exchanges disponibles
    """
    __tablename__ = "exchanges"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(15), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # 'centralized', 'p2p', 'dex'
    description = Column(Text, nullable=True)
    
    # Configuración
    is_active = Column(Boolean, default=True)
    operating_hours = Column(String(100), nullable=True)  # '24/7', '9-17', etc.
    update_frequency = Column(String(50), nullable=True)  # '1h', '5min', 'realtime'
    
    # Metadatos
    website = Column(String(200), nullable=True)
    api_documentation = Column(String(200), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    rates = relationship("RateHistory", back_populates="exchange")
    current_rates = relationship("CurrentRate", back_populates="exchange")
    
    # Índices
    __table_args__ = (
        Index('idx_exchanges_active_type', 'is_active', 'type'),
    )


class CurrencyPair(Base):
    """
    Pares de divisas soportados
    """
    __tablename__ = "currency_pairs"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    base_currency = Column(String(10), nullable=False)  # 'USD', 'USDT', 'EUR'
    quote_currency = Column(String(10), nullable=False)  # 'VES', 'BTC', 'ETH'
    
    # Configuración
    is_active = Column(Boolean, default=True)
    min_amount = Column(Float, nullable=True)
    max_amount = Column(Float, nullable=True)
    
    # Metadatos
    description = Column(Text, nullable=True)
    precision = Column(Integer, default=4)  # Decimales para precios
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relaciones
    current_rates = relationship("CurrentRate", back_populates="currency_pair_rel")
    rates = relationship("RateHistory", back_populates="currency_pair_rel")
    
    # Índices
    __table_args__ = (
        Index('idx_currency_pairs_base_quote', 'base_currency', 'quote_currency'),
        Index('idx_currency_pairs_active', 'is_active'),
    )
