from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PriceHistoryResponse(BaseModel):
    timestamp: datetime
    price: float
    volume: int
    
    class Config:
        from_attributes = True

class MarketChangeResponse(BaseModel):
    change_window_days: int
    price_change: float
    min_price: Optional[float]
    max_price: Optional[float]
    change_percentage: Optional[float]
    calculated_at: datetime
    
    class Config:
        from_attributes = True

class MarketResponse(BaseModel):
    id: int
    ticker: str
    series_ticker: Optional[str]
    title: str
    subtitle: Optional[str]
    category: str
    status: str
    current_price: float
    volume_24h: int
    liquidity: int
    open_time: Optional[datetime]
    close_time: Optional[datetime]
    expiration_time: Optional[datetime]
    resolution_rules: Optional[str]
    tags: Optional[str]
    created_at: datetime
    updated_at: datetime
    price_history: List[PriceHistoryResponse] = []
    market_changes: List[MarketChangeResponse] = []
    
    class Config:
        from_attributes = True

class MarketListResponse(BaseModel):
    markets: List[MarketResponse]
    total: int
    limit: int
    offset: int 