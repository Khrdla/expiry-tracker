import React, { useState, useEffect, useRef } from 'react';
import { Search, Filter, Plus, Download, Camera, Edit, Eye, Package, AlertTriangle } from 'lucide-react';
import EnhancedBarcodeScanner from './EnhancedBarcodeScanner';
import ProductDetailsModal from './ProductDetailsModal';
import EditProductModal from './EditProductModal';

/**
 * Enhanced Product Management with Improved Data Handling
 * 
 * Fixes:
 * - Proper null/undefined handling for all data fields
 * - Fallback values to prevent displaying indices
 * - Enhanced error boundaries and logging
 * - Improved image handling with error states
 * - Stable component rendering
 */
const EnhancedProductManagement = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  // Separate search states for different behaviors
  const [productNameSearch, setProductNameSearch] = useState('');
  const [barcodeSearch, setBarcodeSearch] = useState('');
  const [activeSearchTerm, setActiveSearchTerm] = useState(''); // This drives the actual filtering
  const [selectedDepartment, setSelectedDepartment] = useState('all');
  const [selectedSection, setSelectedSection] = useState('all');
  const [selectedSupplier, setSelectedSupplier] = useState('all');
  const [showScanner, setShowScanner] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showProductDetails, setShowProductDetails] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 50;

  const [filterOptions, setFilterOptions] = useState({
    departments: [],
    sections: [],
    suppliers: []
  });

  // Enhanced debug info
  const [debugInfo, setDebugInfo] = useState({
    lastLoad: null,
    productCount: 0,
    apiCalls: 0,
    errors: 0
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const fileInputRef = useRef(null);

  // Enhanced logging system
  const logActivity = (action, details = {}) => {
    const timestamp = new Date().toISOString();
    console.log(`[ProductManagement] ${timestamp} - ${action}:`, details);
    
    setDebugInfo(prev => ({
      ...prev,
      lastActivity: timestamp,
      apiCalls: action.includes('API') ? prev.apiCalls + 1 : prev.apiCalls,
      errors: action.includes('ERROR') ? prev.errors + 1 : prev.errors
    }));
  };

  useEffect(() => {
    loadProducts();
    loadFilterOptions();
  }, [activeSearchTerm, selectedDepartment, selectedSection, selectedSupplier, currentPage]);

  // Enhanced product loading with comprehensive error handling
  const loadProducts = async () => {
    try {
      setLoading(true);
      logActivity('API_CALL_PRODUCTS', {
        page: currentPage,
        search: activeSearchTerm,
        department: selectedDepartment
      });
      
      const token = localStorage.getItem('token');
      
      if (!token) {
        logActivity('ERROR_NO_TOKEN');
        setError('Authentication token not found');
        return;
      }
      
      const queryParams = new URLSearchParams({
        page: currentPage.toString(),
        limit: itemsPerPage.toString(),
        ...(activeSearchTerm && { search: activeSearchTerm }),
        ...(selectedDepartment !== 'all' && { department: selectedDepartment }),
        ...(selectedSection !== 'all' && { section: selectedSection }),
        ...(selectedSupplier !== 'all' && { supplier: selectedSupplier })
      });
      
      const url = `${BACKEND_URL}/api/products?${queryParams.toString()}`;
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        const processedProducts = processProductsData(data.products || data || []);
        
        const productsWithImages = processedProducts.filter(p => p.image_url);
        console.log('📦 Products Loaded:', {
          total: processedProducts.length,
          withImages: productsWithImages.length,
          sampleImageUrls: productsWithImages.slice(0, 3).map(p => ({ 
            name: p.product_name, 
            imageUrl: p.image_url 
          }))
        });
        
        logActivity('PRODUCTS_LOADED_SUCCESS', {
          count: processedProducts.length,
          hasImages: productsWithImages.length
        });
        
        setProducts(processedProducts);
        setError('');
        
        setDebugInfo(prev => ({
          ...prev,
          lastLoad: new Date().toISOString(),
          productCount: processedProducts.length
        }));
      } else {
        const errorText = await response.text();
        logActivity('PRODUCTS_LOAD_ERROR', {
          status: response.status,
          error: errorText
        });
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
    } catch (error) {
      logActivity('PRODUCTS_LOAD_EXCEPTION', { error: error.message });
      console.error('Products error:', error);
      setError(`Failed to load products: ${error.message}`);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  // Enhanced product data processing
  const processProductsData = (rawProducts) => {
    if (!Array.isArray(rawProducts)) {
      logActivity('ERROR_INVALID_PRODUCTS_DATA', { type: typeof rawProducts });
      return [];
    }

    return rawProducts.map((product, index) => ({
      // Core identification
      id: product?.id || `product_${index}_${Date.now()}`,
      product_name: safeName(product?.product_name) || `Product ${index + 1}`,
      item_number: safeString(product?.item_number) || `ITM-${index + 1}`,
      barcode: safeString(product?.barcode) || '',
      
      // Organization
      department: safeString(product?.department) || 'Unknown Department',
      section: safeString(product?.section) || 'Unknown Section',
      family: safeString(product?.family) || '',
      sub_family: safeString(product?.sub_family) || '',
      
      // Supplier and pricing
      supplier: safeName(product?.supplier) || 'Unknown Supplier',
      purchase_price: safeNumber(product?.purchase_price, 0),
      purchase_currency: safeString(product?.purchase_currency) || 'USD',
      selling_price: safeNumber(product?.selling_price, 0),
      
      // Inventory
      quantity: safeNumber(product?.quantity, 0),
      status: safeString(product?.status) || 'unknown',
      
      // Media
      image_url: safeString(product?.image_url) || null,
      
      // Preserve other fields safely
      ...Object.fromEntries(
        Object.entries(product || {}).filter(([key, value]) => 
          !['id', 'product_name', 'item_number', 'barcode', 'department', 
            'section', 'supplier', 'purchase_price', 'selling_price', 
            'quantity', 'status', 'image_url'].includes(key)
        ).map(([key, value]) => [key, value])
      )
    }));
  };

  // Enhanced filter options loading
  const loadFilterOptions = async () => {
    try {
      logActivity('API_CALL_FILTER_OPTIONS');
      const token = localStorage.getItem('token');
      
      if (!token) {
        logActivity('ERROR_NO_TOKEN_FILTERS');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/filters`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        logActivity('FILTER_OPTIONS_SUCCESS', {
          departments: data?.departments?.length || 0,
          sections: data?.sections?.length || 0,
          suppliers: data?.suppliers?.length || 0
        });
        
        const processedOptions = {
          departments: processFilterArray(data?.departments, 'Department'),
          sections: processFilterArray(data?.sections, 'Section'),
          suppliers: processFilterArray(data?.suppliers, 'Supplier')
        };
        
        setFilterOptions(processedOptions);
      } else {
        logActivity('FILTER_OPTIONS_ERROR', { status: response.status });
      }
    } catch (error) {
      logActivity('FILTER_OPTIONS_EXCEPTION', { error: error.message });
      console.error('Failed to load filter options:', error);
    }
  };

  // Enhanced export functionality
  const handleExport = async (format) => {
    try {
      logActivity('EXPORT_REQUESTED', { format });
      const token = localStorage.getItem('token');
      
      if (!token) {
        logActivity('ERROR_NO_TOKEN_EXPORT');
        setError('Authentication token not found');
        return;
      }
      
      const queryParams = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(selectedDepartment !== 'all' && { department: selectedDepartment }),
        ...(selectedSection !== 'all' && { section: selectedSection }),
        ...(selectedSupplier !== 'all' && { supplier: selectedSupplier })
      });
      
      const response = await fetch(`${BACKEND_URL}/api/export/products/${format}?${queryParams.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `products_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        logActivity('EXPORT_SUCCESS', { format });
      } else {
        throw new Error(`Export failed with status ${response.status}`);
      }
    } catch (error) {
      logActivity('EXPORT_ERROR', { format, error: error.message });
      console.error('Export error:', error);
      setError(`Failed to export ${format}: ${error.message}`);
    }
  };

  // Enhanced image upload handling
  const handleImageUpload = (productId, file) => {
    if (!file || !productId) {
      logActivity('ERROR_INVALID_UPLOAD_PARAMS', { productId, hasFile: !!file });
      return;
    }

    logActivity('IMAGE_UPLOAD_STARTED', { productId, fileName: file.name });
    
    const formData = new FormData();
    formData.append('image', file);
    
    const token = localStorage.getItem('token');
    fetch(`${BACKEND_URL}/api/products/${productId}/image`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        logActivity('IMAGE_UPLOAD_SUCCESS', { productId, imageUrl: data.image_url });
        
        // Clear any previous errors
        setError('');
        
        // Show success message briefly  
        setError('✅ Image uploaded successfully!');
        setTimeout(() => setError(''), 3000);
        
        // Reload products to show updated image
        loadProducts();
      } else {
        throw new Error(data.message || 'Upload failed');
      }
    })
    .catch(error => {
      logActivity('IMAGE_UPLOAD_ERROR', { productId, error: error.message });
      console.error('Upload error:', error);
      setError(`Failed to upload image: ${error.message}`);
    });
  };

  // Utility functions for data safety
  const safeNumber = (value, fallback = 0) => {
    const num = Number(value);
    return isNaN(num) ? fallback : num;
  };

  const safeString = (value) => {
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
    return '';
  };

  const safeName = (value) => {
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
    if (typeof value === 'number') {
      return `Item_${value}`;
    }
    return '';
  };

  const processFilterArray = (array, prefix) => {
    if (!Array.isArray(array)) return [];
    
    return array.map((item, index) => {
      if (typeof item === 'string' && item.trim()) {
        return item.trim();
      }
      if (typeof item === 'object' && item?.name) {
        return item.name;
      }
      return `${prefix}_${index + 1}`;
    }).filter(Boolean);
  };

  // Enhanced currency formatting
  const formatCurrency = (amount, currency = 'USD') => {
    const safeAmount = safeNumber(amount, 0);
    
    if (currency && ['YER', 'SAR', 'EUR'].includes(currency)) {
      return `${safeAmount.toFixed(2)} ${currency}`;
    }
    
    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency || 'USD'
      }).format(safeAmount);
    } catch (error) {
      return `${safeAmount} ${currency}`;
    }
  };

  // Enhanced status color function
  const getStatusColor = (status) => {
    const statusMap = {
      'in_stock': 'bg-green-100 text-green-800',
      'low_stock': 'bg-yellow-100 text-yellow-800',
      'out_of_stock': 'bg-red-100 text-red-800'
    };
    return statusMap[status] || 'bg-gray-100 text-gray-800';
  };

  // Enhanced product handlers
  const handleEditProduct = (product) => {
    logActivity('EDIT_PRODUCT_REQUESTED', { productId: product?.id });
    setSelectedProduct(product);
    setShowEditModal(true);
  };

  const handleViewProduct = (product) => {
    logActivity('VIEW_PRODUCT_REQUESTED', { productId: product?.id });
    setSelectedProduct(product);
    setShowProductDetails(true);
  };

  const handleProductSaved = () => {
    logActivity('PRODUCT_SAVED');
    loadProducts();
    setShowEditModal(false);
  };

  // Enhanced Product Image Component
  const ProductImage = ({ product, className }) => {
    const [imageError, setImageError] = useState(false);
    const [imageLoading, setImageLoading] = useState(true);

    const handleImageError = () => {
      const fullImageUrl = `${BACKEND_URL}/api${product?.image_url}`;
      console.error('🖼️ ProductImage Error:', {
        productId: product?.id,
        productName: product?.product_name,
        imageUrl: product?.image_url,
        fullUrl: fullImageUrl
      });
      logActivity('IMAGE_ERROR', { productId: product?.id, imageUrl: product?.image_url, fullUrl: fullImageUrl });
      setImageError(true);
      setImageLoading(false);
    };

    const handleImageLoad = () => {
      const fullImageUrl = `${BACKEND_URL}/api${product?.image_url}`;
      console.log('✅ ProductImage Loaded:', {
        productId: product?.id,
        productName: product?.product_name,
        imageUrl: product?.image_url,
        fullUrl: fullImageUrl
      });
      logActivity('IMAGE_LOADED', { productId: product?.id, imageUrl: product?.image_url });
      setImageLoading(false);
    };

    if (!product?.image_url || imageError) {
      return (
        <div className={`${className} bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center relative`}>
          <Package className="w-8 h-8 text-gray-400" />
          {product?.image_url && imageError && (
            <div className="absolute bottom-1 left-1 right-1">
              <p className="text-xs text-red-500 bg-white bg-opacity-80 px-1 rounded truncate">
                Image failed
              </p>
            </div>
          )}
          {!product?.image_url && (
            <div className="absolute bottom-1 left-1 right-1">
              <p className="text-xs text-gray-500 bg-white bg-opacity-80 px-1 rounded truncate">
                No image
              </p>
            </div>
          )}
        </div>
      );
    }

    return (
      <div className={`${className} relative overflow-hidden`}>
        {imageLoading && (
          <div className="absolute inset-0 bg-gray-200 flex items-center justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div>
          </div>
        )}
        <img
          src={`${BACKEND_URL}/api${product.image_url}`}
          alt={product.product_name}
          className={`${className} object-cover transition-opacity duration-200`}
          onError={handleImageError}
          onLoad={handleImageLoad}
          style={{ display: imageLoading ? 'none' : 'block' }}
        />
      </div>
    );
  };

  const totalPages = Math.ceil(products.length / itemsPerPage);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading products...</p>
          {debugInfo.apiCalls > 0 && (
            <p className="text-sm text-gray-400 mt-2">API calls: {debugInfo.apiCalls}</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Enhanced Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Enhanced Product Management</h1>
              <p className="text-gray-600 mt-1">
                Showing {products.length.toLocaleString()} products
                {debugInfo.lastLoad && (
                  <span className="text-sm text-gray-400 ml-2">
                    • Updated {new Date(debugInfo.lastLoad).toLocaleTimeString()}
                  </span>
                )}
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
              <div className="flex gap-2">
                <div className="relative group">
                  <button
                    onClick={() => handleExport('excel')}
                    className="flex items-center gap-2 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
                  >
                    <Download size={18} />
                    Export Excel
                  </button>
                </div>
                
                <button
                  onClick={() => setShowScanner(true)}
                  className="flex items-center gap-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                >
                  <Camera size={18} />
                  Multi-Scan
                </button>
                
                <button
                  onClick={() => {
                    setError('Add product functionality will be implemented soon');
                  }}
                  className="flex items-center gap-2 bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors"
                >
                  <Plus size={18} />
                  Add Product
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
            <AlertTriangle size={20} className="flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Product Management Error</p>
              <p className="text-sm">{error}</p>
              {debugInfo.errors > 0 && (
                <p className="text-xs mt-1">Total errors: {debugInfo.errors}</p>
              )}
            </div>
          </div>
        )}

        {/* Enhanced Search and Filters */}
        <div className="mb-6 bg-white p-6 rounded-lg shadow">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search Products</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search by name, barcode, or item number..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Department</label>
                <select
                  value={selectedDepartment}
                  onChange={(e) => setSelectedDepartment(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Departments</option>
                  {filterOptions.departments?.map((dept, index) => (
                    <option key={`dept-${index}`} value={dept}>
                      {safeName(dept) || `Department ${index + 1}`}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Section</label>
                <select
                  value={selectedSection}
                  onChange={(e) => setSelectedSection(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Sections</option>
                  {filterOptions.sections?.map((section, index) => (
                    <option key={`section-${index}`} value={section}>
                      {safeName(section) || `Section ${index + 1}`}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Supplier</label>
                <select
                  value={selectedSupplier}
                  onChange={(e) => setSelectedSupplier(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Suppliers</option>
                  {filterOptions.suppliers?.map((supplier, index) => (
                    <option key={`supplier-${index}`} value={supplier}>
                      {safeName(supplier) || `Supplier ${index + 1}`}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Products Grid */}
        {products.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No products found</p>
            <p className="text-gray-400">Try adjusting your search or filters</p>
            {debugInfo.errors > 0 && (
              <p className="text-red-400 text-sm mt-2">
                {debugInfo.errors} error(s) occurred while loading
              </p>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product) => (
              <div key={product.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
                {/* Product Image */}
                <div className="relative">
                  <ProductImage 
                    product={product}
                    className="w-full h-48 rounded-t-lg"
                  />
                  
                  {/* Action Buttons */}
                  <div className="absolute top-2 right-2 flex gap-1">
                    <button
                      onClick={() => handleViewProduct(product)}
                      className="p-2 bg-white bg-opacity-90 hover:bg-opacity-100 rounded-full shadow transition-colors"
                      title="View Details"
                    >
                      <Eye size={16} className="text-blue-600" />
                    </button>
                    <button
                      onClick={() => handleEditProduct(product)}
                      className="p-2 bg-white bg-opacity-90 hover:bg-opacity-100 rounded-full shadow transition-colors"
                      title="Edit Product"
                    >
                      <Edit size={16} className="text-green-600" />
                    </button>
                  </div>

                  {/* Status Badge */}
                  <div className="absolute top-2 left-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(product.status)}`}>
                      {(product.status || 'unknown').replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Enhanced Product Details */}
                <div className="p-4">
                  <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2" title={product.product_name}>
                    {product.product_name}
                  </h3>
                  
                  <div className="space-y-1 text-sm text-gray-600">
                    <p><span className="font-medium">Item:</span> {product.item_number}</p>
                    <p><span className="font-medium">Dept:</span> {product.department}</p>
                    <p><span className="font-medium">Supplier:</span> {product.supplier}</p>
                    {product.barcode && (
                      <p><span className="font-medium">Barcode:</span> {product.barcode}</p>
                    )}
                  </div>

                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-sm text-gray-500">Quantity</p>
                        <p className="font-semibold">{product.quantity.toLocaleString()}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-500">Purchase Price</p>
                        <p className="font-semibold text-green-600">
                          {formatCurrency(product.purchase_price, product.purchase_currency)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="mt-2 text-center">
                      <p className="text-xs text-gray-500">Stock Value</p>
                      <p className="font-bold text-blue-600">
                        {formatCurrency(product.quantity * product.purchase_price, product.purchase_currency)}
                      </p>
                    </div>
                  </div>

                  {/* Image Upload */}
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) {
                          handleImageUpload(product.id, file);
                        }
                      }}
                      accept="image/*"
                      className="hidden"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="w-full text-xs bg-gray-100 text-gray-700 py-1 rounded hover:bg-gray-200 transition-colors"
                    >
                      {product.image_url ? 'Update Image' : 'Upload Image'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Enhanced Pagination */}
        {totalPages > 1 && (
          <div className="mt-8 flex justify-center">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              
              <div className="flex items-center space-x-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const page = i + 1;
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-3 py-2 text-sm font-medium rounded-md ${
                        currentPage === page
                          ? 'bg-blue-500 text-white'
                          : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
              </div>
              
              <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Enhanced Barcode Scanner Modal */}
      <EnhancedBarcodeScanner
        isOpen={showScanner}
        onClose={() => setShowScanner(false)}
        onProductFound={(product) => {
          setSelectedProduct(product);
          setShowScanner(false);
          setShowProductDetails(true);
        }}
      />

      {/* Product Details Modal */}
      <ProductDetailsModal
        isOpen={showProductDetails}
        onClose={() => setShowProductDetails(false)}
        product={selectedProduct}
      />

      {/* Edit Product Modal */}
      <EditProductModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        product={selectedProduct}
        onSave={handleProductSaved}
      />
    </div>
  );
};

export default EnhancedProductManagement;