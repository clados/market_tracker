import { Market, PriceHistory, FilterState } from '../types/market';
import { TrendingUp, TrendingDown, Star, ExternalLink } from 'lucide-react';
import { useState, useEffect } from 'react';
import { backendApi } from '../services/backendApi';

interface MarketCardProps {
  market: Market;
  filters: FilterState;
  onSelect: (market: Market) => void;
}

export const MarketCard: React.FC<MarketCardProps> = ({ market, filters, onSelect }) => {
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>(market.priceHistory);
  const [calculatedPriceChange, setCalculatedPriceChange] = useState(0);

  // Load fresh history data and calculate price change
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await backendApi.getMarketHistory(market.ticker);
        setPriceHistory(history);
        
        // Calculate price change using the filter's change window
        if (history.length >= 2) {
          const currentPrice = market.currentProbability;
          const now = new Date();
          const windowStart = new Date(now.getTime() - filters.changeWindow * 24 * 60 * 60 * 1000);
          
          // Filter history to the change window period
          const windowHistory = history.filter(point => 
            point.timestamp >= windowStart
          );
          
          if (windowHistory.length >= 2) {
            // Calculate change from the start of the window to current price
            // Sort by timestamp to ensure we get the actual start price
            const sortedHistory = windowHistory.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
            const startPrice = sortedHistory[0].price;
            const priceChange = currentPrice - startPrice;
            setCalculatedPriceChange(priceChange);
          } else {
            // Not enough data points in the window
            setCalculatedPriceChange(0);
          }
        } else {
          // Not enough history data at all
          setCalculatedPriceChange(0);
        }
      } catch (error) {
        console.error(`MarketCard: Failed to load history for ${market.ticker}:`, error);
      }
    };

    loadHistory();
  }, [market.ticker, market.currentProbability, filters.changeWindow]);

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(0)}%`;
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
  const hasPriceChange = calculatedPriceChange !== 0;
  const changePercentage = Math.abs(calculatedPriceChange * 100);
  
  // Determine card color based on category or other criteria
  const getCardColor = () => {
    if (market.category.toLowerCase().includes('politics') || market.category.toLowerCase().includes('election')) {
      return 'bg-purple-800 border-purple-700 hover:bg-purple-750';
    }
    return 'bg-gray-800 border-gray-700 hover:bg-gray-750';
  };



  return (
    <div 
      className={`${getCardColor()} rounded-lg p-4 hover:border-gray-600 transition-colors cursor-pointer border`}
      onClick={() => onSelect(market)}
    >
      <div className="flex justify-between items-start">
        {/* Main Question */}
        <div className="flex-1 pr-4">
          <h3 className="text-white font-medium text-sm leading-relaxed">
            {market.title}
          </h3>
        </div>

        {/* Right Side Data */}
        <div className="flex items-center space-x-3">
          {/* Change Indicator */}
          {hasPriceChange ? (
            <div className={`flex items-center space-x-1 px-2 py-1 rounded text-xs font-medium ${
              isPositiveChange 
                ? 'bg-green-600 text-white' 
                : 'bg-red-600 text-white'
            }`}>
              <span>{changePercentage.toFixed(0)}</span>
              {isPositiveChange ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
            </div>
          ) : (
            <div className="px-2 py-1 rounded text-xs font-medium bg-gray-600 text-gray-300">
              No data
            </div>
          )}

          {/* Current Probability */}
          <div className="text-white font-semibold text-sm">
            {formatPercentage(market.currentProbability)}
          </div>

          {/* External Link */}
          <a
            href={getKalshiUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300"
            title="View on Kalshi"
            onClick={e => e.stopPropagation()}
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
};