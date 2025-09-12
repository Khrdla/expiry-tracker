import React, { useState, useEffect } from 'react';
import { Search, Filter, Package, Plus, Edit, Trash2, Download, Upload, BarChart3, Camera } from 'lucide-react';
import BarcodeScanner from './BarcodeScanner';
import ProductDetailsModal from './ProductDetailsModal';

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
  const [showScanner, setShowScanner] = useState(false);
  const [showProductDetails, setShowProductDetails] = useState(false);
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 50,
    total: 0
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const getDepartmentName = (deptCode) => {
    const names = {
      '01-FMG': 'Fresh & Food Grocery',
      '01-CGD': 'Consumer Goods & Drinks',
      '01-OPSS': 'Operations & Special Services'
    };
    return names[deptCode] || deptCode;
  };

  const formatCurrency = (amount, currency = 'YER') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency === 'SAR' ? 'SAR' : currency === 'EUR' ? 'EUR' : 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(amount);
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
        skip: pagination.skip.toString(),
        limit: pagination.limit.toString()
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
      <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white p-6 rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Product Management</h1>
            <p className="text-green-100">Manage inventory across all departments</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowScanner(true)}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition-all flex items-center space-x-2"
            >
              <Camera size={16} />
              <span>Scan Barcode</span>
            </button>
            <button
              onClick={exportData}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition-all flex items-center space-x-2"
            >
              <Download size={16} />
              <span>Export</span>
            </button>
            <button
              onClick={() => setShowModal(true)}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition-all flex items-center space-x-2"
            >
              <Plus size={16} />
              <span>Add Product</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search products, SKU, barcode..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          {/* Department Filter */}
          <select
            value={filters.department}
            onChange={(e) => handleFilterChange('department', e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {products.map((product) => (
            <div
              key={product.id}
              className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-shadow cursor-pointer"
              onClick={() => handleProductClick(product)}
            >
              {/* Product Image Placeholder */}
              <div className="h-48 bg-gradient-to-br from-green-100 to-blue-100 flex items-center justify-center">
                <Package size={48} className="text-green-600" />
              </div>

              <div className="p-4">
                {/* Product Name */}
                <h3 className="font-semibold text-gray-800 mb-2 line-clamp-2">
                  {product.product_name}
                </h3>

                {/* Item Number & Department */}
                <div className="text-sm text-gray-600 mb-2">
                  <div>Item: {product.item_number || 'N/A'}</div>
                  <div>{getDepartmentName(product.department)}</div>
                </div>

                {/* Status Badge */}
                <div className="flex justify-between items-center mb-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(product.status)}`}>
                    {getStatusIcon(product.status)} {product.status?.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className="text-sm font-semibold text-gray-700">
                    {product.quantity} units
                  </span>
                </div>

                {/* Price Information */}
                <div className="border-t border-gray-200 pt-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">Purchase:</span>
                    <span className="font-medium">
                      {formatCurrency(product.purchase_price, product.purchase_currency)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">Stock Value:</span>
                    <span className="font-semibold text-green-600">
                      {formatCurrency(product.quantity * product.purchase_price, product.purchase_currency)}
                    </span>
                  </div>
                </div>

                {/* Supplier */}
                <div className="mt-2 text-xs text-gray-500 truncate">
                  Supplier: {product.supplier}
                </div>
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
                          {formatCurrency(selectedProduct.selling_price, selectedProduct.purchase_currency)}
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
                  <button className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2">
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
    </div>
  );
};

export default EnhancedProductManagement;