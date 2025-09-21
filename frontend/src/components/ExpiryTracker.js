import React, { useState, useEffect } from 'react';
import { Plus, Filter, Calendar, Package, AlertTriangle, Clock, Search, Download } from 'lucide-react';

const ExpiryTracker = ({ user }) => {
  const [activeTab, setActiveTab] = useState('add-item');  // 'add-item' or 'expiry-list'
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    department: 'all',
    section: 'all',
    status: 'all'
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Fetch products for expiry list
  const fetchProducts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/products`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
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

  useEffect(() => {
    if (activeTab === 'expiry-list') {
      fetchProducts();
    }
  }, [activeTab]);

  const getExpiryStatus = (product) => {
    if (!product.expiry_date) return 'no-date';
    
    const now = new Date();
    const expiryDate = new Date(product.expiry_date);
    const daysUntilExpiry = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));

    if (daysUntilExpiry < 0) return 'expired';
    if (daysUntilExpiry <= 7) return 'near-expiry';
    if (daysUntilExpiry <= 15 && product.section === 'S-10 Beverages') return 'near-expiry';
    return 'good';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'expired': return 'bg-red-100 text-red-800 border-red-200';
      case 'near-expiry': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'good': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'expired': return 'Expired';
      case 'near-expiry': return 'Near Expiry';
      case 'good': return 'Good';
      default: return 'No Date';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-4 md:p-6 rounded-xl">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 flex items-center justify-center bg-white bg-opacity-20 rounded-xl">
              <img 
                src="/geant_logo.jpeg" 
                alt="Geant Logo" 
                className="w-full h-full object-contain"
              />
            </div>
            <div className="text-center lg:text-left">
              <h1 className="text-2xl md:text-3xl font-bold">Expiry Tracker</h1>
              <p className="text-orange-100 text-sm md:text-base">Manage product expiry dates and add new items</p>
            </div>
          </div>
          
          <div className="mt-4 lg:mt-0">
            <button
              onClick={async () => {
                const token = localStorage.getItem('token');
                if (!token) {
                  console.error('❌ No authentication token found');
                  alert('Please log in again to export data.');
                  return;
                }

                try {
                  console.log('🔍 Exporting expiry tracker data...');
                  
                  const response = await fetch(`${BACKEND_URL}/api/export/expiry-tracker`, {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${token}`,
                      'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({})
                  });
                  
                  console.log('📊 Expiry tracker export response status:', response.status);
                  
                  if (response.ok) {
                    const blob = await response.blob();
                    console.log('📥 Received expiry tracker blob:', blob.size, 'bytes');
                    
                    // Create download link
                    const downloadUrl = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = downloadUrl;
                    link.download = `expiry_tracker_export_${new Date().toISOString().split('T')[0]}.xlsx`;
                    
                    // Trigger download
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    // Clean up
                    window.URL.revokeObjectURL(downloadUrl);
                    
                    console.log('✅ Expiry tracker export completed successfully');
                  } else {
                    const errorText = await response.text();
                    console.error('❌ Expiry tracker export failed:', response.status, errorText);
                    
                    if (response.status === 401) {
                      alert('❌ Not authenticated. Please log in again.');
                    } else if (response.status === 403) {
                      alert('❌ Access denied. Admin privileges required.');
                    } else {
                      alert(`❌ Export failed: ${response.status} ${errorText}`);
                    }
                  }
                } catch (error) {
                  console.error('❌ Expiry tracker export error:', error);
                  alert(`❌ Export failed: ${error.message}`);
                }
              }}
              className="flex items-center space-x-2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Download size={16} />
              <span>Export Expiry Data</span>
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-xl shadow-lg p-2">
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('add-item')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-lg transition-colors ${
              activeTab === 'add-item'
                ? 'bg-orange-500 text-white'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Plus size={20} />
            <span>Add New Item</span>
          </button>
          
          <button
            onClick={() => setActiveTab('expiry-list')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-lg transition-colors ${
              activeTab === 'expiry-list'
                ? 'bg-orange-500 text-white'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Clock size={20} />
            <span>Expiry List</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'add-item' ? (
        <AddNewItemForm user={user} />
      ) : (
        <ExpiryList 
          products={products} 
          loading={loading}
          filters={filters}
          setFilters={setFilters}
          getExpiryStatus={getExpiryStatus}
          getStatusColor={getStatusColor}
          getStatusText={getStatusText}
        />
      )}
    </div>
  );
};

// Add New Item Form Component
const AddNewItemForm = ({ user }) => {
  const [formData, setFormData] = useState({
    product_name: '',
    item_number: '',
    barcode: '',
    supplier: '',
    purchase_price: '',
    purchase_currency: 'YER',
    selling_price: '',
    expiry_date: '',
    section: '',
    department: '',
    quantity: '',
    description: '',
    notes: ''
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [lookupQuery, setLookupQuery] = useState('');
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupResults, setLookupResults] = useState(null);
  const [showLookupResults, setShowLookupResults] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Excel lookup function
  const performExcelLookup = async (query) => {
    if (!query.trim()) {
      setLookupResults(null);
      setShowLookupResults(false);
      return;
    }

    setLookupLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/excel-lookup?query=${encodeURIComponent(query)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLookupResults(data);
        setShowLookupResults(true);
        
        // If found, show success message
        if (data.found) {
          setMessage({ 
            type: 'success', 
            text: `Found "${data.product_name}" - Click "Auto-Fill" to populate form` 
          });
        } else {
          setMessage({ type: 'info', text: data.message });
        }
      } else if (response.status === 401) {
        setMessage({ type: 'error', text: 'Authentication expired. Please refresh the page and log in again.' });
        // Optionally redirect to login
        setTimeout(() => {
          localStorage.removeItem('token');
          window.location.href = '/';
        }, 3000);
      } else if (response.status === 403) {
        setMessage({ type: 'error', text: 'Access denied. Please check your permissions.' });
      } else if (response.status === 404) {
        setMessage({ type: 'info', text: 'No products found matching your search.' });
      } else {
        setMessage({ type: 'error', text: `Lookup failed: Server error (${response.status})` });
      }
    } catch (error) {
      console.error('Lookup error:', error);
      setMessage({ type: 'error', text: 'Network error during lookup' });
    } finally {
      setLookupLoading(false);
    }
  };

  // Auto-fill form with lookup results
  const autoFillForm = () => {
    if (lookupResults && lookupResults.found) {
      setFormData({
        ...formData,
        product_name: lookupResults.product_name,
        item_number: lookupResults.item_number,
        barcode: lookupResults.barcode,
        supplier: lookupResults.supplier,
        purchase_price: lookupResults.purchase_price.toString(),
        purchase_currency: lookupResults.purchase_currency,
        selling_price: lookupResults.selling_price.toString(),
        section: lookupResults.section,
        department: lookupResults.department,
        description: lookupResults.arabic_description || ''
      });
      
      setMessage({ 
        type: 'success', 
        text: 'Form auto-filled! Please add expiry date, quantity, and notes.' 
      });
      setShowLookupResults(false);
    }
  };

  // Debounced lookup
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (lookupQuery) {
        performExcelLookup(lookupQuery);
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [lookupQuery]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('token');
      
      // Prepare data for API
      const apiData = {
        ...formData,
        purchase_price: parseFloat(formData.purchase_price) || 0,
        selling_price: parseFloat(formData.selling_price) || 0,
        quantity: parseInt(formData.quantity) || 0,
        expiry_date: formData.expiry_date || null
      };

      const response = await fetch(`${BACKEND_URL}/api/products`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(apiData)
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Product added successfully!' });
        setFormData({
          product_name: '',
          item_number: '',
          barcode: '',
          supplier: '',
          purchase_price: '',
          purchase_currency: 'YER',
          selling_price: '',
          expiry_date: '',
          section: '',
          department: '',
          quantity: '',
          description: '',
          notes: ''
        });
        setLookupQuery('');
        setLookupResults(null);
        setShowLookupResults(false);
      } else {
        const errorData = await response.json();
        setMessage({ type: 'error', text: errorData.detail || 'Failed to add product' });
      }
    } catch (error) {
      console.error('Error adding product:', error);
      setMessage({ type: 'error', text: 'Network error occurred' });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-6">Add New Item</h2>

      {/* Excel Lookup Section */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="text-lg font-medium text-blue-800 mb-3 flex items-center">
          <Search size={20} className="mr-2" />
          Excel Product Lookup
        </h3>
        
        <div className="flex space-x-3">
          <div className="flex-1">
            <input
              type="text"
              value={lookupQuery}
              onChange={(e) => setLookupQuery(e.target.value)}
              placeholder="Type product name or scan barcode to auto-fill form..."
              className="w-full px-4 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          {lookupLoading && (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            </div>
          )}
        </div>

        {/* Lookup Results */}
        {showLookupResults && lookupResults && lookupResults.found && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-green-800">{lookupResults.product_name}</h4>
                <div className="text-sm text-green-700 mt-1">
                  <p>Code: {lookupResults.item_number}</p>
                  <p>Department: {lookupResults.department}</p>
                  <p>Section: {lookupResults.section}</p>
                  <p>Supplier: {lookupResults.supplier}</p>
                  <p>Price: {lookupResults.purchase_price} {lookupResults.purchase_currency}</p>
                </div>
              </div>
              <button
                onClick={autoFillForm}
                className="ml-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
              >
                Auto-Fill Form
              </button>
            </div>
          </div>
        )}
      </div>

      {message.text && (
        <div className={`mb-4 p-4 rounded-lg ${
          message.type === 'success' 
            ? 'bg-green-50 text-green-700 border border-green-200'
            : message.type === 'info'
            ? 'bg-blue-50 text-blue-700 border border-blue-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Basic Information - Auto-filled from Excel */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800 border-b border-gray-200 pb-2">
            Product Details (Auto-filled from Excel)
          </h3>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Product Name *</label>
            <input
              type="text"
              name="product_name"
              value={formData.product_name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-gray-50"
              placeholder="Use lookup above to auto-fill"
              readOnly={lookupResults?.found}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Item Number</label>
            <input
              type="text"
              name="item_number"
              value={formData.item_number}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-gray-50"
              readOnly={lookupResults?.found}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Barcode</label>
            <input
              type="text"
              name="barcode"
              value={formData.barcode}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-gray-50"
              readOnly={lookupResults?.found}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Supplier</label>
            <input
              type="text"
              name="supplier"
              value={formData.supplier}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-gray-50"
              readOnly={lookupResults?.found}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
            <input
              type="text"
              name="department"
              value={formData.department}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-gray-50"
              readOnly={lookupResults?.found}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Section</label>
            <input
              type="text"
              name="section"
              value={formData.section}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-gray-50"
              readOnly={lookupResults?.found}
            />
          </div>
        </div>

        {/* Pricing Information - Auto-filled from Excel */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800 border-b border-gray-200 pb-2">
            Pricing (Auto-filled from Excel)
          </h3>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Price</label>
            <div className="flex space-x-2">
              <input
                type="number"
                step="0.01"
                name="purchase_price"
                value={formData.purchase_price}
                onChange={handleChange}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-gray-50"
                readOnly={lookupResults?.found}
              />
              <input
                type="text"
                name="purchase_currency"
                value={formData.purchase_currency}
                onChange={handleChange}
                className="w-20 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-gray-50 text-center"
                readOnly={lookupResults?.found}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Selling Price (YER)</label>
            <input
              type="number"
              step="0.01"
              name="selling_price"
              value={formData.selling_price}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-gray-50"
              readOnly={lookupResults?.found}
            />
          </div>
        </div>

        {/* User Input Fields */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800 border-b border-gray-200 pb-2">
            User Input Required
          </h3>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label>
            <input
              type="number"
              name="quantity"
              value={formData.quantity}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              placeholder="Enter quantity"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date *</label>
            <input
              type="date"
              name="expiry_date"
              value={formData.expiry_date}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              placeholder="Additional notes or comments"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-gray-50"
              readOnly={lookupResults?.found}
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="md:col-span-2 lg:col-span-3">
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 px-6 rounded-lg font-medium transition-colors ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-orange-500 hover:bg-orange-600 text-white'
            }`}
          >
            {loading ? 'Adding Product...' : 'Add Product'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Expiry List Component
const ExpiryList = ({ products, loading, filters, setFilters, getExpiryStatus, getStatusColor, getStatusText }) => {
  const filteredProducts = products.filter(product => {
    if (filters.department !== 'all' && product.department !== filters.department) return false;
    if (filters.section !== 'all' && product.section !== filters.section) return false;
    if (filters.status !== 'all' && getExpiryStatus(product) !== filters.status) return false;
    return true;
  });

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4 md:mb-0">Expiry List</h2>
        
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <select
            value={filters.department}
            onChange={(e) => setFilters({...filters, department: e.target.value})}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          >
            <option value="all">All Departments</option>
            <option value="01-FMG">01-FMG</option>
            <option value="01-CGD">01-CGD</option>
            <option value="01-OPSS">01-OPSS</option>
          </select>

          <select
            value={filters.status}
            onChange={(e) => setFilters({...filters, status: e.target.value})}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="expired">Expired</option>
            <option value="near-expiry">Near Expiry</option>
            <option value="good">Good</option>
            <option value="no-date">No Date</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredProducts.map((product) => {
            const status = getExpiryStatus(product);
            return (
              <div key={product.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-gray-800 text-sm line-clamp-2">{product.product_name}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(status)}`}>
                    {getStatusText(status)}
                  </span>
                </div>
                
                <div className="space-y-1 text-xs text-gray-600">
                  <div>Department: {product.department}</div>
                  <div>Section: {product.section || 'N/A'}</div>
                  <div>Quantity: {product.quantity || 0}</div>
                  {product.expiry_date && (
                    <div>Expiry: {new Date(product.expiry_date).toLocaleDateString()}</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!loading && filteredProducts.length === 0 && (
        <div className="text-center py-12">
          <Package size={48} className="text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No products found matching the selected filters.</p>
        </div>
      )}
    </div>
  );
};

export default ExpiryTracker;