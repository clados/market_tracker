import { Market, PriceHistory } from '../types/market';
import { Sparkline } from './Sparkline';
import { TrendingUp, TrendingDown, BarChart3, ExternalLink } from 'lucide-react';
import { useState, useEffect } from 'react';
import { backendApi } from '../services/backendApi';

interface MarketCardProps {
  market: Market;
  onSelect: (market: Market) => void;
}

export const MarketCard: React.FC<MarketCardProps> = ({ market, onSelect }) => {
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>(market.priceHistory);
  const [calculatedPriceChange, setCalculatedPriceChange] = useState(0);

  // Load fresh history data and calculate price change
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await backendApi.getMarketHistory(market.ticker);
        setPriceHistory(history);
        
        // Calculate price change using 30-day window (same as MarketDetail)
        if (history.length > 0) {
          const currentPrice = market.currentProbability;
          const now = new Date();
          const windowStart = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000); // 30 days ago
          
          // Filter history to the last 30 days
          const windowHistory = history.filter(point => 
            point.timestamp >= windowStart
          );
          
          if (windowHistory.length > 0) {
            const prices = windowHistory.map(point => point.price);
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            
            // Calculate absolute change from current price to the most extreme point
            const changeFromMin = Math.abs(currentPrice - minPrice);
            const changeFromMax = Math.abs(currentPrice - maxPrice);
            
            // Use the larger change (more dramatic)
            const absoluteChange = Math.max(changeFromMin, changeFromMax);
            
            // Calculate percentage change relative to current price
            const percentageChange = currentPrice > 0 ? (absoluteChange / currentPrice) : 0;
            setCalculatedPriceChange(percentageChange);
          }
        }
      } catch (error) {
        console.error(`MarketCard: Failed to load history for ${market.ticker}:`, error);
      }
    };

    loadHistory();
  }, [market.ticker, market.currentProbability]);

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) return `$${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `$${(volume / 1000).toFixed(0)}K`;
    return `$${volume}`;
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  // Function to construct Kalshi URL using actual data
  const getKalshiUrl = () => {
    if (market.seriesTicker) {
      // Extract base series name from series_ticker (remove date and market suffix)
      // Example: "KXATPMATCH-25JUL26DAVSHE" -> "kxatpmatch"
      const baseSeriesName = market.seriesTicker
        .split('-')[0]  // Take the part before the first dash
        .toLowerCase();  // Convert to lowercase
      
      // Create a slug from the title
      const marketSlug = market.title.toLowerCase()
        .replace(/[^a-z0-9]/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
      
      return `https://kalshi.com/markets/${baseSeriesName}/${marketSlug}`;
    }
    // Fallback to simple ticker-based URL if no series_ticker
    return `https://kalshi.com/markets/${market.ticker}`;
  };

  const isPositiveChange = calculatedPriceChange > 0;
  const sparklineColor = isPositiveChange ? '#10b981' : '#ef4444';

  return (
    <div 
      className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-colors cursor-pointer border border-gray-700 hover:border-gray-600"
      onClick={() => onSelect(market)}
    >
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="text-white font-semibold text-sm mb-1 line-clamp-2 flex items-center">
            {market.title}
            <a
              href={getKalshiUrl()}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 text-blue-400 hover:text-blue-300 flex items-center"
              title="View on Kalshi"
              onClick={e => e.stopPropagation()}
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          </h3>
          <p className="text-gray-400 text-xs font-mono">
            {market.ticker}
          </p>
        </div>
        <div className="flex items-center space-x-1 ml-2">
          {isPositiveChange ? (
            <TrendingUp className="w-4 h-4 text-green-400" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-400" />
          )}
          <span className={`text-sm font-semibold ${
            isPositiveChange ? 'text-green-400' : 'text-red-400'
          }`}>
            {isPositiveChange ? '+' : ''}{formatPercentage(calculatedPriceChange)}
          </span>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-gray-400 text-xs">Current Probability</span>
          <span className="text-white text-lg font-bold">
            {formatPercentage(market.currentProbability)}
          </span>
        </div>
        <div className="h-10 mb-2">
          <Sparkline 
            data={priceHistory.map(point => ({
              timestamp: point.timestamp.toISOString(),
              price: point.price,
              volume: point.volume
            }))} 
            color={sparklineColor}
            height={40}
          />
        </div>
      </div>

      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-1">
          <BarChart3 className="w-3 h-3 text-gray-400" />
          <span className="text-gray-400 text-xs">
            Volume last 24h: {formatVolume(market.volume24h)}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="bg-gray-700 text-gray-300 px-2 py-1 rounded text-xs">
            {market.category}
          </span>
          <span className="text-gray-400 text-xs">
            {market.status}
          </span>
        </div>
      </div>
    </div>
  );
};