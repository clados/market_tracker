import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useMarkets } from './hooks/useMarkets';
import { MarketCard } from './components/MarketCard';
import { FilterBar } from './components/FilterBar';
import { MarketDetail } from './components/MarketDetail';

import { Market } from './types/market';
import { BarChart3, TrendingUp, Eye, AlertCircle, Loader2 } from 'lucide-react';

function formatVolume(volume: number) {
  if (volume >= 1000) {
    return `$${(volume / 1000).toFixed(1)}K`;
  }
  return `$${volume}`;
}

function App() {
  const { 
    markets, 
    filters, 
    setFilters, 
    getRelatedMarkets, 
    totalMarkets,
    totalActiveMarkets,
    highVolumeMarkets,
    bigMovers,
    loading,
    loadingMore,
    hasMore,
    error,
    refreshMarkets,
    loadMore
  } = useMarkets();
  

  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadingRef = useRef<HTMLDivElement>(null);

  const handleSelectMarket = (market: Market) => {
    setSelectedMarket(market);
  };

  const handleCloseDetail = () => {
    setSelectedMarket(null);
  };

  const relatedMarkets = selectedMarket ? getRelatedMarkets(selectedMarket.ticker) : [];

  // Intersection Observer for infinite scrolling
  const lastElementRef = useCallback((node: HTMLDivElement | null) => {
    if (loading) return;
    
    if (observerRef.current) {
      observerRef.current.disconnect();
    }
    
    observerRef.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore && !loadingMore) {
        loadMore();
      }
    });
    
    if (node) {
      observerRef.current.observe(node);
    }
  }, [loading, hasMore, loadingMore, loadMore]);

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Market Tracker</h1>
                <p className="text-gray-400 text-sm">Discover underreacting prediction markets</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-white font-semibold">Live Markets</div>
                <div className="text-blue-400 text-sm">Real-time analysis</div>
              </div>
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Error Banner */}
        {error && (
          <div className="bg-red-900 border border-red-700 rounded-lg p-4 mb-6 flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <div>
              <div className="text-red-200 font-medium">Error Loading Markets</div>
              <div className="text-red-300 text-sm">{error}</div>
            </div>
            <button
              onClick={refreshMarkets}
              className="ml-auto px-3 py-1 bg-red-800 hover:bg-red-700 text-red-200 rounded text-sm transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Filters */}
        <FilterBar
          filters={filters}
          onFiltersChange={setFilters}
          totalMarkets={totalMarkets}
        />

        {/* Market Cards */}
        {loading ? (
          <div className="grid grid-cols-1 gap-3 mb-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-gray-800 rounded-lg p-4 border border-gray-700 animate-pulse">
                <div className="h-4 bg-gray-700 rounded mb-3"></div>
                <div className="h-3 bg-gray-700 rounded mb-4 w-2/3"></div>
                <div className="h-10 bg-gray-700 rounded mb-4"></div>
                <div className="flex justify-between">
                  <div className="h-3 bg-gray-700 rounded w-1/4"></div>
                  <div className="h-3 bg-gray-700 rounded w-1/3"></div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 mb-6">
            {markets.map((market, index) => (
              <div key={market.id} ref={index === markets.length - 1 ? lastElementRef : null}>
                <MarketCard
                  market={market}
                  filters={filters}
                  onSelect={handleSelectMarket}
                />
              </div>
            ))}
            
            {/* Loading more indicator */}
            {loadingMore && (
              <div className="flex justify-center items-center py-6">
                <div className="flex items-center space-x-2 text-gray-400">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Loading more markets...</span>
                </div>
              </div>
            )}
            
            {/* End of results indicator */}
            {!hasMore && markets.length > 0 && (
              <div className="flex justify-center items-center py-6">
                <div className="text-gray-400 text-sm">
                  No more markets to load
                </div>
              </div>
            )}
          </div>
        )}

        {/* Market Detail Modal */}
        {selectedMarket && (
          <MarketDetail
            market={selectedMarket}
            filters={filters}
            relatedMarkets={relatedMarkets}
            onClose={handleCloseDetail}
            onSelectMarket={handleSelectMarket}
          />
        )}
      </div>
    </div>
  );
}

export default App;