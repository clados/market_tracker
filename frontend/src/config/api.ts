export const API_CONFIG = {
  // Backend configuration
  BACKEND_URL: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',
  
  // Market filtering defaults
  DEFAULT_DAYS_OLD: parseInt(import.meta.env.VITE_DEFAULT_DAYS_OLD || '90'),
  DEFAULT_MIN_LIQUIDITY: parseInt(import.meta.env.VITE_DEFAULT_MIN_LIQUIDITY || '1000'),
  
  // Rate limiting configuration
  RETRY_ATTEMPTS: parseInt(import.meta.env.VITE_API_RETRY_ATTEMPTS || '3'),
  RETRY_DELAY: parseInt(import.meta.env.VITE_API_RETRY_DELAY || '1000'),
  
  // API endpoints
  ENDPOINTS: {
    MARKETS: '/api/markets',
    MARKET_DETAIL: '/api/markets',
    MARKET_HISTORY: '/api/markets',
    CATEGORIES: '/api/categories',
    HEALTH: '/health'
  }
} as const;

// Debug logging
console.log('API_CONFIG loaded with:', {
  BACKEND_URL: API_CONFIG.BACKEND_URL,
  VITE_BACKEND_URL: import.meta.env.VITE_BACKEND_URL
});

export const getBackendUrl = (endpoint: string) => {
  return `${API_CONFIG.BACKEND_URL}${endpoint}`;
};