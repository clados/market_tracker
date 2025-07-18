import { Market, PriceHistory } from '../types/market';
import { API_CONFIG } from '../config/api';

// Helper function to get backend URL
const getBackendUrl = (endpoint: string): string => {
  return `${API_CONFIG.BACKEND_URL}${endpoint}`;
};

// Backend API response types
interface BackendMarketsResponse {
  markets: any[];
  total: number;
  limit: number;
  offset: number;
}

interface BackendMarketStatsResponse {
  total_active: number;
  high_volume: number;
  volatile: number;
  filtered_total: number;
}

interface BackendPriceHistoryResponse {
  timestamp: string;
  price: number;
  volume: number;
}

class BackendApiService {
  constructor() {
    console.log('BackendApiService: Initialized with backend URL:', API_CONFIG.BACKEND_URL);
  }

  private async fetchWithRetry(url: string, options: RequestInit = {}, retries = 3): Promise<Response> {
    const maxRetries = API_CONFIG.RETRY_ATTEMPTS || retries;
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await fetch(url, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
        });
        
        if (response.ok) {
          return response;
        }
        
        if (response.status === 429 && i < retries - 1) {
          // Rate limited, wait and retry
          await new Promise(resolve => setTimeout(resolve, API_CONFIG.RETRY_DELAY * (i + 1)));
          continue;
        }
        
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      } catch (error) {
        // If it's an abort error, don't retry
        if (error instanceof Error && error.name === 'AbortError') {
          throw error;
        }
        
        if (i === maxRetries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, API_CONFIG.RETRY_DELAY * (i + 1)));
      }
    }
    
    throw new Error('Max retries exceeded');
  }

  private transformBackendMarket(backendMarket: any, priceHistory: PriceHistory[] = []): Market {
    return {
      id: backendMarket.id,
      ticker: backendMarket.ticker,
      title: backendMarket.title,
      subtitle: backendMarket.subtitle || '',
      category: backendMarket.category,
      status: backendMarket.status,
      currentProbability: backendMarket.current_price,
      volume24h: backendMarket.volume_24h,
      liquidity: backendMarket.liquidity,
      openTime: backendMarket.open_time,
      closeTime: backendMarket.close_time,
      expirationTime: backendMarket.expiration_time,
      resolutionRules: backendMarket.resolution_rules || '',
      tags: backendMarket.tags || '',
      createdAt: backendMarket.created_at,
      updatedAt: backendMarket.updated_at,
      priceHistory: priceHistory,
      related: [] // Will be populated separately if needed
    };
  }

  async checkBackendHealth(): Promise<{ success: boolean; message: string }> {
    try {
      const response = await this.fetchWithRetry(getBackendUrl('/health'));
      const data = await response.json();
      return { success: true, message: `Backend healthy: ${data.status}` };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return { success: false, message: `Backend connection failed: ${errorMessage}` };
    }
  }

  async getMarkets(
    limit = 100, 
    offset = '0', 
    status = 'active', 
    minLiquidity?: number, 
    pages?: number, 
    changeWindow: number = 30, 
    minChange?: number, 
    signal?: AbortSignal
  ): Promise<{ markets: Market[]; total: number; cursor?: string }> {
    console.log('BackendApiService: getMarkets called with:', { limit, status, minLiquidity, minChange, signal: !!signal });

    try {
      const url = new URL(getBackendUrl('/api/markets'));
      url.searchParams.set('limit', limit.toString());
      url.searchParams.set('status', status);
      if (minLiquidity) url.searchParams.set('min_liquidity', minLiquidity.toString());
      if (minChange) url.searchParams.set('min_change', minChange.toString());
      if (offset) url.searchParams.set('offset', offset);

      console.log('BackendApiService: Fetching from URL:', url.toString());

      const response = await this.fetchWithRetry(url.toString(), { signal });
      console.log('BackendApiService: Response received:', response.status, response.statusText);
      
      const data: BackendMarketsResponse = await response.json();

      console.log('BackendApiService: Received', data.markets.length, 'markets from backend');

      // Transform backend markets to frontend format
      const markets = data.markets.map(backendMarket => 
        this.transformBackendMarket(backendMarket, [])
      );

      return { 
        markets, 
        total: data.total,
        cursor: data.offset + data.limit < data.total ? (data.offset + data.limit).toString() : undefined 
      };
    } catch (error) {
      console.error('BackendApiService: Failed to fetch markets:', error);
      throw error;
    }
  }

  async getMarketStats(
    filters?: { 
      status?: string; 
      min_liquidity?: number; 
      category?: string; 
      search?: string; 
      min_change?: number 
    }, 
    signal?: AbortSignal
  ): Promise<{ total_active: number; high_volume: number; volatile: number; filtered_total: number }> {
    let url = getBackendUrl('/api/markets/stats');
    if (filters) {
      const params = new URLSearchParams();
      if (filters.status) params.set('status', filters.status);
      if (filters.min_liquidity !== undefined) params.set('min_liquidity', String(filters.min_liquidity));
      if (filters.category) params.set('category', filters.category);
      if (filters.search) params.set('search', filters.search);
      if (filters.min_change !== undefined) params.set('min_change', String(filters.min_change));
      url += `?${params.toString()}`;
    }
    const response = await this.fetchWithRetry(url, { signal });
    const data: BackendMarketStatsResponse = await response.json();
    return data;
  }

  async getMarketHistory(ticker: string, days: number = 30, signal?: AbortSignal): Promise<PriceHistory[]> {
    try {
      const url = getBackendUrl(`/api/markets/${ticker}/history?days=${days}`);
      const response = await this.fetchWithRetry(url, { signal });
      const data: BackendPriceHistoryResponse[] = await response.json();
      
      return data.map(item => ({
        timestamp: new Date(item.timestamp),
        price: item.price,
        volume: item.volume
      }));
    } catch (error) {
      console.error('BackendApiService: Failed to fetch market history:', error);
      throw error;
    }
  }

  async getMarketDetail(ticker: string, signal?: AbortSignal): Promise<Market | null> {
    try {
      const url = getBackendUrl(`/api/markets/${ticker}`);
      const response = await this.fetchWithRetry(url, { signal });
      const data = await response.json();
      
      return this.transformBackendMarket(data, []);
    } catch (error) {
      console.error('BackendApiService: Failed to fetch market detail:', error);
      return null;
    }
  }
}

export const backendApi = new BackendApiService();