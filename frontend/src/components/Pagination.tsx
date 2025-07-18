import { PaginationState } from '../types/market';
import { ChevronLeft, ChevronRight, SkipBack, SkipForward } from 'lucide-react';
import { useState } from 'react';

interface PaginationProps {
  pagination: PaginationState;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({ 
  pagination, 
  onPageChange, 
  onPageSizeChange 
}) => {
  const { currentPage, pageSize, totalPages, totalItems } = pagination;
  const [jumpToPage, setJumpToPage] = useState('');

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const handleJumpToPage = () => {
    const page = parseInt(jumpToPage);
    if (page >= 1 && page <= totalPages) {
      onPageChange(page);
      setJumpToPage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleJumpToPage();
    }
  };

  // Enhanced page numbers with better logic
  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 9;
    
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show first page, ellipsis, current page area, ellipsis, last page
      const start = Math.max(1, currentPage - 2);
      const end = Math.min(totalPages, currentPage + 2);
      
      // Always show first page
      pages.push(1);
      
      if (start > 2) {
        pages.push('...');
      }
      
      for (let i = start; i <= end; i++) {
        if (i > 1 && i < totalPages) {
          pages.push(i);
        }
      }
      
      if (end < totalPages - 1) {
        pages.push('...');
      }
      
      // Always show last page
      if (totalPages > 1) {
        pages.push(totalPages);
      }
    }
    
    return pages;
  };

  return (
    <div className="flex items-center justify-between bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <label className="text-gray-400 text-sm">Show:</label>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(parseInt(e.target.value))}
            className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={6}>6</option>
            <option value={12}>12</option>
            <option value={24}>24</option>
          </select>
        </div>
        
        <div className="text-gray-400 text-sm">
          Showing {startItem}-{endItem} of {totalItems} markets
        </div>

        <div className="text-gray-400 text-sm">
          Page {currentPage} of {totalPages}
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Jump to page input */}
        <div className="flex items-center space-x-2">
          <label className="text-gray-400 text-sm">Go to:</label>
          <input
            type="number"
            value={jumpToPage}
            onChange={(e) => setJumpToPage(e.target.value)}
            onKeyPress={handleKeyPress}
            min="1"
            max={totalPages}
            className="w-16 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Page"
          />
          <button
            onClick={handleJumpToPage}
            className="px-2 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 transition-colors text-sm"
          >
            Go
          </button>
        </div>

        {/* Navigation buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onPageChange(1)}
            disabled={currentPage === 1}
            className="flex items-center px-2 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="First page"
          >
            <SkipBack className="w-4 h-4" />
          </button>

          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="flex items-center space-x-1 px-3 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          <div className="flex space-x-1">
            {getPageNumbers().map((page, index) => (
              <button
                key={index}
                onClick={() => typeof page === 'number' ? onPageChange(page) : null}
                disabled={typeof page !== 'number'}
                className={`px-3 py-2 rounded-lg transition-colors ${
                  page === currentPage
                    ? 'bg-blue-600 text-white'
                    : typeof page === 'number'
                    ? 'bg-gray-700 text-white hover:bg-gray-600'
                    : 'bg-gray-700 text-gray-500 cursor-default'
                }`}
              >
                {page}
              </button>
            ))}
          </div>

          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="flex items-center space-x-1 px-3 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <span>Next</span>
            <ChevronRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => onPageChange(totalPages)}
            disabled={currentPage === totalPages}
            className="flex items-center px-2 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Last page"
          >
            <SkipForward className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};