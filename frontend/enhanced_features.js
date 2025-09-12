// Enhanced frontend features for inventory system
// This code will be integrated into App.js

// Out of Stock Screen Component
const OutOfStockScreen = () => {
  const [outOfStockProducts, setOutOfStockProducts] = useState([]);
  const [sections, setSections] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [filters, setFilters] = useState({ section: '', supplier: '' });
  const [loading, setLoading] = useState(false);

  const fetchOutOfStockProducts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.section) params.append('section', filters.section);
      if (filters.supplier) params.append('supplier', filters.supplier);
      
      const response = await axios.get(`${API}/products/out-of-stock?${params}`, {
        headers: getAuthHeaders(token)
      });
      
      setOutOfStockProducts(response.data.out_of_stock_products || []);
    } catch (error) {
      setError('Error fetching out-of-stock products');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportOutOfStock = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.section) params.append('section', filters.section);
      if (filters.supplier) params.append('supplier', filters.supplier);
      
      const response = await axios.get(`${API}/export/out-of-stock-excel?${params}`, {
        responseType: 'blob',
        headers: getAuthHeaders(token)
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `out_of_stock_products_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Out-of-stock products exported successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError('Error exporting out-of-stock products');
      console.error('Error:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
          <h2 className="text-2xl font-bold text-red-600 mb-4 md:mb-0">
            🚨 Out of Stock Products
          </h2>
          <button
            onClick={exportOutOfStock}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            📥 Export Out of Stock
          </button>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Section</label>
            <select
              value={filters.section}
              onChange={(e) => setFilters({...filters, section: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent"
            >
              <option value="">All Sections</option>
              {sections.map(section => (
                <option key={section} value={section}>{section}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Supplier</label>
            <select
              value={filters.supplier}
              onChange={(e) => setFilters({...filters, supplier: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent"
            >
              <option value="">All Suppliers</option>
              {suppliers.map(supplier => (
                <option key={supplier} value={supplier}>{supplier}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={fetchOutOfStockProducts}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors mb-6"
        >
          🔍 Apply Filters
        </button>

        {/* Out of Stock Products Grid */}
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : outOfStockProducts.length === 0 ? (
          <div className="text-center py-8 text-green-600">
            🎉 No out-of-stock products found! All items are in stock.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {outOfStockProducts.map(product => (
              <OutOfStockProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Out of Stock Product Card Component
const OutOfStockProductCard = ({ product }) => {
  return (
    <div className="bg-white border-2 border-red-200 rounded-lg shadow-lg p-4 relative">
      {/* Out of Stock Badge */}
      <div className="absolute top-2 right-2 bg-red-600 text-white px-2 py-1 rounded-full text-xs font-bold">
        🚨 OUT OF STOCK
      </div>

      {/* Product Image */}
      <div className="flex justify-center mb-4 mt-6">
        {product.image_url ? (
          <img 
            src={`${BACKEND_URL}${product.image_url}`}
            alt={product.product_name}
            className="w-20 h-20 object-contain rounded-lg border border-gray-200"
            style={{ aspectRatio: '1:1', objectFit: 'contain' }}
          />
        ) : (
          <div className="w-20 h-20 bg-red-100 rounded-lg flex items-center justify-center border border-red-200">
            <span className="text-red-400 text-2xl">📦</span>
          </div>
        )}
      </div>

      {/* Product Details */}
      <div className="space-y-2">
        <h3 className="font-bold text-gray-900 text-center mb-2 leading-tight">
          {product.product_name}
        </h3>

        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Supplier:</span>
            <span className="font-medium">{product.supplier}</span>
          </div>

          {product.barcode && (
            <div className="flex justify-between">
              <span className="text-gray-600">Barcode:</span>
              <span className="font-mono text-xs bg-gray-100 px-1 rounded">{product.barcode}</span>
            </div>
          )}

          <div className="flex justify-between">
            <span className="text-gray-600">Stock:</span>
            <span className="font-bold text-red-600">0 (OUT OF STOCK)</span>
          </div>

          {product.purchase_price_formatted && (
            <div className="flex justify-between">
              <span className="text-gray-600">Purchase Price:</span>
              <span className="font-medium text-blue-600">{product.purchase_price_formatted}</span>
            </div>
          )}

          {product.selling_price_formatted && (
            <div className="flex justify-between">
              <span className="text-gray-600">Selling Price:</span>
              <span className="font-medium text-green-600">{product.selling_price_formatted}</span>
            </div>
          )}

          <div className="flex justify-between">
            <span className="text-gray-600">Section:</span>
            <span className="font-medium">{product.section}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Enhanced Product Card Component with Out of Stock Indicators
const EnhancedProductCard = ({ product, showStockValue = false }) => {
  const isExpired = product.expiry_date && new Date(product.expiry_date) < new Date();
  const isExpiringSoon = product.expiry_date && 
    new Date(product.expiry_date) <= new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) &&
    new Date(product.expiry_date) >= new Date();
  
  const isOutOfStock = product.quantity === 0;
  const isLowStock = product.quantity > 0 && product.quantity <= 5;
  
  // Calculate stock value with currency
  const stockValue = product.purchase_price && product.purchase_currency ? 
    (product.quantity * product.purchase_price) : null;
  
  return (
    <div className={`bg-white rounded-xl shadow-lg border-2 p-4 mx-2 my-3 max-w-sm mx-auto relative ${
      isOutOfStock ? 'border-red-300 bg-red-50' : 'border-gray-200'
    }`}>
      
      {/* Out of Stock Indicator */}
      {isOutOfStock && (
        <div className="absolute top-2 right-2 bg-red-600 text-white px-2 py-1 rounded-full text-xs font-bold z-10">
          🚨 OUT OF STOCK
        </div>
      )}

      {/* Product Image */}
      <div className="flex justify-center mb-4 mt-6">
        {product.image_url ? (
          <img 
            src={`${BACKEND_URL}${product.image_url}`}
            alt={product.product_name}
            className="w-24 h-24 object-contain rounded-lg border-2 border-gray-200"
            style={{ 
              aspectRatio: '1:1', 
              objectFit: 'contain',
              imageRendering: 'crisp-edges'
            }}
            loading="lazy"
          />
        ) : (
          <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg flex items-center justify-center border-2 border-blue-300">
            <svg className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a8.949 8.949 0 008.354-5.646z" />
            </svg>
          </div>
        )}
      </div>
      
      {/* Product Title */}
      <h3 className="text-lg font-bold text-gray-900 text-center mb-3 leading-tight">
        {product.product_name}
      </h3>
      
      {/* Product Details */}
      <div className="space-y-2 text-sm">
        {/* Barcode */}
        {product.barcode && (
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 font-medium">Barcode:</span>
            <span className="font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">
              {product.barcode}
            </span>
          </div>
        )}
        
        {/* Stock Available */}
        <div className="flex justify-between items-center py-1">
          <span className="text-gray-600 font-medium">Stock Available:</span>
          <span className={`font-bold px-2 py-1 rounded ${
            isOutOfStock ? 'text-red-700 bg-red-100' :
            isLowStock ? 'text-yellow-700 bg-yellow-100' : 
            'text-green-700 bg-green-100'
          }`}>
            {product.quantity}
            {isOutOfStock && <span className="ml-1 text-xs">🚨</span>}
          </span>
        </div>
        
        {/* Supplier */}
        <div className="flex justify-between items-center py-1">
          <span className="text-gray-600 font-medium">Supplier:</span>
          <span className="text-gray-900 text-right flex-1 ml-2">
            {product.supplier}
          </span>
        </div>
        
        {/* Expiry Date */}
        <div className="flex justify-between items-center py-1">
          <span className="text-gray-600 font-medium">Expiry Date:</span>
          <span className={`px-2 py-1 rounded text-sm font-medium ${
            isExpired ? 'text-red-700 bg-red-100' :
            isExpiringSoon ? 'text-yellow-700 bg-yellow-100' :
            'text-green-700 bg-green-100'
          }`}>
            {formatDate(product.expiry_date)}
          </span>
        </div>
        
        {/* Selling Price */}
        <div className="flex justify-between items-center py-1">
          <span className="text-gray-600 font-medium">Selling Price:</span>
          <span className="text-xl font-bold text-green-600">
            {formatCurrency(product.selling_price)}
          </span>
        </div>
        
        {/* Purchase Price & Currency */}
        {product.purchase_price && (
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 font-medium">Purchase Price:</span>
            <span className="text-lg font-semibold text-blue-600">
              {product.purchase_price?.toFixed(2) || '0.00'} {product.purchase_currency || 'YER'}
            </span>
          </div>
        )}
        
        {/* Stock Value with Currency */}
        {showStockValue && stockValue && (
          <div className="flex justify-between items-center py-1 bg-blue-50 px-2 rounded">
            <span className="text-blue-700 font-medium">Stock Value:</span>
            <span className="text-lg font-bold text-blue-700">
              {stockValue.toFixed(2)} {product.purchase_currency || 'YER'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Supplier Dashboard Component
const EnhancedSupplierDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [sections, setSections] = useState([]);
  const [selectedSection, setSelectedSection] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchSupplierDashboard = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedSection) params.append('section', selectedSection);
      
      const response = await axios.get(`${API}/suppliers/dashboard?${params}`, {
        headers: getAuthHeaders(token)
      });
      
      setDashboardData(response.data);
    } catch (error) {
      setError('Error fetching supplier dashboard');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">📊 Enhanced Supplier Dashboard</h2>

        {/* Section Filter */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Section</label>
          <div className="flex gap-4">
            <select
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
              className="flex-1 p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Sections</option>
              {sections.map(section => (
                <option key={section} value={section}>{section}</option>
              ))}
            </select>
            <button
              onClick={fetchSupplierDashboard}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              🔍 Apply Filter
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8">Loading dashboard...</div>
        ) : dashboardData ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* High Stock Value Suppliers */}
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="text-lg font-bold text-green-800 mb-4">💰 High Stock Value Suppliers</h3>
              <div className="space-y-3">
                {dashboardData.high_stock_value_suppliers?.map((supplier, index) => (
                  <div key={supplier.supplier} className="bg-white p-3 rounded-lg shadow-sm">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">#{index + 1} {supplier.supplier}</span>
                      <span className="font-bold text-green-600">{supplier.total_stock_value_formatted}</span>
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {supplier.total_products} products • {supplier.total_quantity} total quantity
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Zero Stock Suppliers */}
            <div className="bg-red-50 p-4 rounded-lg">
              <h3 className="text-lg font-bold text-red-800 mb-4">🚨 Zero Stock Suppliers</h3>
              <div className="space-y-3">
                {dashboardData.zero_stock_suppliers?.map(supplier => (
                  <div key={supplier.supplier} className="bg-white p-3 rounded-lg shadow-sm">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{supplier.supplier}</span>
                      <span className="font-bold text-red-600">{supplier.zero_stock_count} items</span>
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      Out of stock: {supplier.zero_stock_items.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};