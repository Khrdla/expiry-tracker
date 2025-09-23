import React, { useState, useEffect } from 'react';
import { Search, Filter, Package, Plus, Edit, Trash2, Download, Upload, BarChart3, Camera, X } from 'lucide-react';
import WorkingCameraScanner from './WorkingCameraScanner';
import ProductDetailsModal from './ProductDetailsModal';

// Simple ProductImage component to handle image loading errors safely
const ProductImage = ({ imageUrl, alt }) => {
  const [imageError, setImageError] = useState(false);
  
  if (!imageUrl || imageError) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="bg-white rounded-full p-3 mb-2 shadow-md">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <span className="text-gray-400 text-xs font-medium">No image</span>
      </div>
    );
  }
  
  return (
    <img 
      src={imageUrl}
      alt={alt}
      className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
      onError={() => setImageError(true)}
    />
  );
};

const EnhancedProductManagement = ({ user, selectedFilters = {} }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    department: selectedFilters.department || 'all',
    section: selectedFilters.section || 'all',
    supplier: selectedFilters.supplier || '',
    status: selectedFilters.status || 'all',
    search: ''
  });
  const [filterOptions, setFilterOptions] = useState({
    departments: [],
    sections: [],
    suppliers: [],
    families: [],
    currencies: []
  });
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editFormData, setEditFormData] = useState({});
  const [showScanner, setShowScanner] = useState(false);
  const [showProductDetails, setShowProductDetails] = useState(false);
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 50,
    total: 0
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const getDepartmentName = (deptCode) => {
    // Return department code exactly as it appears in Excel sheet
    return deptCode;
  };

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
    const colors = {
      'in_stock': 'bg-green-100 text-green-800',
      'low_stock': 'bg-yellow-100 text-yellow-800',
      'out_of_stock': 'bg-red-100 text-red-800',
      'expired': 'bg-red-200 text-red-900',
      'near_expiry': 'bg-orange-100 text-orange-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'in_stock': '✅',
      'low_stock': '⚠️',
      'out_of_stock': '🚫',
      'expired': '❌',
      'near_expiry': '⏰'
    };
    return icons[status] || '📦';
  };

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [filters, pagination.skip]);

  const fetchFilterOptions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/filters`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFilterOptions(data);
      }
    } catch (error) {
      console.error('Error fetching filter options:', error);
    }
  };

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        skip: (pagination.skip || 0).toString(),
        limit: (pagination.limit || 10).toString()
      });

      if (filters.department && filters.department !== 'all') {
        params.append('department', filters.department);
      }
      if (filters.section && filters.section !== 'all') {
        params.append('section', filters.section);
      }
      if (filters.supplier) {
        params.append('supplier', filters.supplier);
      }
      if (filters.status && filters.status !== 'all') {
        params.append('status', filters.status);
      }
      if (filters.search) {
        params.append('search', filters.search);
      }

      const response = await fetch(`${BACKEND_URL}/api/products?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, skip: 0 })); // Reset to first page
  };

  const handleProductClick = (product) => {
    setSelectedProduct(product);
    setShowModal(true);
  };

  const exportData = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      
      if (filters.department && filters.department !== 'all') {
        params.append('department', filters.department);
      }
      if (filters.section && filters.section !== 'all') {
        params.append('section', filters.section);
      }
      if (filters.supplier) {
        params.append('supplier', filters.supplier);
      }

      const response = await fetch(`${BACKEND_URL}/api/export/excel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          export_type: 'excel',
          department: filters.department !== 'all' ? filters.department : null,
          section: filters.section !== 'all' ? filters.section : null,
          supplier: filters.supplier || null
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `inventory_export_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white p-4 md:p-6 rounded-xl">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 flex items-center justify-center bg-white bg-opacity-20 rounded-xl">
              <img 
                src="/geant_logo.jpeg" 
                alt="Geant Logo" 
                className="w-full h-full object-contain"
              />
            </div>
            <div className="text-center lg:text-left">
              <h1 className="text-2xl md:text-3xl font-bold">Product Management</h1>
              <p className="text-green-100 text-sm md:text-base">Manage inventory across all departments</p>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2 lg:space-x-3">
            <button
              onClick={() => setShowScanner(true)}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-3 md:px-4 py-2 rounded-lg transition-all flex items-center justify-center space-x-2 text-sm md:text-base"
            >
              <Camera size={16} />
              <span className="hidden sm:inline">Scan Barcode</span>
              <span className="sm:hidden">Scan</span>
            </button>
            <button
              onClick={exportData}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-3 md:px-4 py-2 rounded-lg transition-all flex items-center justify-center space-x-2 text-sm md:text-base"
            >
              <Download size={16} />
              <span className="hidden sm:inline">Export</span>
              <span className="sm:hidden">📊</span>
            </button>
            <button
              onClick={() => setShowModal(true)}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-3 md:px-4 py-2 rounded-lg transition-all flex items-center justify-center space-x-2 text-sm md:text-base"
            >
              <Plus size={16} />
              <span className="hidden sm:inline">Add Product</span>
              <span className="sm:hidden">Add</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-lg p-4 md:p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
          {/* Search */}
          <div className="relative lg:col-span-2">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search products, SKU, barcode..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm md:text-base"
            />
          </div>

          {/* Department Filter */}
          <select
            value={filters.department}
            onChange={(e) => handleFilterChange('department', e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm md:text-base"
          >
            <option value="all">All Departments</option>
            {filterOptions.departments.map(dept => (
              <option key={dept.value} value={dept.value}>
                {getDepartmentName(dept.value)}
              </option>
            ))}
          </select>

          {/* Section Filter */}
          <select
            value={filters.section}
            onChange={(e) => handleFilterChange('section', e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm md:text-base"
          >
            <option value="all">All Sections</option>
            {filterOptions.sections.map(section => (
              <option key={section.value} value={section.value}>
                {section.value}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm md:text-base"
          >
            <option value="all">All Status</option>
            <option value="in_stock">In Stock</option>
            <option value="low_stock">Low Stock</option>
            <option value="out_of_stock">Out of Stock</option>
            <option value="near_expiry">Near Expiry</option>
            <option value="expired">Expired</option>
          </select>

          {/* Supplier Filter */}
          <input
            type="text"
            placeholder="Filter by supplier..."
            value={filters.supplier}
            onChange={(e) => handleFilterChange('supplier', e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm md:text-base"
          />
        </div>

        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Showing {products.length} products</span>
          <div className="flex space-x-2">
            <span className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded mr-1"></div>
              In Stock
            </span>
            <span className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 rounded mr-1"></div>
              Low Stock
            </span>
            <span className="flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded mr-1"></div>
              Out of Stock
            </span>
          </div>
        </div>
      </div>

      {/* Products Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-16 w-16 md:h-32 md:w-32 border-b-2 border-green-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
          {products.map((product) => (
            <div
              key={product.id}
              className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-shadow cursor-pointer"
              onClick={() => handleProductClick(product)}
            >
              {/* Product Image */}
              <div className="h-48 md:h-56 relative overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100">
                <ProductImage 
                  imageUrl={product.image_url ? `${BACKEND_URL}${product.image_url}` : null}
                  alt={product.product_name}
                />
                
                {/* Product Status Badge */}
                <div className="absolute top-2 right-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    product.quantity <= 0 ? 'bg-red-100 text-red-800' :
                    product.quantity <= 10 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {product.quantity <= 0 ? 'Out' : product.quantity <= 10 ? 'Low' : 'In Stock'}
                  </span>
                </div>
              </div>

              <div className="p-3 md:p-4">
                {/* Product Name */}
                <h3 className="font-semibold text-gray-800 mb-2 line-clamp-2 text-sm md:text-base">
                  {product.product_name}
                </h3>

                {/* Item Number & Department */}
                <div className="text-xs md:text-sm text-gray-600 mb-2">
                  <div>#{product.item_number || 'N/A'}</div>
                  <div>{getDepartmentName(product.department)}</div>
                </div>

                {/* Pricing Information */}
                <div className="mb-3 space-y-1">
                  <div className="flex justify-between items-center text-xs md:text-sm">
                    <span className="text-gray-600">Purchase:</span>
                    <span className="font-medium text-green-600">
                      {product.purchase_price ? `${product.purchase_price.toFixed(2)} ${product.purchase_currency || 'YER'}` : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs md:text-sm">
                    <span className="text-gray-600">Stock Value:</span>
                    <span className="font-medium text-blue-600">
                      {product.purchase_price && product.quantity 
                        ? `${(product.purchase_price * product.quantity).toFixed(2)} ${product.purchase_currency || 'YER'}`
                        : '0'}
                    </span>
                  </div>
                </div>

                {/* Quantity & Status */}
                <div className="flex justify-between items-center mb-3">
                  <div className="text-xs md:text-sm">
                    <span className="text-gray-600">Qty: </span>
                    <span className="font-bold">{product.quantity || 0}</span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(product.status)}`}>
                    {getStatusIcon(product.status)} {product.status?.replace('_', ' ').toUpperCase()}
                  </span>
                </div>

                {/* Supplier */}
                {product.supplier && (
                  <div className="text-xs text-gray-500 truncate">
                    Supplier: {product.supplier}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {products.length === pagination.limit && (
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => setPagination(prev => ({ ...prev, skip: Math.max(0, prev.skip - prev.limit) }))}
            disabled={pagination.skip === 0}
            className="px-4 py-2 bg-green-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            onClick={() => setPagination(prev => ({ ...prev, skip: prev.skip + prev.limit }))}
            className="px-4 py-2 bg-green-600 text-white rounded-lg"
          >
            Next
          </button>
        </div>
      )}

      {/* Product Detail Modal */}
      {showModal && selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-semibold text-gray-800">Product Details</h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left Column - Product Image and Basic Info */}
                <div>
                  <div className="h-64 bg-gradient-to-br from-green-100 to-blue-100 rounded-lg flex items-center justify-center mb-6">
                    <Package size={64} className="text-green-600" />
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-600">Product Name</label>
                      <p className="text-lg font-semibold text-gray-800">{selectedProduct.product_name}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-600">Item Number</label>
                        <p className="text-gray-800">{selectedProduct.item_number || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Barcode</label>
                        <p className="text-gray-800">{selectedProduct.barcode || 'N/A'}</p>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-gray-600">Status</label>
                      <div className="mt-1">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedProduct.status)}`}>
                          {getStatusIcon(selectedProduct.status)} {selectedProduct.status?.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Column - Detailed Information */}
                <div className="space-y-6">
                  {/* Department & Category Info */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-800 mb-3">Classification</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <label className="font-medium text-gray-600">Department</label>
                        <p className="text-gray-800">{getDepartmentName(selectedProduct.department)}</p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-600">Section</label>
                        <p className="text-gray-800">{selectedProduct.section}</p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-600">Family</label>
                        <p className="text-gray-800">{selectedProduct.family}</p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-600">Sub Family</label>
                        <p className="text-gray-800">{selectedProduct.sub_family}</p>
                      </div>
                    </div>
                  </div>

                  {/* Stock Information */}
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-800 mb-3">Stock Information</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <label className="font-medium text-gray-600">Current Stock</label>
                        <p className="text-2xl font-bold text-blue-600">{selectedProduct.quantity}</p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-600">Location</label>
                        <p className="text-gray-800">{selectedProduct.location || 'Not specified'}</p>
                      </div>
                    </div>
                  </div>

                  {/* Pricing Information */}
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-800 mb-3">Pricing</h3>
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-600">Purchase Price:</span>
                        <span className="font-semibold">
                          {formatCurrency(selectedProduct.purchase_price, selectedProduct.purchase_currency)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-medium text-gray-600">Selling Price:</span>
                        <span className="font-semibold">
                          {formatCurrency(selectedProduct.selling_price, 'YER')}
                        </span>
                      </div>
                      <div className="flex justify-between border-t pt-2">
                        <span className="font-medium text-gray-600">Total Stock Value:</span>
                        <span className="font-bold text-green-600 text-lg">
                          {formatCurrency(selectedProduct.quantity * selectedProduct.purchase_price, selectedProduct.purchase_currency)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Supplier Information */}
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-800 mb-3">Supplier Details</h3>
                    <div className="text-sm space-y-2">
                      <div>
                        <label className="font-medium text-gray-600">Supplier Name</label>
                        <p className="text-gray-800">{selectedProduct.supplier}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="font-medium text-gray-600">Supplier Code</label>
                          <p className="text-gray-800">{selectedProduct.supplier_code || 'N/A'}</p>
                        </div>
                        <div>
                          <label className="font-medium text-gray-600">Currency</label>
                          <p className="text-gray-800">{selectedProduct.purchase_currency}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Additional Information */}
                  {(selectedProduct.arabic_description || selectedProduct.brand) && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-semibold text-gray-800 mb-3">Additional Information</h3>
                      <div className="text-sm space-y-2">
                        {selectedProduct.brand && (
                          <div>
                            <label className="font-medium text-gray-600">Brand</label>
                            <p className="text-gray-800">{selectedProduct.brand}</p>
                          </div>
                        )}
                        {selectedProduct.arabic_description && (
                          <div>
                            <label className="font-medium text-gray-600">Arabic Description</label>
                            <p className="text-gray-800" dir="rtl">{selectedProduct.arabic_description}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-4 mt-8 pt-6 border-t border-gray-200">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-6 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Close
                </button>
                {(user?.role === 'admin' || user?.role === 'manager') && (
                  <button 
                    onClick={() => {
                      setEditFormData(selectedProduct);
                      setShowModal(false);
                      setShowEditModal(true);
                    }}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                  >
                    <Edit size={16} />
                    <span>Edit Product</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && products.length === 0 && (
        <div className="text-center py-12">
          <Package size={64} className="text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">No products found</h3>
          <p className="text-gray-600 mb-6">Try adjusting your filters or search terms.</p>
          <button
            onClick={() => setFilters({
              department: 'all',
              section: 'all',
              supplier: '',
              status: 'all',
              search: ''
            })}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Edit Product Modal */}
      {showEditModal && (
        <EditProductModal
          product={editFormData}
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setEditFormData({});
          }}
          onSave={(updatedProduct) => {
            // Update the product in the list
            setProducts(products.map(p => p.id === updatedProduct.id ? updatedProduct : p));
            setShowEditModal(false);
            setEditFormData({});
          }}
        />
      )}

      {/* Barcode Scanner Modal */}
      <FixedMobileScanner
        isOpen={showScanner}
        onClose={() => setShowScanner(false)}
        onProductFound={(product) => {
          setSelectedProduct(product);
          setShowScanner(false);
          setShowProductDetails(true);
        }}
      />

      {/* Product Details Modal (for scanned products) */}
      <ProductDetailsModal
        product={selectedProduct}
        isOpen={showProductDetails}
        onClose={() => {
          setShowProductDetails(false);
          setSelectedProduct(null);
        }}
      />
    </div>
  );
};

// Edit Product Modal Component
const EditProductModal = ({ product, isOpen, onClose, onSave }) => {
  const [formData, setFormData] = useState(product || {});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [imageFile, setImageFile] = useState(null);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  
  const [imagePreview, setImagePreview] = useState(
    product?.image_url ? `${BACKEND_URL}${product.image_url}` : null
  );

  useEffect(() => {
    if (product) {
      setFormData(product);
      // Use direct static file serving (without /api prefix)
      const imageUrl = product.image_url ? `${BACKEND_URL}${product.image_url}` : null;
      setImagePreview(imageUrl);
    }
  }, [product, BACKEND_URL]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('token');
      
      // Prepare form data for API
      const apiData = {
        ...formData,
        purchase_price: parseFloat(formData.purchase_price) || 0,
        selling_price: parseFloat(formData.selling_price) || 0,
        quantity: parseInt(formData.quantity) || 0
      };

      // Update product
      const response = await fetch(`${BACKEND_URL}/api/products/${product.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(apiData)
      });

      if (response.ok) {
        const updatedProduct = await response.json();
        
        // Handle image upload if there's a new image
        if (imageFile) {
          const imageFormData = new FormData();
          imageFormData.append('image', imageFile);
          
          const imageResponse = await fetch(`${BACKEND_URL}/api/products/${product.id}/image`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
            },
            body: imageFormData
          });

          if (imageResponse.ok) {
            const imageData = await imageResponse.json();
            updatedProduct.image_url = imageData.image_url;
            // Update the preview to show the uploaded image from server
            setImagePreview(`${BACKEND_URL}${imageData.image_url}`);
          }
        }

        setMessage({ type: 'success', text: 'Product updated successfully!' });
        setTimeout(() => {
          onSave(updatedProduct);
        }, 1000);
      } else {
        const errorData = await response.json();
        setMessage({ type: 'error', text: errorData.detail || 'Failed to update product' });
      }
    } catch (error) {
      console.error('Error updating product:', error);
      setMessage({ type: 'error', text: 'Network error occurred' });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-t-xl">
          <h2 className="text-2xl font-bold">Edit Product</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
          >
            <X size={24} className="text-white" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {message.text && (
            <div className={`mb-4 p-4 rounded-lg ${
              message.type === 'success' 
                ? 'bg-green-50 text-green-700 border border-green-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}>
              {message.text}
            </div>
          )}

          <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">Basic Information</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product Name</label>
                <input
                  type="text"
                  name="product_name"
                  value={formData.product_name || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Item Number</label>
                <input
                  type="text"
                  name="item_number"
                  value={formData.item_number || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Barcode</label>
                <input
                  type="text"
                  name="barcode"
                  value={formData.barcode || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Supplier</label>
                <input
                  type="text"
                  name="supplier"
                  value={formData.supplier || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                <select
                  name="department"
                  value={formData.department || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="">Select Department</option>
                  <option value="01-FMG">01-FMG</option>
                  <option value="01-CGD">01-CGD</option>
                  <option value="01-OPSS">01-OPSS</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Section</label>
                <input
                  type="text"
                  name="section"
                  value={formData.section || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">Pricing & Stock</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Price</label>
                <div className="flex space-x-2">
                  <input
                    type="number"
                    step="0.01"
                    name="purchase_price"
                    value={formData.purchase_price || ''}
                    onChange={handleChange}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                  <select
                    name="purchase_currency"
                    value={formData.purchase_currency || 'YER'}
                    onChange={handleChange}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="YER">YER</option>
                    <option value="SAR">SAR</option>
                    <option value="EUR">EUR</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Selling Price (YER)</label>
                <input
                  type="number"
                  step="0.01"
                  name="selling_price"
                  value={formData.selling_price || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                <input
                  type="number"
                  name="quantity"
                  value={formData.quantity || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label>
                <input
                  type="date"
                  name="expiry_date"
                  value={formData.expiry_date ? formData.expiry_date.split('T')[0] : ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              {/* Image Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product Image</label>
                <div className="space-y-3">
                  {imagePreview ? (
                    <div className="w-32 h-32 bg-gray-100 rounded-lg overflow-hidden border border-blue-500">
                      <img 
                        src={imagePreview} 
                        alt="Product preview" 
                        className="w-full h-full object-cover"
                        onError={() => {
                          setImagePreview(null); // This will trigger the else case below
                        }}
                      />
                    </div>
                  ) : (
                    <div className="w-32 h-32 bg-gray-200 rounded-lg flex items-center justify-center border border-red-500">
                      <span className="text-gray-500 text-sm">No image</span>
                    </div>
                  )}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500">Upload product image (JPG, PNG, max 5MB)</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  name="description"
                  value={formData.description || ''}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="lg:col-span-2 flex justify-end space-x-4 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                  loading
                    ? 'bg-gray-400 cursor-not-allowed text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EnhancedProductManagement;