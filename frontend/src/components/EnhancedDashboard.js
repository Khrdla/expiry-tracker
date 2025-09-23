import React, { useState, useEffect } from 'react';
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
import { Camera } from 'lucide-react';
import CleanCameraScanner from './CleanCameraScanner';
import ProductDetailsModal from './ProductDetailsModal';
import Dashboard3DCharts from './Dashboard3DCharts';
import AdvancedBarcodeFeatures from './AdvancedBarcodeFeatures';
import EnhancedVisualCharts from './EnhancedVisualCharts';

const EnhancedDashboard = () => {
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

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    loadUserData();
    loadDashboardData();
    loadFilterOptions();
  }, [selectedDepartment, selectedSection, selectedSupplier]);

  const loadUserData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Failed to load user data:', error);
    }
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
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
        setKpis(data.kpis || {});
        
        const departments = Object.entries(data.kpis || {}).map(([key, value]) => ({
          name: key,
          value: value.total_items || 0,
          expired: value.expired_items || 0,
          stock_value: value.stock_value || 0
        }));
        setChartData(departments);
        setError('');
      } else {
        throw new Error('Failed to load dashboard data');
      }
    } catch (error) {
      console.error('Dashboard error:', error);
      setError('Failed to load dashboard data');
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

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount || 0);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'in_stock': return 'text-green-600 bg-green-100';
      case 'low_stock': return 'text-yellow-600 bg-yellow-100';
      case 'out_of_stock': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

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
              <h1 className="text-3xl font-bold text-gray-900">
                Dashboard
              </h1>
              <p className="text-gray-600 mt-1">
                Welcome back, {user?.username || 'User'}
              </p>
            </div>
            
            {/* Mobile-optimized action buttons */}
            <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
              <div className="flex gap-2">
                <button
                  onClick={() => setShowScanner(true)}
                  className="flex-1 sm:flex-initial bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl flex items-center justify-center gap-2 font-medium"
                >
                  <Camera size={18} />
                  📱 Scan
                </button>
                
                <button
                  onClick={() => setShowAdvancedBarcodeFeatures(true)}
                  className="flex-1 sm:flex-initial bg-gradient-to-r from-green-500 to-teal-600 text-white px-4 py-2 rounded-lg hover:from-green-600 hover:to-teal-700 transition-all duration-200 shadow-lg hover:shadow-xl flex items-center justify-center gap-2 font-medium"
                >
                  🚀 Pro
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

        {/* Filters - Mobile-friendly grid layout */}
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
                {filterOptions.departments?.map(dept => (
                  <option key={dept.value || dept} value={dept.value || dept}>
                    {dept.label || dept}
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
                {filterOptions.sections?.map(section => (
                  <option key={section} value={section}>{section}</option>
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
                {filterOptions.suppliers?.map(supplier => (
                  <option key={supplier} value={supplier}>{supplier}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {Object.entries(kpis).map(([key, value]) => (
            <div key={key} className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{key}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {value.total_items?.toLocaleString() || 0}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Stock Value</p>
                  <p className="text-sm font-semibold text-green-600">
                    {typeof value.stock_value === 'number' 
                      ? formatCurrency(value.stock_value) 
                      : value.stock_value || '$0'}
                  </p>
                </div>
              </div>
              
              <div className="mt-4 flex justify-between text-sm">
                <span className="text-red-600">
                  Expired: {value.expired_items || 0}
                </span>
                <span className="text-yellow-600">
                  Low Stock: {value.low_stock_items || 0}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Department Distribution Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Items by Department</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
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
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="stock_value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Enhanced Visual Charts Integration */}
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

        {/* Top Suppliers */}
        {kpis.top_suppliers && kpis.top_suppliers.length > 0 && (
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
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {supplier.supplier}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {supplier.total_items}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {supplier.total_stock_value}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Recent Alerts */}
        {kpis.recent_alerts && kpis.recent_alerts.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Alerts</h3>
            <div className="space-y-3">
              {kpis.recent_alerts.map((alert, index) => (
                <div key={index} className={`p-3 rounded-lg border ${getStatusColor(alert.type)}`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{alert.message}</p>
                      <p className="text-sm opacity-75">{alert.product_name}</p>
                    </div>
                    <span className="text-xs opacity-75">
                      {new Date(alert.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Floating Action Button - Mobile optimized */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          onClick={() => setShowScanner(true)}
          className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-full shadow-xl hover:shadow-2xl transform hover:scale-110 transition-all duration-300 flex items-center justify-center"
        >
          <Camera size={24} />
        </button>
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