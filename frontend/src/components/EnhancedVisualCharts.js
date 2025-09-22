import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Area, AreaChart,
  RadialBarChart, RadialBar, Treemap, Scatter, ScatterChart
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Package, AlertTriangle, 
  DollarSign, Users, Building2, Target, Activity, Zap 
} from 'lucide-react';

const EnhancedVisualCharts = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    departmentBreakdown: [],
    stockLevels: {},
    supplierPerformance: [],
    wasteData: []
  });
  const [activeTab, setActiveTab] = useState('departments');

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch multiple analytics endpoints
      const [deptResponse, stockResponse, supplierResponse, wasteResponse] = await Promise.all([
        fetch(`${BACKEND_URL}/api/analytics/department-breakdown`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${BACKEND_URL}/api/analytics/stock-levels`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${BACKEND_URL}/api/analytics/supplier-performance`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${BACKEND_URL}/api/waste`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      const departmentBreakdown = await deptResponse.json();
      const stockLevels = await stockResponse.json();
      const supplierPerformance = await supplierResponse.json();
      const wasteData = await wasteResponse.json();

      setDashboardData({
        departmentBreakdown,
        stockLevels,
        supplierPerformance,
        wasteData: wasteData.waste_entries || []
      });
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Color schemes for different chart types
  const departmentColors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16'];
  const statusColors = {
    'in_stock': '#10B981',
    'low_stock': '#F59E0B', 
    'out_of_stock': '#EF4444',
    'near_expiry': '#F97316',
    'expired': '#DC2626'
  };

  const formatCurrency = (value, currency = 'YER') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency === 'YER' ? 'USD' : currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value / (currency === 'YER' ? 516 : 1)); // Approximate YER to USD conversion
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  // Department Performance Chart
  const DepartmentChart = () => (
    <div className="bg-white p-6 rounded-xl shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-800">Department Performance</h3>
          <p className="text-gray-600">Stock value and product count by department</p>
        </div>
        <Building2 className="text-blue-500" size={24} />
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={dashboardData.departmentBreakdown}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="_id" tick={{ fontSize: 12 }} />
          <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
          <Tooltip 
            formatter={(value, name) => [
              name.includes('value') ? formatCurrency(value) : formatNumber(value),
              name
            ]}
            labelStyle={{ color: '#374151' }}
          />
          <Legend />
          <Bar 
            yAxisId="left"
            dataKey="total_products" 
            fill="#3B82F6" 
            name="Total Products"
            radius={[4, 4, 0, 0]}
          />
          <Bar 
            yAxisId="right"
            dataKey="total_value_yer" 
            fill="#10B981" 
            name="Stock Value (YER)"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      
      {/* Department Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        {dashboardData.departmentBreakdown.slice(0, 4).map((dept, index) => (
          <div key={dept._id} className="bg-gradient-to-r from-blue-50 to-green-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-gray-600">{dept._id}</div>
            <div className="text-lg font-bold text-gray-800">{formatNumber(dept.total_products)}</div>
            <div className="text-xs text-gray-500">{formatCurrency(dept.total_value_yer)}</div>
          </div>
        ))}
      </div>
    </div>
  );

  // Stock Status Distribution
  const StockStatusChart = () => {
    const statusData = dashboardData.stockLevels.status_breakdown || [];
    
    return (
      <div className="bg-white p-6 rounded-xl shadow-lg">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-800">Stock Status Distribution</h3>
            <p className="text-gray-600">Current inventory status breakdown</p>
          </div>
          <Package className="text-green-500" size={24} />
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pie Chart */}
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={120}
                paddingAngle={5}
                dataKey="count"
              >
                {statusData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={statusColors[entry._id] || '#6B7280'} 
                  />
                ))}
              </Pie>
              <Tooltip formatter={(value, name) => [formatNumber(value), 'Products']} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          
          {/* Status Cards */}
          <div className="space-y-4">
            {statusData.map((status, index) => (
              <div key={status._id} className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow">
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: statusColors[status._id] || '#6B7280' }}
                  ></div>
                  <div>
                    <div className="font-medium capitalize">{status._id.replace('_', ' ')}</div>
                    <div className="text-sm text-gray-500">{formatCurrency(status.total_value)}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold">{formatNumber(status.count)}</div>
                  <div className="text-xs text-gray-500">products</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Stock Range Distribution */}
        {dashboardData.stockLevels.stock_ranges && (
          <div className="mt-8">
            <h4 className="text-lg font-semibold mb-4">Stock Quantity Ranges</h4>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={dashboardData.stockLevels.stock_ranges}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="_id" />
                <YAxis />
                <Tooltip formatter={(value) => [formatNumber(value), 'Products']} />
                <Area 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#8884d8" 
                  fill="#8884d8" 
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    );
  };

  // Top Suppliers Performance
  const SupplierChart = () => (
    <div className="bg-white p-6 rounded-xl shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-800">Top Supplier Performance</h3>
          <p className="text-gray-600">Leading suppliers by stock value and product count</p>
        </div>
        <Users className="text-purple-500" size={24} />
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <BarChart 
          data={dashboardData.supplierPerformance.slice(0, 10)}
          layout="horizontal"
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" tick={{ fontSize: 12 }} />
          <YAxis 
            dataKey="_id" 
            type="category" 
            width={150}
            tick={{ fontSize: 10 }}
          />
          <Tooltip 
            formatter={(value, name) => [
              name.includes('value') ? formatCurrency(value) : formatNumber(value),
              name
            ]}
          />
          <Legend />
          <Bar 
            dataKey="total_stock_value" 
            fill="#8B5CF6" 
            name="Stock Value (YER)"
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      
      {/* Supplier Performance Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
        {dashboardData.supplierPerformance.slice(0, 6).map((supplier, index) => (
          <div key={supplier._id} className="bg-gradient-to-r from-purple-50 to-blue-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-gray-600 truncate" title={supplier._id}>
              {supplier._id}
            </div>
            <div className="text-lg font-bold text-gray-800">{formatNumber(supplier.total_products)}</div>
            <div className="text-xs text-gray-500">{formatCurrency(supplier.total_stock_value)}</div>
            <div className="text-xs text-red-500 mt-1">
              {supplier.out_of_stock_count} out of stock
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Waste Analysis Chart
  const WasteChart = () => {
    // Process waste data for visualization
    const wasteByDepartment = dashboardData.wasteData.reduce((acc, item) => {
      const dept = item.department || 'Unknown';
      if (!acc[dept]) {
        acc[dept] = { department: dept, total_waste: 0, total_value: 0, count: 0 };
      }
      acc[dept].total_waste += item.quantity || 0;
      acc[dept].total_value += (item.quantity || 0) * (item.purchase_price || 0);
      acc[dept].count += 1;
      return acc;
    }, {});
    
    const wasteChartData = Object.values(wasteByDepartment);
    
    return (
      <div className="bg-white p-6 rounded-xl shadow-lg">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-800">Waste Analysis by Department</h3>
            <p className="text-gray-600">Waste quantity and value breakdown</p>
          </div>
          <AlertTriangle className="text-red-500" size={24} />
        </div>
        
        {wasteChartData.length > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={wasteChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="department" />
                <YAxis />
                <Tooltip 
                  formatter={(value, name) => [
                    name.includes('value') ? formatCurrency(value) : formatNumber(value),
                    name
                  ]}
                />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="total_waste" 
                  stackId="1"
                  stroke="#EF4444" 
                  fill="#EF4444" 
                  fillOpacity={0.6}
                  name="Waste Quantity"
                />
                <Area 
                  type="monotone" 
                  dataKey="total_value" 
                  stackId="2"
                  stroke="#F59E0B" 
                  fill="#F59E0B" 
                  fillOpacity={0.6}
                  name="Waste Value (YER)"
                />
              </AreaChart>
            </ResponsiveContainer>
            
            {/* Waste Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              {wasteChartData.slice(0, 4).map((dept, index) => (
                <div key={dept.department} className="bg-gradient-to-r from-red-50 to-orange-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-gray-600">{dept.department}</div>
                  <div className="text-lg font-bold text-gray-800">{formatNumber(dept.total_waste)}</div>
                  <div className="text-xs text-gray-500">{formatCurrency(dept.total_value)}</div>
                  <div className="text-xs text-red-500">{dept.count} items</div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <AlertTriangle size={48} className="mx-auto mb-4 text-gray-300" />
            <p>No waste data available</p>
            <p className="text-sm">Waste entries will appear here once recorded</p>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white p-6 rounded-xl shadow-lg animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Navigation */}
      <div className="bg-white p-6 rounded-xl shadow-lg">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center space-x-2">
              <Activity className="text-blue-500" />
              <span>Advanced Analytics Dashboard</span>
            </h2>
            <p className="text-gray-600">Comprehensive inventory insights and performance metrics</p>
          </div>
          <button
            onClick={fetchDashboardData}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center space-x-2"
          >
            <Zap size={16} />
            <span>Refresh Data</span>
          </button>
        </div>
        
        {/* Tab Navigation */}
        <div className="flex space-x-2 border-b">
          {[
            { id: 'departments', label: 'Departments', icon: Building2 },
            { id: 'stock', label: 'Stock Levels', icon: Package },
            { id: 'suppliers', label: 'Suppliers', icon: Users },
            { id: 'waste', label: 'Waste Analysis', icon: AlertTriangle }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-t-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <tab.icon size={16} />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Chart Content */}
      {activeTab === 'departments' && <DepartmentChart />}
      {activeTab === 'stock' && <StockStatusChart />}
      {activeTab === 'suppliers' && <SupplierChart />}
      {activeTab === 'waste' && <WasteChart />}
    </div>
  );
};

export default EnhancedVisualCharts;