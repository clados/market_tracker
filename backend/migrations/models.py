from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import datetime

class Market(Base):
    __tablename__ = "markets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    subtitle = Column(Text)
    category = Column(String(100), index=True)
    status = Column(String(50), default="open")
    current_price = Column(Float, nullable=False)
    volume_24h = Column(Integer, default=0)
    liquidity = Column(Integer, default=0)
    open_time = Column(DateTime)
    close_time = Column(DateTime)
    expiration_time = Column(DateTime)
    resolution_rules = Column(Text)
    tags = Column(Text)  # JSON string
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    price_history = relationship("PriceHistory", back_populates="market", cascade="all, delete-orphan")
    market_changes = relationship("MarketChange", back_populates="market", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_markets_status_category', 'status', 'category'),
        Index('idx_markets_liquidity', 'liquidity'),
        Index('idx_markets_open_time', 'open_time'),
    )

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    market = relationship("Market", back_populates="price_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_price_history_market_timestamp', 'market_id', 'timestamp'),
    )

class MarketChange(Base):
    __tablename__ = "market_changes"
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    change_window_days = Column(Integer, nullable=False)  # 1, 7, 30, 90 days
    price_change = Column(Float, nullable=False)
    min_price = Column(Float)
    max_price = Column(Float)
    change_percentage = Column(Float)
    calculated_at = Column(DateTime, default=func.now())
    
    # Relationships
    market = relationship("Market", back_populates="market_changes")
    
    # Indexes
    __table_args__ = (
        Index('idx_market_changes_market_window', 'market_id', 'change_window_days'),
        Index('idx_market_changes_price_change', 'price_change'),
        Index('idx_market_changes_calculated_at', 'calculated_at'),
    ) 