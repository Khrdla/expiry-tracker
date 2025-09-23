import React, { useState, useEffect, useRef } from 'react';
import { Search, Filter, Plus, Download, Camera, Edit, Eye, Package } from 'lucide-react';
import CleanCameraScanner from './CleanCameraScanner';
import ProductDetailsModal from './ProductDetailsModal';
import EditProductModal from './EditProductModal';

const EnhancedProductManagement = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
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

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadProducts();
    loadFilterOptions();
  }, [searchTerm, selectedDepartment, selectedSection, selectedSupplier, currentPage]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const queryParams = new URLSearchParams({
        page: currentPage.toString(),
        limit: itemsPerPage.toString(),
        ...(searchTerm && { search: searchTerm }),
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
        setProducts(data.products || data || []);
        setError('');
      } else {
        throw new Error('Failed to load products');
      }
    } catch (error) {
      console.error('Products error:', error);
      setError('Failed to load products');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const loadFilterOptions = async () => {
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
      console.error('Failed to load filter options:', error);
    }
  };

  const handleExport = async (format) => {
    try {
      const token = localStorage.getItem('token');
      
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
        a.download = `products.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        throw new Error(`Failed to export ${format}`);
      }
    } catch (error) {
      console.error('Export error:', error);
      setError(`Failed to export ${format}`);
    }
  };

  const handleImageUpload = (productId, file) => {
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
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        loadProducts(); // Reload to show updated image
        setError('');
      } else {
        throw new Error(data.message || 'Upload failed');
      }
    })
    .catch(error => {
      console.error('Upload error:', error);
      setError('Failed to upload image');
    });
  };

  const formatCurrency = (amount, currency = 'USD') => {
    if (currency && ['YER', 'SAR', 'EUR'].includes(currency)) {
      return `${amount} ${currency}`;
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD'
    }).format(amount || 0);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'in_stock': return 'bg-green-100 text-green-800';
      case 'low_stock': return 'bg-yellow-100 text-yellow-800';
      case 'out_of_stock': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleEditProduct = (product) => {
    setSelectedProduct(product);
    setShowEditModal(true);
  };

  const handleViewProduct = (product) => {
    setSelectedProduct(product);
    setShowProductDetails(true);
  };

  const handleProductSaved = () => {
    loadProducts();
    setShowEditModal(false);
  };

  // Component for handling product images with error fallback
  const ProductImage = ({ product, className }) => {
    const [imageError, setImageError] = useState(false);
    const [imageLoading, setImageLoading] = useState(true);

    const handleImageError = () => {
      setImageError(true);
      setImageLoading(false);
    };

    const handleImageLoad = () => {
      setImageLoading(false);
    };

    if (!product.image_url || imageError) {
      return (
        <div className={`${className} bg-gray-200 flex items-center justify-center`}>
          <Package className="w-8 h-8 text-gray-400" />
        </div>
      );
    }

    return (
      <div className={`${className} relative`}>
        {imageLoading && (
          <div className="absolute inset-0 bg-gray-200 flex items-center justify-center">
            <Package className="w-8 h-8 text-gray-400" />
          </div>
        )}
        <img
          src={`${BACKEND_URL}${product.image_url}`}
          alt={product.product_name}
          className={`${className} object-cover`}
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Product Management</h1>
              <p className="text-gray-600 mt-1">
                Showing {products.length} products
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
              <div className="flex gap-2">
                <div className="relative">
                  <button
                    onClick={() => {}}
                    className="flex items-center gap-2 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
                  >
                    <Download size={18} />
                    Export
                  </button>
                  <div className="hidden group-hover:block absolute right-0 mt-1 w-32 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                    <button
                      onClick={() => handleExport('excel')}
                      className="block w-full text-left px-4 py-2 hover:bg-gray-100"
                    >
                      Excel
                    </button>
                    <button
                      onClick={() => handleExport('pdf')}
                      className="block w-full text-left px-4 py-2 hover:bg-gray-100"
                    >
                      PDF
                    </button>
                  </div>
                </div>
                
                <button
                  onClick={() => setShowScanner(true)}
                  className="flex items-center gap-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                >
                  <Camera size={18} />
                  Scan Barcode
                </button>
                
                <button
                  onClick={() => {
                    // Future: Add new product functionality
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

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Search and Filters */}
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
                  {filterOptions.departments?.map(dept => (
                    <option key={dept.value || dept} value={dept.value || dept}>
                      {dept.label || dept}
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
                  {filterOptions.sections?.map(section => (
                    <option key={section.value || section} value={section.value || section}>
                      {section.label || section}
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
                  {filterOptions.suppliers?.map(supplier => (
                    <option key={supplier.value || supplier} value={supplier.value || supplier}>
                      {supplier.label || supplier}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Products Grid */}
        {products.length === 0 ? (
          <div className="text-center py-12">
            <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No products found</p>
            <p className="text-gray-400">Try adjusting your search or filters</p>
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
                      {product.status?.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Product Details */}
                <div className="p-4">
                  <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                    {product.product_name}
                  </h3>
                  
                  <div className="space-y-1 text-sm text-gray-600">
                    <p><span className="font-medium">Item:</span> {product.item_number}</p>
                    <p><span className="font-medium">Dept:</span> {product.department}</p>
                    <p><span className="font-medium">Supplier:</span> {product.supplier}</p>
                  </div>

                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-sm text-gray-500">Quantity</p>
                        <p className="font-semibold">{product.quantity || 0}</p>
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
                        {formatCurrency((product.quantity || 0) * (product.purchase_price || 0), product.purchase_currency)}
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
                      Upload Image
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-8 flex justify-center">
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              
              <span className="px-3 py-2 text-sm font-medium text-gray-700">
                Page {currentPage} of {totalPages}
              </span>
              
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

      {/* Barcode Scanner Modal */}
      <CleanCameraScanner
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