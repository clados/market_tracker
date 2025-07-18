import { Market, PriceHistory } from '../types/market';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { X, TrendingUp, TrendingDown, Volume2, Calendar, Tag, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { useState, useEffect } from 'react';
import { backendApi } from '../services/backendApi';

interface MarketDetailProps {
  market: Market;
  relatedMarkets: Market[];
  onClose: () => void;
  onSelectMarket: (market: Market) => void;
}

export const MarketDetail: React.FC<MarketDetailProps> = ({ 
  market, 
  relatedMarkets, 
  onClose,
  onSelectMarket 
}) => {
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>(market.priceHistory);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [calculatedPriceChange, setCalculatedPriceChange] = useState(0);

  // Load history when modal opens if not already loaded
  useEffect(() => {
    const loadHistory = async () => {
      if (priceHistory.length === 0) {
        setLoadingHistory(true);
        try {
          console.log(`MarketDetail: Loading history for ${market.ticker}`);
          const history = await backendApi.getMarketHistory(market.ticker);
          setPriceHistory(history);
          console.log(`MarketDetail: Loaded ${history.length} history points for ${market.ticker}`);
          
          // Recalculate price change based on loaded history
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
              const newPriceChange = Math.max(changeFromMin, changeFromMax);
              setCalculatedPriceChange(newPriceChange);
              
              console.log(`MarketDetail: Recalculated price change for ${market.ticker}: current=${currentPrice}, min=${minPrice}, max=${maxPrice}, change=${newPriceChange}`);
            }
          }
        } catch (error) {
          console.error(`MarketDetail: Failed to load history for ${market.ticker}:`, error);
        } finally {
          setLoadingHistory(false);
        }
      }
    };

    loadHistory();
  }, [market.ticker, priceHistory.length, market.currentProbability]);

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) return `$${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `$${(volume / 1000).toFixed(0)}K`;
    return `$${volume}`;
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const chartData = priceHistory.map(point => ({
    timestamp: point.timestamp.getTime(),
    price: point.price * 100,
    volume: point.volume,
    date: format(point.timestamp, 'MMM dd')
  }));

  const isPositiveChange = calculatedPriceChange > 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-6 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white mb-2">{market.title}</h2>
            <p className="text-gray-400 font-mono text-sm">{market.ticker}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">Current Probability</div>
              <div className="text-white text-2xl font-bold">
                {formatPercentage(market.currentProbability)}
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">Price Change</div>
              <div className={`text-2xl font-bold flex items-center ${
                isPositiveChange ? 'text-green-400' : 'text-red-400'
              }`}>
                {isPositiveChange ? (
                  <TrendingUp className="w-5 h-5 mr-1" />
                ) : (
                  <TrendingDown className="w-5 h-5 mr-1" />
                )}
                {isPositiveChange ? '+' : ''}{formatPercentage(calculatedPriceChange)}
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">Volume</div>
              <div className="text-white text-2xl font-bold flex items-center">
                <Volume2 className="w-5 h-5 mr-1" />
                {formatVolume(market.volume24h)}
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">Status</div>
              <div className="text-white text-lg font-bold flex items-center">
                <Calendar className="w-4 h-4 mr-1" />
                {market.status}
              </div>
            </div>
          </div>

          {/* Price Chart */}
          <div className="bg-gray-700 rounded-lg p-4 mb-6">
            <h3 className="text-white font-semibold mb-4">Price History</h3>
            <div className="h-64">
              {loadingHistory ? (
                <div className="flex items-center justify-center h-full">
                  <div className="flex items-center space-x-2 text-gray-400">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Loading price history...</span>
                  </div>
                </div>
              ) : chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#9CA3AF"
                      fontSize={12}
                    />
                    <YAxis 
                      stroke="#9CA3AF"
                      fontSize={12}
                      domain={[0, 100]}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F9FAFB'
                      }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'Price']}
                    />
                    <Line
                      type="monotone"
                      dataKey="price"
                      stroke={isPositiveChange ? '#10b981' : '#ef4444'}
                      strokeWidth={2}
                      dot={{ fill: isPositiveChange ? '#10b981' : '#ef4444', strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <span>No price history available</span>
                </div>
              )}
            </div>
          </div>

          {/* Description and Resolution Criteria */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-3 flex items-center">
                <Tag className="w-4 h-4 mr-2" />
                Market Details
              </h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-400">Category:</span>
                  <span className="text-white ml-2">{market.category}</span>
                </div>
                <div>
                  <span className="text-gray-400">Subtitle:</span>
                  <span className="text-white ml-2">{market.subtitle}</span>
                </div>
                <div>
                  <span className="text-gray-400">Liquidity:</span>
                  <span className="text-white ml-2">{formatVolume(market.liquidity)}</span>
                </div>
                <div>
                  <span className="text-gray-400">Tags:</span>
                  <span className="text-white ml-2">{market.tags}</span>
                </div>
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-3">Resolution Rules</h3>
              <p className="text-gray-300 text-sm leading-relaxed">
                {market.resolutionRules || 'Resolution rules not available'}
              </p>
            </div>
          </div>

          {/* Related Markets */}
          {relatedMarkets.length > 0 && (
            <div className="bg-gray-700 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-4">Related Markets</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {relatedMarkets.map((relatedMarket) => (
                  <div
                    key={relatedMarket.ticker}
                    className="bg-gray-600 rounded-lg p-3 cursor-pointer hover:bg-gray-500 transition-colors"
                    onClick={() => onSelectMarket(relatedMarket)}
                  >
                    <h4 className="text-white font-medium text-sm mb-1">
                      {relatedMarket.title}
                    </h4>
                    <p className="text-gray-400 text-xs font-mono mb-2">
                      {relatedMarket.ticker}
                    </p>
                    <div className="flex justify-between items-center">
                      <span className="text-white text-sm font-bold">
                        {formatPercentage(relatedMarket.currentProbability)}
                      </span>
                      <span className="text-gray-400 text-xs">
                        {formatVolume(relatedMarket.volume24h)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};