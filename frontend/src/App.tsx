import React, { useState } from 'react';
import { useMarkets } from './hooks/useMarkets';
import { MarketCard } from './components/MarketCard';
import { FilterBar } from './components/FilterBar';
import { Pagination } from './components/Pagination';
import { MarketDetail } from './components/MarketDetail';

import { Market } from './types/market';
import { BarChart3, TrendingUp, Eye, AlertCircle } from 'lucide-react';

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
    pagination, 
    setPagination, 
    getRelatedMarkets, 
    totalMarkets,
    totalActiveMarkets,
    highVolumeMarkets,
    bigMovers,
    loading,
    error,
    refreshMarkets
  } = useMarkets();
  

  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null);

  const handlePageChange = (page: number) => {
    setPagination(prev => ({ ...prev, currentPage: page }));
  };

  const handlePageSizeChange = (size: number) => {
    setPagination(prev => ({ ...prev, pageSize: size, currentPage: 1 }));
  };

  const handleSelectMarket = (market: Market) => {
    setSelectedMarket(market);
  };

  const handleCloseDetail = () => {
    setSelectedMarket(null);
  };

  const relatedMarkets = selectedMarket ? getRelatedMarkets(selectedMarket.ticker) : [];

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
                <h1 className="text-2xl font-bold text-white">Kalshi Market Tracker</h1>
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

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-400 text-sm">Active Markets</div>
                <div className="text-white text-2xl font-bold">{totalActiveMarkets}</div>
              </div>
              <Eye className="w-8 h-8 text-blue-400" />
            </div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-400 text-sm">High Volume</div>
                <div className="text-white text-2xl font-bold">{highVolumeMarkets}</div>
              </div>
              <BarChart3 className="w-8 h-8 text-green-400" />
            </div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-gray-400 text-sm">Big Movers</div>
                <div className="text-white text-2xl font-bold">{bigMovers}</div>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-400" />
            </div>
          </div>
        </div>

        {/* Filters */}
        <FilterBar
          filters={filters}
          onFiltersChange={setFilters}
          totalMarkets={totalMarkets}
        />

        {/* Market Cards */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-gray-800 rounded-lg p-6 border border-gray-700 animate-pulse">
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
            {markets.map((market) => (
              <MarketCard
                key={market.id}
                market={market}
                onSelect={handleSelectMarket}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {!loading && (
          <Pagination
            pagination={pagination}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
          />
        )}

        {/* Market Detail Modal */}
        {selectedMarket && (
          <MarketDetail
            market={selectedMarket}
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