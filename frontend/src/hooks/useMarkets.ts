import { useState, useEffect, useRef, useCallback } from 'react';
import { Market, FilterState } from '../types/market';
import { backendApi } from '../services/backendApi';

export const useMarkets = () => {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [totalActiveMarkets, setTotalActiveMarkets] = useState<number>(0);
  const [highVolumeMarkets, setHighVolumeMarkets] = useState<number>(0);
  const [bigMovers, setBigMovers] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  
  const [filters, setFilters] = useState<FilterState>({
    minVolume: 0,
    minPriceChange: 0,
    changeWindow: 30,
    search: ''
  });

  const [pageSize] = useState(12); // Fixed page size for infinite scrolling
  const [currentOffset, setCurrentOffset] = useState(0);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Load initial markets
  const loadMarkets = async (reset: boolean = false) => {
    try {
      if (reset) {
        setLoading(true);
        setCurrentOffset(0);
        setMarkets([]);
        setHasMore(true);
      } else {
        setLoadingMore(true);
      }
      
      setError(null);

      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;

      console.log('Loading markets...');
      console.log('Filter values:', { minVolume: filters.minVolume, minPriceChange: filters.minPriceChange });
      
      const offset = reset ? 0 : currentOffset;
      
      const { markets: fetchedMarkets, total } = await backendApi.getMarkets(
        pageSize,
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
      console.log('Total markets from API:', total);
      
      if (reset) {
        setMarkets(fetchedMarkets);
      } else {
        setMarkets(prev => [...prev, ...fetchedMarkets]);
      }
      
      // Check if there are more markets to load
      const newOffset = offset + fetchedMarkets.length;
      setHasMore(newOffset < total);
      setCurrentOffset(newOffset);

      // Load stats only on initial load or filter change
      if (reset) {
        const stats = await backendApi.getMarketStats({
          status: 'active',
          min_liquidity: filters.minVolume > 0 ? filters.minVolume : undefined,
          min_change: filters.minPriceChange > 0 ? filters.minPriceChange : undefined
        }, controller.signal);

        if (controller.signal.aborted) return;

        setTotalActiveMarkets(stats.total_active);
        setHighVolumeMarkets(stats.high_volume);
        setBigMovers(stats.big_movers);
      }

    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.error('Error loading markets:', err);
        setError('Failed to load markets');
      }
    } finally {
      setLoading(false);
      setLoadingMore(false);
      abortControllerRef.current = null;
    }
  };

  // Load more markets for infinite scrolling
  const loadMore = useCallback(async () => {
    if (!loadingMore && hasMore && !loading) {
      await loadMarkets(false);
    }
  }, [loadingMore, hasMore, loading, currentOffset, filters, pageSize]);

  // Load on mount
  useEffect(() => {
    loadMarkets(true);
  }, []);

  // Load when filters change (reset and reload)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadMarkets(true);
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
    
    // For now, return markets in the same category as a simple related markets implementation
    // This can be enhanced later with more sophisticated related market logic
    return markets.filter(m => 
      m.ticker !== marketId && 
      m.category === market.category
    ).slice(0, 3); // Limit to 3 related markets
  };

  const refreshMarkets = () => {
    loadMarkets(true);
  };

  return {
    markets: filteredMarkets,
    filters,
    setFilters,
    getRelatedMarkets,
    totalMarkets: markets.length,
    totalActiveMarkets,
    highVolumeMarkets,
    bigMovers,
    loading,
    loadingMore,
    hasMore,
    error,
    refreshMarkets,
    loadMore
  };
};