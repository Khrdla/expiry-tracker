import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  PieChart, 
  Pie, 
  Cell,
  ResponsiveContainer,
  LineChart,
  Line
} from 'recharts';
import { Camera, AlertTriangle, TrendingUp, Grid3X3 } from 'lucide-react';
import EnhancedBarcodeScanner from './EnhancedBarcodeScanner';
import ProductDetailsModal from './ProductDetailsModal';
import Dashboard3DCharts from './Dashboard3DCharts';
import AdvancedBarcodeFeatures from './AdvancedBarcodeFeatures';
import EnhancedVisualCharts from './EnhancedVisualCharts';

/**
 * Enhanced Dashboard with Improved Data Handling
 * 
 * Fixes:
 * - Proper handling of null/undefined data
 * - Fallback values to prevent displaying indices
 * - Enhanced error boundaries and logging
 * - Stable state management
 */
const EnhancedDashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [kpis, setKpis] = useState({});
  const [chartData, setChartData] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedDepartment, setSelectedDepartment] = useState('all');
  const [selectedSection, setSelectedSection] = useState('all');
  const [selectedSupplier, setSelectedSupplier] = useState('all');
  const [showScanner, setShowScanner] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showProductDetails, setShowProductDetails] = useState(false);
  const [show3DCharts, setShow3DCharts] = useState(false);
  const [showAdvancedBarcodeFeatures, setShowAdvancedBarcodeFeatures] = useState(false);
  const [showEnhancedVisualCharts, setShowEnhancedVisualCharts] = useState(false);
  const [filterOptions, setFilterOptions] = useState({
    departments: [],
    sections: [],
    suppliers: []
  });

  // Add debug logging for data issues
  const [debugInfo, setDebugInfo] = useState({
    lastDataLoad: null,
    apiCallCount: 0,
    errorCount: 0
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Enhanced logging system
  const logDashboardActivity = (action, details = {}) => {
    const timestamp = new Date().toISOString();
    console.log(`[Dashboard] ${timestamp} - ${action}:`, details);
    
    setDebugInfo(prev => ({
      ...prev,
      lastActivity: timestamp,
      apiCallCount: action.includes('API') ? prev.apiCallCount + 1 : prev.apiCallCount,
      errorCount: action.includes('ERROR') ? prev.errorCount + 1 : prev.errorCount
    }));
  };

  useEffect(() => {
    loadUserData();
    loadDashboardData();
    loadFilterOptions();
  }, [selectedDepartment, selectedSection, selectedSupplier]);

  // Enhanced user data loading with error handling
  const loadUserData = async () => {
    try {
      logDashboardActivity('API_CALL_USER_DATA');
      const token = localStorage.getItem('token');
      
      if (!token) {
        logDashboardActivity('ERROR_NO_TOKEN');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const userData = await response.json();
        logDashboardActivity('USER_DATA_SUCCESS', { username: userData?.username });
        setUser(userData);
      } else {
        logDashboardActivity('USER_DATA_ERROR', { status: response.status });
      }
    } catch (error) {
      logDashboardActivity('USER_DATA_EXCEPTION', { error: error.message });
      console.error('Failed to load user data:', error);
    }
  };

  // Enhanced dashboard data loading with comprehensive error handling
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      logDashboardActivity('API_CALL_DASHBOARD_DATA', {
        department: selectedDepartment,
        section: selectedSection,
        supplier: selectedSupplier
      });
      
      const token = localStorage.getItem('token');
      
      if (!token) {
        logDashboardActivity('ERROR_NO_TOKEN_DASHBOARD');
        setError('Authentication token not found');
        return;
      }

      const queryParams = new URLSearchParams({
        ...(selectedDepartment !== 'all' && { department: selectedDepartment }),
        ...(selectedSection !== 'all' && { section: selectedSection }),
        ...(selectedSupplier !== 'all' && { supplier: selectedSupplier })
      });
      
      const url = `${BACKEND_URL}/api/dashboard${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        logDashboardActivity('DASHBOARD_DATA_SUCCESS', {
          kpisCount: Object.keys(data.kpis || {}).length,
          dataStructure: Object.keys(data)
        });
        
        // Enhanced data processing with null checks
        const processedKpis = processKpisData(data.kpis || {});
        setKpis(processedKpis);
        
        // Enhanced chart data processing
        const processedChartData = processChartData(processedKpis);
        setChartData(processedChartData);
        
        setError('');
        setDebugInfo(prev => ({
          ...prev,
          lastDataLoad: new Date().toISOString()
        }));
      } else {
        const errorText = await response.text();
        logDashboardActivity('DASHBOARD_DATA_ERROR', {
          status: response.status,
          error: errorText
        });
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
    } catch (error) {
      logDashboardActivity('DASHBOARD_DATA_EXCEPTION', { error: error.message });
      console.error('Dashboard error:', error);
      setError(`Failed to load dashboard data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Enhanced KPI data processing with proper department name handling
  const processKpisData = (rawKpis) => {
    console.log('🔍 Raw KPIs received:', rawKpis);
    
    const processedKpis = {};
    
    // Handle different possible KPI data structures
    if (Array.isArray(rawKpis)) {
      // If KPIs come as an array, extract department names from objects
      rawKpis.forEach((item, index) => {
        const departmentName = item?.department || item?.name || `Department_${index}`;
        const processedValue = {
          total_items: safeNumber(item?.total_items, 0),
          expired_items: safeNumber(item?.expired_items, 0),
          low_stock_items: safeNumber(item?.low_stock_items, 0),
          stock_value: safeNumber(item?.stock_value, 0),
          department: departmentName
        };
        processedKpis[departmentName] = processedValue;
      });
    } else if (typeof rawKpis === 'object' && rawKpis !== null) {
      // If KPIs come as an object, process each entry
      Object.entries(rawKpis).forEach(([key, value]) => {
        // Get department name from value object or use key
        const departmentName = value?.department || key;
        
        const processedValue = {
          total_items: safeNumber(value?.total_items, 0),
          expired_items: safeNumber(value?.expired_items, 0),
          low_stock_items: safeNumber(value?.low_stock_items, 0),
          stock_value: safeNumber(value?.stock_value, 0),
          department: departmentName
        };
        
        processedKpis[departmentName] = processedValue;
      });
    }
    
    console.log('✅ Processed KPIs:', processedKpis);
    
    logDashboardActivity('KPIS_PROCESSED', {
      originalKeys: Array.isArray(rawKpis) ? rawKpis.map((item, i) => i) : Object.keys(rawKpis),
      processedKeys: Object.keys(processedKpis),
      processedData: processedKpis
    });
    
    return processedKpis;
  };

  // Enhanced chart data processing with debug logging
  const processChartData = (kpis) => {
    console.log('📊 Processing Chart Data:', {
      rawKpis: kpis,
      kpisKeys: Object.keys(kpis),
      kpisEntries: Object.entries(kpis)
    });

    const chartData = Object.entries(kpis).map(([key, value]) => ({
      name: safeName(key),
      value: safeNumber(value?.total_items, 0),
      expired: safeNumber(value?.expired_items, 0),
      stock_value: safeNumber(value?.stock_value, 0)
    }));
    
    console.log('📈 Chart Data Result:', {
      chartData,
      itemCount: chartData.length,
      hasValidData: chartData.some(item => item.value > 0 || item.stock_value > 0)
    });
    
    logDashboardActivity('CHART_DATA_PROCESSED', {
      itemCount: chartData.length,
      names: chartData.map(item => item.name)
    });
    
    return chartData;
  };

  // Enhanced filter options loading
  const loadFilterOptions = async () => {
    try {
      logDashboardActivity('API_CALL_FILTER_OPTIONS');
      const token = localStorage.getItem('token');
      
      if (!token) {
        logDashboardActivity('ERROR_NO_TOKEN_FILTERS');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/filters`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        logDashboardActivity('FILTER_OPTIONS_SUCCESS', {
          departments: data?.departments?.length || 0,
          sections: data?.sections?.length || 0,
          suppliers: data?.suppliers?.length || 0
        });
        
        // Process filter options with safety checks
        const processedOptions = {
          departments: processFilterArray(data?.departments, 'Department'),
          sections: processFilterArray(data?.sections, 'Section'),
          suppliers: processFilterArray(data?.suppliers, 'Supplier')
        };
        
        // Debug logging to understand filter data
        console.log('🏢 Dashboard Filter Options Debug:', {
          rawData: {
            departments: data?.departments,
            sections: data?.sections,
            suppliers: data?.suppliers
          },
          processedData: processedOptions
        });
        
        setFilterOptions(processedOptions);
      } else {
        logDashboardActivity('FILTER_OPTIONS_ERROR', { status: response.status });
      }
    } catch (error) {
      logDashboardActivity('FILTER_OPTIONS_EXCEPTION', { error: error.message });
      console.error('Failed to load filter options:', error);
    }
  };

  // Utility functions for data safety
  const safeNumber = (value, fallback = 0) => {
    const num = Number(value);
    return isNaN(num) ? fallback : num;
  };

  const safeName = (value) => {
    // Handle string values (should be most common)
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
    
    // Handle objects with different name properties
    if (typeof value === 'object' && value !== null) {
      if (value.label) return value.label;
      if (value.name) return value.name;
      if (value.value) return value.value;
    }
    
    // Handle numeric values that might represent department codes
    if (typeof value === 'number') {
      // Don't create fallback names for numbers, return as string
      return value.toString();
    }
    
    return value || 'Unknown';
  };

  const processFilterArray = (array, prefix) => {
    if (!Array.isArray(array)) return [];
    
    return array.map((item, index) => {
      // Handle string values
      if (typeof item === 'string' && item.trim()) {
        return item.trim();
      }
      
      // Handle object with 'label' property (backend format: {value: "01-FMG", label: "01-FMG"})
      if (typeof item === 'object' && item?.label) {
        return item.label;
      }
      
      // Handle object with 'name' property
      if (typeof item === 'object' && item?.name) {
        return item.name;
      }
      
      // Handle object with 'value' property
      if (typeof item === 'object' && item?.value) {
        return item.value;
      }
      
      // Log when fallback is used to debug
      console.warn(`Dashboard filter fallback used for ${prefix}:`, item);
      return `${prefix}_${index + 1}`;
    }).filter(Boolean);
  };

  // Enhanced currency formatting
  const formatCurrency = (amount, currency = 'USD') => {
    const safeAmount = safeNumber(amount, 0);
    
    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
      }).format(safeAmount);
    } catch (error) {
      return `${safeAmount} ${currency}`;
    }
  };

  // Enhanced status color function
  const getStatusColor = (status) => {
    const statusMap = {
      'in_stock': 'text-green-600 bg-green-100',
      'low_stock': 'text-yellow-600 bg-yellow-100',
      'out_of_stock': 'text-red-600 bg-red-100'
    };
    return statusMap[status] || 'text-gray-600 bg-gray-100';
  };

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
          {debugInfo.apiCallCount > 0 && (
            <p className="text-sm text-gray-400 mt-2">API calls: {debugInfo.apiCallCount}</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Enhanced Header with Debug Info */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Enhanced Dashboard
              </h1>
              <p className="text-gray-600 mt-1">
                Welcome back, {user?.username || 'User'}
              </p>
              {process.env.NODE_ENV === 'development' && debugInfo.lastDataLoad && (
                <p className="text-xs text-gray-400 mt-1">
                  Last updated: {new Date(debugInfo.lastDataLoad).toLocaleTimeString()}
                </p>
              )}
            </div>
            
            {/* Enhanced Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/grid')}
                  className="flex-1 sm:flex-initial bg-gradient-to-r from-indigo-500 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-indigo-600 hover:to-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl flex items-center justify-center gap-2 font-medium"
                >
                  <Grid3X3 size={18} />
                  📊 Grid View
                </button>
                
                <button
                  onClick={() => setShowScanner(true)}
                  className="flex-1 sm:flex-initial bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl flex items-center justify-center gap-2 font-medium"
                >
                  <Camera size={18} />
                  📱 Multi-Scan
                </button>
                
                <button
                  onClick={() => setShowAdvancedBarcodeFeatures(true)}
                  className="flex-1 sm:flex-initial bg-gradient-to-r from-green-500 to-teal-600 text-white px-4 py-2 rounded-lg hover:from-green-600 hover:to-teal-700 transition-all duration-200 shadow-lg hover:shadow-xl flex items-center justify-center gap-2 font-medium"
                >
                  🚀 Advanced
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
              <p className="font-medium">Dashboard Error</p>
              <p className="text-sm">{error}</p>
              {debugInfo.errorCount > 0 && (
                <p className="text-xs mt-1">Total errors: {debugInfo.errorCount}</p>
              )}
            </div>
          </div>
        )}

        {/* Enhanced Filters */}
        <div className="mb-6 bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-3">Filters</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
              <select
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Departments</option>
                {filterOptions.departments?.map((dept, index) => (
                  <option key={`dept-${index}`} value={dept}>
                    {dept || `Department ${index + 1}`}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Section</label>
              <select
                value={selectedSection}
                onChange={(e) => setSelectedSection(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Sections</option>
                {filterOptions.sections?.map((section, index) => (
                  <option key={`section-${index}`} value={section}>
                    {section || `Section ${index + 1}`}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Supplier</label>
              <select
                value={selectedSupplier}
                onChange={(e) => setSelectedSupplier(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Suppliers</option>
                {filterOptions.suppliers?.map((supplier, index) => (
                  <option key={`supplier-${index}`} value={supplier}>
                    {supplier || `Supplier ${index + 1}`}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Enhanced KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {Object.entries(kpis).length > 0 ? (
            Object.entries(kpis).map(([key, value]) => (
              <div key={key} className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{safeName(key)}</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {safeNumber(value?.total_items, 0).toLocaleString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Stock Value</p>
                    <p className="text-sm font-semibold text-green-600">
                      {typeof value?.stock_value === 'number' 
                        ? formatCurrency(value.stock_value) 
                        : (value?.stock_value || '$0')}
                    </p>
                  </div>
                </div>
                
                <div className="mt-4 flex justify-between text-sm">
                  <span className="text-red-600">
                    Expired: {safeNumber(value?.expired_items, 0)}
                  </span>
                  <span className="text-yellow-600">
                    Low Stock: {safeNumber(value?.low_stock_items, 0)}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full bg-white rounded-lg shadow p-8 text-center">
              <TrendingUp className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500 text-lg">No KPI data available</p>
              <p className="text-gray-400 text-sm">Check your filters or try refreshing the page</p>
            </div>
          )}
        </div>

        {/* Enhanced Charts Section */}
        {chartData.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Department Distribution Chart */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Items by Department</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value, name) => [value.toLocaleString(), name]} />
                  <Legend />
                  <Bar dataKey="value" fill="#8884d8" name="Total Items" />
                  <Bar dataKey="expired" fill="#ff7c7c" name="Expired Items" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Stock Value Distribution */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Stock Value Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${safeName(name)}: ${safeNumber(value, 0)}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="stock_value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [value.toLocaleString(), 'Stock Value']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Advanced Analytics Section */}
        <div className="mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-4">
              <h3 className="text-lg font-semibold">Advanced Analytics</h3>
              <div className="flex gap-2 w-full sm:w-auto">
                <button
                  onClick={() => setShowEnhancedVisualCharts(true)}
                  className="flex-1 sm:flex-initial bg-gradient-to-r from-purple-500 to-pink-600 text-white px-4 py-2 rounded-lg hover:from-purple-600 hover:to-pink-700 transition-all duration-200 shadow-lg hover:shadow-xl font-medium"
                >
                  📊 Visual Charts
                </button>
                
                <button
                  onClick={() => setShow3DCharts(true)}
                  className="flex-1 sm:flex-initial bg-gradient-to-r from-indigo-500 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-indigo-600 hover:to-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl font-medium"
                >
                  🎯 3D View
                </button>
              </div>
            </div>
            
            <p className="text-gray-600">
              Access advanced analytics, 3D visualizations, and comprehensive department performance metrics.
            </p>
          </div>
        </div>

        {/* Enhanced Top Suppliers */}
        {kpis.top_suppliers && Array.isArray(kpis.top_suppliers) && kpis.top_suppliers.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">Top Suppliers</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Supplier
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Items
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stock Value
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {kpis.top_suppliers.map((supplier, index) => (
                    <tr key={`supplier-row-${index}`} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {safeName(supplier?.supplier)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {safeNumber(supplier?.total_items, 0).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {supplier?.total_stock_value || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Enhanced Recent Alerts */}
        {kpis.recent_alerts && Array.isArray(kpis.recent_alerts) && kpis.recent_alerts.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Alerts</h3>
            <div className="space-y-3">
              {kpis.recent_alerts.map((alert, index) => (
                <div key={`alert-${index}`} className={`p-3 rounded-lg border ${getStatusColor(alert.type)}`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{alert.message || 'Alert message unavailable'}</p>
                      <p className="text-sm opacity-75">{safeName(alert.product_name)}</p>
                    </div>
                    <span className="text-xs opacity-75">
                      {alert.created_at ? new Date(alert.created_at).toLocaleDateString() : 'Unknown date'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Enhanced Floating Action Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          onClick={() => setShowScanner(true)}
          className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-full shadow-xl hover:shadow-2xl transform hover:scale-110 transition-all duration-300 flex items-center justify-center"
          title="Multi-Format Barcode Scanner"
        >
          <Camera size={24} />
        </button>
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

      {/* 3D Charts Modal */}
      <Dashboard3DCharts
        isOpen={show3DCharts}
        onClose={() => setShow3DCharts(false)}
        kpis={kpis}
        chartData={chartData}
      />

      {/* Advanced Barcode Features Modal */}
      <AdvancedBarcodeFeatures
        isOpen={showAdvancedBarcodeFeatures}
        onClose={() => setShowAdvancedBarcodeFeatures(false)}
      />

      {/* Enhanced Visual Charts Modal */}
      <EnhancedVisualCharts
        isOpen={showEnhancedVisualCharts}
        onClose={() => setShowEnhancedVisualCharts(false)}
        kpis={kpis}
        filterOptions={filterOptions}
      />
    </div>
  );
};

export default EnhancedDashboard;