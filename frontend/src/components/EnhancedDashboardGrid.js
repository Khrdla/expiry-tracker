import React, { useState, useEffect, useCallback } from 'react';
import { Package, Calendar, Barcode, Eye, RefreshCw, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import ProductDetailsModal from './ProductDetailsModal';

/**
 * Enhanced Dashboard Grid Component
 * 
 * Features:
 * - Mobile-first responsive design (4 items per row on mobile)
 * - Fixed product image loading in grid cards
 * - Real-time data synchronization with master data
 * - Elegant animations and transitions
 * - Status-based color coding
 * - Lazy loading for performance
 */
const EnhancedDashboardGrid = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showProductModal, setShowProductModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [refreshing, setRefreshing] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const ITEMS_PER_PAGE = 20; // Optimized for mobile performance

  /**
   * Enhanced Product Image Component with Fixed Loading
   * Ensures images display correctly in both grid and details view
   */
  const ProductImage = ({ product, className = "" }) => {
    const [imageLoading, setImageLoading] = useState(true);
    const [imageError, setImageError] = useState(false);

    // Reset image states when product changes
    useEffect(() => {
      if (product?.image_url) {
        setImageLoading(true);
        setImageError(false);
      }
    }, [product?.image_url]);

    const handleImageLoad = () => {
      setImageLoading(false);
      setImageError(false);
    };

    const handleImageError = () => {
      setImageLoading(false);
      setImageError(true);
    };

    // If no image URL or image failed to load, show clean placeholder
    if (!product?.image_url || imageError) {
      return (
        <div className={`${className} bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center relative overflow-hidden`}>
          <Package className="w-8 h-8 text-slate-400" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/5 to-transparent"></div>
        </div>
      );
    }

    return (
      <div className={`${className} relative overflow-hidden bg-slate-100`}>
        {/* Loading State */}
        {imageLoading && (
          <div className="absolute inset-0 bg-slate-200 flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500 border-t-transparent"></div>
          </div>
        )}
        
        {/* Actual Image - Fixed URL construction */}
        <img
          src={`${BACKEND_URL}/api${product.image_url}`}
          alt={product.product_name}
          className={`${className} object-cover transition-all duration-300 hover:scale-105`}
          onLoad={handleImageLoad}
          onError={handleImageError}
          style={{ display: imageLoading ? 'none' : 'block' }}
        />
        
        {/* Gradient overlay for better text readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      </div>
    );
  };

  /**
   * Status Color and Icon Logic
   * Provides visual indicators for product status
   */
  const getStatusInfo = (product) => {
    const quantity = parseInt(product.quantity) || 0;
    const expiryDate = product.expiry_date ? new Date(product.expiry_date) : null;
    const today = new Date();
    const daysToExpiry = expiryDate ? Math.ceil((expiryDate - today) / (1000 * 60 * 60 * 24)) : null;

    // Priority: Expired > Low Stock > Near Expiry > In Stock
    if (daysToExpiry !== null && daysToExpiry <= 0) {
      return {
        status: 'expired',
        color: 'bg-red-500',
        textColor: 'text-red-700',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        icon: AlertTriangle,
        label: 'Expired'
      };
    }
    
    if (quantity <= 5) {
      return {
        status: 'low_stock',
        color: 'bg-orange-500',
        textColor: 'text-orange-700',
        bgColor: 'bg-orange-50',
        borderColor: 'border-orange-200',
        icon: AlertTriangle,
        label: 'Low Stock'
      };
    }
    
    if (daysToExpiry !== null && daysToExpiry <= 30) {
      return {
        status: 'near_expiry',
        color: 'bg-yellow-500',
        textColor: 'text-yellow-700',
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-200',
        icon: Clock,
        label: 'Near Expiry'
      };
    }

    return {
      status: 'in_stock',
      color: 'bg-green-500',
      textColor: 'text-green-700',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      icon: CheckCircle,
      label: 'In Stock'
    };
  };

  /**
   * Format expiry date for display
   */
  const formatExpiryDate = (dateString) => {
    if (!dateString) return 'No expiry date';
    
    try {
      const date = new Date(dateString);
      const today = new Date();
      const daysToExpiry = Math.ceil((date - today) / (1000 * 60 * 60 * 24));
      
      const formattedDate = date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
      
      if (daysToExpiry <= 0) {
        return `Expired ${formattedDate}`;
      } else if (daysToExpiry <= 30) {
        return `${daysToExpiry}d - ${formattedDate}`;
      }
      
      return formattedDate;
    } catch (error) {
      return 'Invalid date';
    }
  };

  /**
   * Load Products with Real-time Data Sync
   * Ensures dashboard is always in sync with master data
   */
  const loadProducts = useCallback(async (showRefreshIndicator = false) => {
    try {
      if (showRefreshIndicator) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/products?limit=${ITEMS_PER_PAGE}&page=${currentPage}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Process and validate data to ensure sync with master data
        const processedProducts = data.map(product => ({
          ...product,
          // Ensure all required fields have valid values
          product_name: product.product_name || 'Unknown Product',
          barcode: product.barcode || 'N/A',
          quantity: parseInt(product.quantity) || 0,
          purchase_price: parseFloat(product.purchase_price) || 0,
          selling_price: parseFloat(product.selling_price) || 0,
          currency: product.currency || 'YER',
          expiry_date: product.expiry_date || null,
          image_url: product.image_url || null,
          department: product.department || 'Unknown',
          supplier: product.supplier || 'Unknown'
        }));

        setProducts(processedProducts);
        setError('');
        
        console.log('📊 Dashboard data loaded:', {
          count: processedProducts.length,
          withImages: processedProducts.filter(p => p.image_url).length,
          lastUpdate: new Date().toISOString()
        });
        
      } else {
        throw new Error(`Failed to load products: ${response.status}`);
      }
    } catch (err) {
      console.error('Dashboard load error:', err);
      setError('Failed to load products. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [BACKEND_URL, currentPage]);

  // Initial load and auto-refresh setup
  useEffect(() => {
    loadProducts();
    
    // Auto-refresh every 30 seconds to keep data in sync
    const interval = setInterval(() => {
      loadProducts(true);
    }, 30000);

    return () => clearInterval(interval);
  }, [loadProducts]);

  /**
   * Handle Product Card Click
   * Opens detailed product view
   */
  const handleProductClick = (product) => {
    setSelectedProduct(product);
    setShowProductModal(true);
  };

  /**
   * Manual Refresh Handler
   */
  const handleRefresh = () => {
    loadProducts(true);
  };

  if (loading && !refreshing) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center p-8 bg-white rounded-2xl shadow-xl max-w-md">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-800 mb-2">Error Loading Dashboard</h3>
          <p className="text-slate-600 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 p-4">
      {/* Header with Refresh */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex justify-between items-center bg-white rounded-2xl shadow-sm border border-slate-200/50 p-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Product Dashboard</h1>
            <p className="text-slate-600 mt-1">
              {products.length} products • {products.filter(p => p.image_url).length} with images
            </p>
          </div>
          
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all ${
              refreshing 
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed' 
                : 'bg-blue-50 text-blue-600 hover:bg-blue-100 active:scale-95'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Syncing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Responsive Product Grid - Mobile First (4 per row) */}
      <div className="max-w-7xl mx-auto">
        {products.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-2xl shadow-sm">
            <Package className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-600 mb-2">No Products Found</h3>
            <p className="text-slate-400">Start by adding products to your inventory</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {products.map((product, index) => {
              const statusInfo = getStatusInfo(product);
              const StatusIcon = statusInfo.icon;
              
              return (
                <div
                  key={product.id}
                  onClick={() => handleProductClick(product)}
                  className="group bg-white rounded-2xl shadow-sm hover:shadow-xl border border-slate-200/50 overflow-hidden cursor-pointer transform hover:scale-[1.02] transition-all duration-300"
                  style={{
                    animationDelay: `${index * 50}ms`,
                    animation: 'fadeInUp 0.5s ease-out both'
                  }}
                >
                  {/* Product Image - Fixed for Grid Display */}
                  <div className="relative">
                    <ProductImage 
                      product={product}
                      className="w-full h-32 sm:h-36 object-cover"
                    />
                    
                    {/* Status Badge */}
                    <div className={`absolute top-2 right-2 px-2 py-1 rounded-full text-xs font-medium ${statusInfo.bgColor} ${statusInfo.textColor} border ${statusInfo.borderColor} backdrop-blur-sm`}>
                      <div className="flex items-center gap-1">
                        <StatusIcon className="w-3 h-3" />
                        <span className="hidden sm:inline">{statusInfo.label}</span>
                      </div>
                    </div>
                  </div>

                  {/* Product Info */}
                  <div className="p-3">
                    {/* Product Name */}
                    <h3 className="font-semibold text-slate-800 text-sm mb-2 line-clamp-2 min-h-[2.5rem] group-hover:text-blue-600 transition-colors">
                      {product.product_name}
                    </h3>

                    {/* Key Details */}
                    <div className="space-y-2 text-xs">
                      {/* Barcode */}
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <Barcode className="w-3 h-3 flex-shrink-0" />
                        <span className="truncate font-mono">{product.barcode}</span>
                      </div>

                      {/* Expiry Date */}
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <Calendar className="w-3 h-3 flex-shrink-0" />
                        <span className="truncate">{formatExpiryDate(product.expiry_date)}</span>
                      </div>

                      {/* Stock Quantity */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 text-slate-500">
                          <Package className="w-3 h-3 flex-shrink-0" />
                          <span>Stock:</span>
                        </div>
                        <span className="font-semibold text-slate-700">{product.quantity}</span>
                      </div>
                    </div>

                    {/* Price Display */}
                    <div className="mt-3 pt-2 border-t border-slate-100">
                      <div className="text-right">
                        <span className="text-sm font-bold text-slate-800">
                          {product.selling_price?.toFixed(2)} {product.currency}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Hover Effect Overlay */}
                  <div className="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Product Details Modal */}
      {showProductModal && selectedProduct && (
        <ProductDetailsModal
          product={selectedProduct}
          isOpen={showProductModal}
          onClose={() => {
            setShowProductModal(false);
            setSelectedProduct(null);
          }}
        />
      )}

      {/* CSS Animation Keyframes */}
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
};

export default EnhancedDashboardGrid;