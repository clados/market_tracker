export interface Market {
  id: number;
  ticker: string;
  seriesTicker: string | null;
  title: string;
  subtitle: string;
  category: string;
  status: string;
  currentProbability: number;
  volume24h: number;
  liquidity: number;
  openTime: string | null;
  closeTime: string | null;
  expirationTime: string | null;
  resolutionRules: string;
  tags: string;
  createdAt: string;
  updatedAt: string;
  priceHistory: PriceHistory[];
  related: string[];
}

export interface PriceHistory {
  timestamp: Date;
  price: number;
  volume: number;
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