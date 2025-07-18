import { Market } from '../types/market';
import { Sparkline } from './Sparkline';
import { TrendingUp, TrendingDown, Volume2 } from 'lucide-react';

interface MarketCardProps {
  market: Market;
  onSelect: (market: Market) => void;
}

export const MarketCard: React.FC<MarketCardProps> = ({ market, onSelect }) => {
  const formatVolume = (volume: number) => {
    if (volume >= 1000000) return `$${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `$${(volume / 1000).toFixed(0)}K`;
    return `$${volume}`;
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  // Calculate price change from price history if available
  const calculatePriceChange = () => {
    if (market.priceHistory.length === 0) return 0;
    
    const prices = market.priceHistory.map(point => point.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const currentPrice = market.currentProbability;
    
    // Calculate absolute change from current price to the most extreme point
    const changeFromMin = Math.abs(currentPrice - minPrice);
    const changeFromMax = Math.abs(currentPrice - maxPrice);
    
    return Math.max(changeFromMin, changeFromMax);
  };

  const priceChange = calculatePriceChange();
  const isPositiveChange = priceChange > 0;
  const sparklineColor = isPositiveChange ? '#10b981' : '#ef4444';

  return (
    <div 
      className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-colors cursor-pointer border border-gray-700 hover:border-gray-600"
      onClick={() => onSelect(market)}
    >
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="text-white font-semibold text-sm mb-1 line-clamp-2">
            {market.title}
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
            {isPositiveChange ? '+' : ''}{formatPercentage(priceChange)}
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
            data={market.priceHistory.map(point => ({
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
          <Volume2 className="w-3 h-3 text-gray-400" />
          <span className="text-gray-400 text-xs">
            {formatVolume(market.volume24h)}
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