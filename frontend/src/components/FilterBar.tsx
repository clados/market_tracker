import { FilterState } from '../types/market';
import { Search, Filter } from 'lucide-react';

interface FilterBarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  totalMarkets: number;
}

export const FilterBar: React.FC<FilterBarProps> = ({ 
  filters, 
  onFiltersChange, 
  totalMarkets 
}) => {
  return (
    <div className="bg-gray-800 rounded-lg p-4 mb-6 border border-gray-700">
      <div className="flex items-center space-x-2 mb-4">
        <Filter className="w-4 h-4 text-gray-400" />
        <h2 className="text-white font-semibold">Filters</h2>
        <span className="text-gray-400 text-sm">
          ({totalMarkets} markets)
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
        {/* Search */}
        <div className="relative">
          <label className="block text-gray-400 text-sm mb-1">Search</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search markets..."
              value={filters.search}
              onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent h-10"
            />
          </div>
        </div>

        {/* Change Window */}
        <div>
          <label className="block text-gray-400 text-sm mb-1">Change Window</label>
          <select
            value={filters.changeWindow}
            onChange={(e) => onFiltersChange({ ...filters, changeWindow: parseInt(e.target.value) })}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent h-10"
          >
            <option value={1}>1 Day</option>
            <option value={7}>7 Days</option>
            <option value={14}>14 Days</option>
            <option value={30}>30 Days</option>
          </select>
        </div>

        {/* Min Volume */}
        <div>
          <label className="block text-gray-400 text-sm mb-1">
            Min Volume: ${filters.minVolume.toLocaleString()}
          </label>
          <div className="h-10 flex items-center">
            <input
              type="range"
              min="0"
              max="100000"
              step="5000"
              value={filters.minVolume}
              onChange={(e) => onFiltersChange({ ...filters, minVolume: parseInt(e.target.value) })}
              className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
            />
          </div>
        </div>

        {/* Min Price Change */}
        <div>
          <label className="block text-gray-400 text-sm mb-1">
            Min Change: {(filters.minPriceChange * 100).toFixed(1)}%
          </label>
          <div className="h-10 flex items-center">
            <input
              type="range"
              min="0"
              max="1.0"
              step="0.01"
              value={filters.minPriceChange}
              onChange={(e) => onFiltersChange({ ...filters, minPriceChange: parseFloat(e.target.value) })}
              className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
            />
          </div>
        </div>
      </div>
    </div>
  );
};