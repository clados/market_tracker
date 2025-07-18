import { useState, useEffect, useRef } from 'react';
import { Market, FilterState, PaginationState } from '../types/market';
import { backendApi } from '../services/backendApi';

export const useMarkets = () => {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [totalActiveMarkets, setTotalActiveMarkets] = useState<number>(0);
  const [highVolumeMarkets, setHighVolumeMarkets] = useState<number>(0);
  const [volatileMarkets, setVolatileMarkets] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [filters, setFilters] = useState<FilterState>({
    minVolume: 0,
    minPriceChange: 0,
    changeWindow: 30,
    search: ''
  });

  const [pagination, setPagination] = useState<PaginationState>({
    currentPage: 1,
    pageSize: 6,
    totalPages: 0,
    totalItems: 0
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  // Simple load function
  const loadMarkets = async () => {
    try {
      setLoading(true);
      setError(null);

      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;

      console.log('Loading markets...');
      
      const offset = (pagination.currentPage - 1) * pagination.pageSize;
      
      const { markets: fetchedMarkets, total } = await backendApi.getMarkets(
        pagination.pageSize,
        offset.toString(),
        'active',
        filters.minVolume > 0 ? filters.minVolume : undefined,
        1,
        filters.changeWindow,
        filters.minPriceChange > 0 ? filters.minPriceChange : undefined,
        controller.signal
      );

      if (controller.signal.aborted) return;

      console.log('Markets loaded:', fetchedMarkets.length);
      setMarkets(fetchedMarkets);
      
      const totalPages = Math.ceil(total / pagination.pageSize);
      setPagination(prev => ({
        ...prev,
        totalItems: total,
        totalPages: totalPages
      }));

      // Load stats
      const stats = await backendApi.getMarketStats({
        status: 'active',
        min_change: filters.minPriceChange > 0 ? filters.minPriceChange : undefined
      }, controller.signal);

      if (controller.signal.aborted) return;

      setTotalActiveMarkets(stats.total_active);
      setHighVolumeMarkets(stats.high_volume);
      setVolatileMarkets(stats.volatile);

    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.error('Error loading markets:', err);
        setError('Failed to load markets');
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  // Load on mount
  useEffect(() => {
    loadMarkets();
  }, []);

  // Load when pagination changes
  useEffect(() => {
    loadMarkets();
  }, [pagination.currentPage, pagination.pageSize]);

  // Load when filters change (with debounce for sliders)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setPagination(prev => ({ ...prev, currentPage: 1 }));
      loadMarkets();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [filters.minVolume, filters.minPriceChange, filters.changeWindow, filters.search]);

  // Filter markets client-side for search
  const filteredMarkets = markets.filter(market => 
    !filters.search || market.title.toLowerCase().includes(filters.search.toLowerCase())
  );

  const getRelatedMarkets = (marketId: string): Market[] => {
    const market = markets.find(m => m.ticker === marketId);
    if (!market) return [];
    return markets.filter(m => market.related.includes(m.ticker));
  };

  const refreshMarkets = () => {
    loadMarkets();
  };

  return {
    markets: filteredMarkets,
    filters,
    setFilters,
    pagination,
    setPagination,
    getRelatedMarkets,
    totalMarkets: pagination.totalItems,
    highVolumeMarkets,
    volatileMarkets,
    loading,
    error,
    refreshMarkets
  };
};