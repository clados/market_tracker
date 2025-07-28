export interface Market {
  id: number;
  ticker: string;
  seriesTicker?: string;
  title: string;
  subtitle?: string;
  category: string;
  status: string;
  currentProbability: number; // Display name is probability, but backend field is current_price
  volume24h: number;
  liquidity: number;
  openTime?: Date;
  closeTime?: Date;
  expirationTime?: Date;
  resolutionRules?: string;
  tags?: string;
  createdAt: Date;
  updatedAt: Date;
  priceHistory: PriceHistory[]; // Keep backend field name
  marketChanges: MarketChange[];
}

export interface PriceHistory {
  timestamp: Date;
  price: number; // Backend field name, but frontend displays as probability
  volume: number;
}

export interface MarketChange {
  changeWindowDays: number;
  priceChange: number; // Backend field name, but frontend displays as probability change
  minPrice?: number; // Backend field name
  maxPrice?: number; // Backend field name
  changePercentage?: number;
  calculatedAt: Date;
}

export interface PricePoint {
  timestamp: string;
  price: number;
  volume: number;
}

export interface FilterState {
  minVolume: number;
  minPriceChange: number;
  changeWindow: number;
  search: string;
}

export interface PaginationState {
  currentPage: number;
  pageSize: number;
  totalPages: number;
  totalItems: number;
}