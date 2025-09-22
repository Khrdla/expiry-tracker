import React from 'react';
import { X, Package, MapPin, Users, Calendar, DollarSign, Hash, Barcode } from 'lucide-react';

const ProductDetailsModal = ({ product, isOpen, onClose }) => {
  const [imageLoading, setImageLoading] = React.useState(true);
  const [imageError, setImageError] = React.useState(false);
  
  // Reset image states when product changes
  React.useEffect(() => {
    if (product?.image_url) {
      setImageLoading(true);
      setImageError(false);
    }
  }, [product?.image_url]);
  
  if (!isOpen || !product) return null;

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const formatCurrency = (amount, currency = 'YER') => {
    const numAmount = parseFloat(amount) || 0;
    
    // Handle different currencies with proper symbols
    switch (currency?.toUpperCase()) {
      case 'YER':
        return `${numAmount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })} YER`;
      case 'SAR':
        return `${numAmount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })} SAR`;
      case 'EUR':
        return `€${numAmount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
      case 'USD':
        return `$${numAmount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
      default:
        return `${numAmount.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${currency || 'YER'}`;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'in_stock': return 'bg-green-100 text-green-800 border-green-200';
      case 'low_stock': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'out_of_stock': return 'bg-red-100 text-red-800 border-red-200';
      case 'expired': return 'bg-red-100 text-red-800 border-red-200';
      case 'near_expiry': return 'bg-orange-100 text-orange-800 border-orange-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'in_stock': return 'In Stock';
      case 'low_stock': return 'Low Stock';
      case 'out_of_stock': return 'Out of Stock';
      case 'expired': return 'Expired';
      case 'near_expiry': return 'Near Expiry';
      default: return 'Unknown';
    }
  };

  const getDepartmentName = (deptCode) => {
    // Return department code exactly as it appears in Excel sheet
    return deptCode;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-auto max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-t-2xl">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
              <Package size={24} className="text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">Product Details</h2>
              <p className="text-green-100">Scanned from barcode</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
          >
            <X size={24} className="text-white" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Product Image - Prominent Display */}
          <div className="mb-8">
            <div className="flex justify-center">
              {product.image_url ? (
                <div className="w-full max-w-lg">
                  {imageLoading && !imageError && (
                    <div className="w-full h-80 bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100 rounded-3xl shadow-2xl border-8 border-white flex flex-col items-center justify-center">
                      <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></div>
                      <p className="text-slate-500 text-lg font-medium">Loading image...</p>
                    </div>
                  )}
                  
                  <img 
                    src={`${BACKEND_URL}${product.image_url}`}
                    alt={product.product_name}
                    className={`w-full h-80 object-cover rounded-3xl shadow-2xl border-8 border-white bg-white hover:shadow-3xl transition-all duration-500 transform hover:scale-[1.02] ${imageLoading || imageError ? 'hidden' : ''}`}
                    style={{
                      filter: 'drop-shadow(0 25px 50px rgba(0, 0, 0, 0.15))'
                    }}
                    onError={(e) => {
                      console.error('❌ Image failed to load:', `${BACKEND_URL}${product.image_url}`);
                      setImageLoading(false);
                      setImageError(true);
                    }}
                    onLoad={() => {
                      console.log('✅ Product image loaded successfully:', `${BACKEND_URL}${product.image_url}`);
                      setImageLoading(false);
                      setImageError(false);
                    }}
                  />
                  {imageError && (
                    <div className="w-full h-80 bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100 rounded-3xl shadow-2xl border-8 border-white flex flex-col items-center justify-center">
                      <div className="bg-white rounded-full p-6 mb-6 shadow-xl">
                        <svg className="w-16 h-16 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      </div>
                      <p className="text-slate-500 text-lg font-medium">Image not available</p>
                      <p className="text-slate-400 text-sm mt-2">Product image failed to load</p>
                      <p className="text-slate-300 text-xs mt-1 text-center px-4 break-all">
                        URL: {`${BACKEND_URL}${product.image_url}`}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="w-full max-w-lg h-80 bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100 rounded-3xl shadow-2xl border-8 border-white flex flex-col items-center justify-center">
                  <div className="bg-white rounded-full p-6 mb-6 shadow-xl">
                    <svg className="w-16 h-16 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <p className="text-slate-500 text-lg font-medium">No image available</p>
                  <p className="text-slate-400 text-sm mt-2">This product has no image uploaded</p>
                </div>
              )}
            </div>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-3">{product.product_name}</h1>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <span className={`px-4 py-2 rounded-full text-sm font-medium border ${getStatusColor(product.status)}`}>
                {getStatusText(product.status)}
              </span>
              <div className="bg-blue-50 border border-blue-200 px-4 py-2 rounded-full">
                <span className="text-blue-800 text-sm font-semibold">Qty: {product.quantity || 0}</span>
              </div>
            </div>
          </div>

          {/* Product Information Grid */}
          <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">
                Basic Information
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <Hash size={16} className="text-gray-500" />
                  <div>
                    <p className="text-sm text-gray-600">Item Number</p>
                    <p className="font-medium">{product.item_number || 'Not specified'}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Barcode size={16} className="text-gray-500" />
                  <div>
                    <p className="text-sm text-gray-600">Barcode</p>
                    <p className="font-medium font-mono">{product.barcode || 'Not specified'}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Package size={16} className="text-gray-500" />
                  <div>
                    <p className="text-sm text-gray-600">Department</p>
                    <p className="font-medium">{getDepartmentName(product.department)}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Package size={16} className="text-gray-500" />
                  <div>
                    <p className="text-sm text-gray-600">Section</p>
                    <p className="font-medium">{product.section || 'Not specified'}</p>
                  </div>
                </div>

                {product.brand && (
                  <div className="flex items-center space-x-3">
                    <Package size={16} className="text-gray-500" />
                    <div>
                      <p className="text-sm text-gray-600">Brand</p>
                      <p className="font-medium">{product.brand}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Pricing and Stock */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">
                Pricing & Stock
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <DollarSign size={16} className="text-green-500" />
                  <div>
                    <p className="text-sm text-gray-600">Purchase Price</p>
                    <p className="font-medium text-green-600">
                      {formatCurrency(product.purchase_price || 0, product.purchase_currency)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <DollarSign size={16} className="text-blue-500" />
                  <div>
                    <p className="text-sm text-gray-600">Selling Price</p>
                    <p className="font-medium text-blue-600">
                      {formatCurrency(product.selling_price || 0, 'YER')}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Package size={16} className="text-purple-500" />
                  <div>
                    <p className="text-sm text-gray-600">Stock Value</p>
                    <p className="font-medium text-purple-600">
                      {formatCurrency((product.quantity || 0) * (product.purchase_price || 0), product.purchase_currency)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Users size={16} className="text-gray-500" />
                  <div>
                    <p className="text-sm text-gray-600">Supplier</p>
                    <p className="font-medium">{product.supplier || 'Not specified'}</p>
                  </div>
                </div>

                {product.location && (
                  <div className="flex items-center space-x-3">
                    <MapPin size={16} className="text-gray-500" />
                    <div>
                      <p className="text-sm text-gray-600">Location</p>
                      <p className="font-medium">{product.location}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Additional Information */}
          {(product.family || product.sub_family || product.arabic_description) && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">
                Additional Information
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {product.family && (
                  <div>
                    <p className="text-sm text-gray-600">Family</p>
                    <p className="font-medium">{product.family}</p>
                  </div>
                )}

                {product.sub_family && (
                  <div>
                    <p className="text-sm text-gray-600">Sub Family</p>
                    <p className="font-medium">{product.sub_family}</p>
                  </div>
                )}

                {product.arabic_description && (
                  <div className="md:col-span-2">
                    <p className="text-sm text-gray-600">Arabic Description</p>
                    <p className="font-medium" dir="rtl">{product.arabic_description}</p>
                  </div>
                )}
              </div>
            </div>
          )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-center space-x-4 pt-6 border-t border-gray-200">
            <button
              onClick={onClose}
              className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Close
            </button>
            <button
              onClick={() => {
                // Add to favorites or other action
                console.log('Product action:', product);
              }}
              className="px-6 py-3 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-lg hover:from-green-600 hover:to-blue-600 transition-colors"
            >
              Add to Favorites
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetailsModal;