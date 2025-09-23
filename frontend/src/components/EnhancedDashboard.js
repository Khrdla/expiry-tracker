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
import FixedMobileScanner from './FixedMobileScanner';
import ProductDetailsModal from './ProductDetailsModal';
import Dashboard3DCharts from './Dashboard3DCharts';
import EnhancedVisualCharts from './EnhancedVisualCharts';
import AdvancedBarcodeFeatures from './AdvancedBarcodeFeatures';

const EnhancedDashboard = ({ user, onProductClick, onAlertClick }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDepartment, setSelectedDepartment] = useState('all');
  const [selectedSection, setSelectedSection] = useState('all');
  const [showAlerts, setShowAlerts] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [showScanner, setShowScanner] = useState(false);
  const [showProductDetails, setShowProductDetails] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showExportDropdown, setShowExportDropdown] = useState(false);
  const [wasteData, setWasteData] = useState(null);
  const [showAdvancedFeatures, setShowAdvancedFeatures] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const COLORS = {
    'in_stock': '#22c55e',
    'low_stock': '#f59e0b', 
    'out_of_stock': '#ef4444',
    'expired': '#991b1b',
    'near_expiry': '#fb923c'
  };

  const DEPARTMENT_COLORS = {
    '01-FMG': '#22c55e',
    '01-CGD': '#3b82f6',
    '01-OPSS': '#8b5cf6'
  };

  useEffect(() => {
    fetchDashboardData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    setRefreshInterval(interval);
    
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
      
      // Also fetch waste data for 3D charts
      await fetchWasteData(token);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchWasteData = async (token) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/waste/reports?period=weekly`, {
        headers: { 'Authorization': `Bearer ${token || localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setWasteData(data);
      }
    } catch (error) {
      console.error('Error fetching waste data:', error);
    }
  };

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

  // Export functions with proper authentication
  const handleExport = async (type) => {
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('❌ No authentication token found');
      alert('Please log in again to export reports');
      return;
    }

    console.log('🔍 Starting export:', type);
    
    let url = '';
    let isGetRequest = false;
    
    switch (type) {
      case 'inventory':
        url = `${BACKEND_URL}/api/export/excel`;
        // This is a POST request
        break;
      case 'dashboard-excel':
        url = `${BACKEND_URL}/api/export/dashboard/excel`;
        isGetRequest = true;
        break;
      case 'dashboard-pdf':
        url = `${BACKEND_URL}/api/export/dashboard/pdf`;
        isGetRequest = true;
        break;
      case 'expiry-tracker':
        url = `${BACKEND_URL}/api/export/expiry-tracker`;
        // This is a POST request
        break;
      case 'return-forms':
        url = `${BACKEND_URL}/api/export/return-forms`;
        isGetRequest = true;
        break;
      default:
        console.error('❌ Unknown export type:', type);
        return;
    }

    try {
      console.log('📡 Making authenticated request to:', url);
      
      if (isGetRequest) {
        // For GET requests, use fetch with proper Authorization header
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        console.log('📊 Export response status:', response.status);
        
        if (response.ok) {
          // Get the blob data
          const blob = await response.blob();
          console.log('📥 Received blob:', blob.size, 'bytes');
          
          // Determine file name and type
          let fileName = 'export';
          let fileExtension = '.xlsx';
          
          if (type === 'dashboard-excel') {
            fileName = 'dashboard_export';
            fileExtension = '.xlsx';
          } else if (type === 'dashboard-pdf') {
            fileName = 'dashboard_export';
            fileExtension = '.pdf';
          } else if (type === 'return-forms') {
            fileName = 'return_forms_export';
            fileExtension = '.xlsx';
          }
          
          // Create download link
          const downloadUrl = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = `${fileName}_${new Date().toISOString().split('T')[0]}${fileExtension}`;
          
          // Trigger download
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          // Clean up
          window.URL.revokeObjectURL(downloadUrl);
          
          console.log('✅ Export completed successfully');
        } else {
          const errorText = await response.text();
          console.error('❌ Export failed:', response.status, errorText);
          
          if (response.status === 401) {
            alert('❌ Not authenticated. Please log in again.');
          } else if (response.status === 403) {
            alert('❌ Access denied. Admin privileges required.');
          } else {
            alert(`❌ Export failed: ${response.status} ${errorText}`);
          }
        }
      } else {
        // For POST requests, use fetch with proper headers and JSON data
        const exportData = {};
        
        // Add filters if any
        if (selectedDepartment !== 'all') {
          exportData.department = selectedDepartment;
        }
        
        if (selectedSection !== 'all') {
          exportData.section = selectedSection;
        }
        
        console.log('📤 POST export data:', exportData);
        
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(exportData),
        });
        
        console.log('📊 POST Export response status:', response.status);
        
        if (response.ok) {
          // Get the blob data
          const blob = await response.blob();
          console.log('📥 Received POST blob:', blob.size, 'bytes');
          
          // Determine file name
          let fileName = 'inventory_export';
          if (type === 'expiry-tracker') {
            fileName = 'expiry_tracker_export';
          }
          
          // Create download link
          const downloadUrl = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = `${fileName}_${new Date().toISOString().split('T')[0]}.xlsx`;
          
          // Trigger download
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          // Clean up
          window.URL.revokeObjectURL(downloadUrl);
          
          console.log('✅ POST Export completed successfully');
        } else {
          const errorText = await response.text();
          console.error('❌ POST Export failed:', response.status, errorText);
          
          if (response.status === 401) {
            alert('❌ Not authenticated. Please log in again.');
          } else if (response.status === 403) {
            alert('❌ Access denied. Admin privileges required.');
          } else {
            alert(`❌ Export failed: ${response.status} ${errorText}`);
          }
        }
      }
    } catch (error) {
      console.error('❌ Export error:', error);
      alert(`❌ Export failed: ${error.message}`);
    }
    
    setShowExportDropdown(false);
  };

  const getFilteredKPIs = () => {
    if (!dashboardData) return [];
    if (selectedDepartment === 'all') return dashboardData.kpis;
    return dashboardData.kpis.filter(kpi => kpi.department === selectedDepartment);
  };

  const prepareChartData = () => {
    const kpis = getFilteredKPIs();
    return kpis.map(kpi => ({
      department: getDepartmentName(kpi.department),
      'Total Items': kpi.total_items,
      'Out of Stock': kpi.out_of_stock_items,
      'Low Stock': kpi.low_stock_items,
      'Near Expiry': kpi.near_expiry_items,
      'Stock Value': kpi.total_stock_value
    }));
  };

  const prepareExpiryData = () => {
    if (!dashboardData) return [];
    const expiry = dashboardData.expiry_status;
    return Object.entries(expiry).map(([key, value]) => ({
      name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: value,
      color: COLORS[key]
    })).filter(item => item.value > 0); // Only show non-zero values
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-500"></div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="text-center text-red-600 p-8">
        <p>Failed to load dashboard data. Please try again.</p>
        <button onClick={fetchDashboardData} className="mt-4 bg-green-500 text-white px-4 py-2 rounded">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header - Mobile Optimized */}
      <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white p-3 md:p-6 rounded-xl">
        {/* Logo and Title Section */}
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-12 h-12 md:w-16 md:h-16 flex items-center justify-center bg-white bg-opacity-20 rounded-xl flex-shrink-0">
            <img 
              src="/geant_logo.jpeg" 
              alt="Geant Logo" 
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <h1 className="text-lg md:text-2xl lg:text-3xl font-bold">📊 Geant Hypermarket</h1>
            <p className="text-green-100 text-xs md:text-sm">Inventory Management Dashboard</p>
            <p className="text-xs text-green-200">Role: {user?.role?.toUpperCase()} | Auto-refresh: ON</p>
          </div>
        </div>
        
        {/* Controls - Mobile First Layout */}
        <div className="space-y-3">
          {/* Primary Actions Row */}
          <div className="flex space-x-2">
            <button
              onClick={() => setShowScanner(true)}
              className="flex-1 bg-white bg-opacity-20 hover:bg-opacity-30 text-white py-3 rounded-lg transition-all flex items-center justify-center space-x-2 font-medium"
              title="Quick Barcode Scanner"
            >
              <Camera size={18} />
              <span>📱 Scan</span>
            </button>
            
            <button
              onClick={() => setShowAdvancedFeatures(true)}
              className="flex-1 bg-purple-500 bg-opacity-80 hover:bg-opacity-100 text-white py-3 rounded-lg transition-all flex items-center justify-center space-x-2 font-medium"
              title="Advanced Features"
            >
              <span>🚀</span>
              <span>Pro</span>
            </button>
            
            <button
              onClick={fetchDashboardData}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-3 rounded-lg transition-all"
              title="Refresh Data"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
          
          {/* Filters Row */}
          <div className="grid grid-cols-2 gap-2">
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="bg-white text-gray-800 px-3 py-2 rounded-lg font-medium text-sm"
            >
              <option value="all">🏢 All Departments</option>
              {dashboardData.accessible_departments.map(dept => (
                <option key={dept} value={dept}>{getDepartmentName(dept)}</option>
              ))}
            </select>
            
            <select
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
              className="bg-white text-gray-800 px-3 py-2 rounded-lg font-medium text-sm"
            >
              <option value="all">📍 All Sections</option>
              {dashboardData.sections?.map(section => (
                <option key={section} value={section}>{section}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* KPI Cards - Mobile Optimized */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-6">
        {getFilteredKPIs().map((kpi, index) => (
          <div key={index} className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
            <div 
              className="h-2"
              style={{ backgroundColor: DEPARTMENT_COLORS[kpi.department] }}
            ></div>
            
            <div className="p-3 md:p-6">
              <div className="flex items-center justify-between mb-3 md:mb-4">
                <h3 className="font-semibold text-gray-800 text-sm md:text-base">{getDepartmentName(kpi.department)}</h3>
                <div className="text-xl md:text-2xl">📦</div>
              </div>
              
              <div className="space-y-2 md:space-y-3">
                <div 
                  className="flex justify-between items-center cursor-pointer hover:bg-green-50 p-1 md:p-2 rounded transition-colors"
                  onClick={() => onProductClick && onProductClick('total', kpi.department)}
                >
                  <span className="text-xs md:text-sm text-gray-600">✅ Total</span>
                  <span className="font-bold text-green-600 text-sm md:text-base">{kpi.total_items.toLocaleString()}</span>
                </div>
                
                <div 
                  className="flex justify-between items-center cursor-pointer hover:bg-red-50 p-1 md:p-2 rounded transition-colors"
                  onClick={() => onProductClick && onProductClick('out_of_stock', kpi.department)}
                >
                  <span className="text-xs md:text-sm text-gray-600">❌ Out Stock</span>
                  <span className="font-bold text-red-600 text-sm md:text-base">{kpi.out_of_stock_items.toLocaleString()}</span>
                </div>
                
                <div 
                  className="flex justify-between items-center cursor-pointer hover:bg-yellow-50 p-1 md:p-2 rounded transition-colors"
                  onClick={() => onProductClick && onProductClick('low_stock', kpi.department)}
                >
                  <span className="text-xs md:text-sm text-gray-600">⚠️ Low Stock</span>
                  <span className="font-bold text-yellow-600 text-sm md:text-base">{kpi.low_stock_items.toLocaleString()}</span>
                </div>
                
                <div 
                  className="flex justify-between items-center cursor-pointer hover:bg-orange-50 p-1 md:p-2 rounded transition-colors"
                  onClick={() => onProductClick && onProductClick('near_expiry', kpi.department)}
                >
                  <span className="text-xs md:text-sm text-gray-600">⏰ Near Expiry</span>
                  <span className="font-bold text-orange-600 text-sm md:text-base">{kpi.near_expiry_items.toLocaleString()}</span>
                </div>
                
                <div className="pt-2 border-t border-gray-200">
                  <div className="flex justify-between items-center">
                    <span className="text-xs md:text-sm text-gray-600">💰 Value</span>
                    <span className="font-bold text-blue-600 text-xs md:text-sm break-all">{formatCurrency(kpi.total_stock_value)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Section - Mobile Optimized */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 md:gap-6">
        {/* Department Overview Chart */}
        <div className="bg-white rounded-xl shadow-lg p-3 md:p-6">
          <h3 className="text-base md:text-lg lg:text-xl font-semibold text-gray-800 mb-3 md:mb-4 flex items-center">
            📊 <span className="ml-2">Department Overview</span>
          </h3>
          <ResponsiveContainer width="100%" height={window.innerWidth < 768 ? 220 : 280}>
            <BarChart data={prepareChartData()}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey="department" 
                tick={{ fontSize: window.innerWidth < 768 ? 8 : 10 }}
                angle={window.innerWidth < 768 ? -90 : -45}
                textAnchor="end"
                height={window.innerWidth < 768 ? 60 : 80}
                interval={0}
              />
              <YAxis tick={{ fontSize: window.innerWidth < 768 ? 8 : 10 }} />
              <Tooltip 
                formatter={(value, name) => [
                  name === 'Stock Value' ? formatCurrency(value) : value.toLocaleString(),
                  name
                ]}
                contentStyle={{
                  fontSize: window.innerWidth < 768 ? '10px' : '12px',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                  backgroundColor: 'rgba(255, 255, 255, 0.95)'
                }}
              />
              <Legend wrapperStyle={{ fontSize: window.innerWidth < 768 ? '10px' : '12px' }} />
              <Bar dataKey="Total Items" fill="#22c55e" radius={[2, 2, 0, 0]} />
              <Bar dataKey="Out of Stock" fill="#ef4444" radius={[2, 2, 0, 0]} />
              <Bar dataKey="Low Stock" fill="#f59e0b" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Stock Status Pie Chart */}
        <div className="bg-white rounded-xl shadow-lg p-3 md:p-6">
          <h3 className="text-base md:text-lg lg:text-xl font-semibold text-gray-800 mb-3 md:mb-4 flex items-center">
            🥧 <span className="ml-2">Stock Status</span>
          </h3>
          <ResponsiveContainer width="100%" height={window.innerWidth < 768 ? 220 : 280}>
            <PieChart>
              <Pie
                data={prepareExpiryData()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value, percent }) => {
                  const shortName = name.replace('OUT OF STOCK', 'OUT').replace('NEAR EXPIRY', 'EXPIRY');
                  if (window.innerWidth < 768) {
                    return value > 0 ? `${(percent * 100).toFixed(0)}%` : '';
                  }
                  return value > 0 ? `${shortName}: ${value}` : '';
                }}
                outerRadius={window.innerWidth < 768 ? 70 : window.innerWidth < 1024 ? 80 : 100}
                innerRadius={window.innerWidth < 768 ? 20 : window.innerWidth < 1024 ? 25 : 30}
                fill="#8884d8"
                dataKey="value"
                strokeWidth={2}
                stroke="#fff"
              >
                {prepareExpiryData().map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value, name) => [value.toLocaleString(), name]}
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  fontSize: window.innerWidth < 768 ? '10px' : '12px'
                }}
              />
              <Legend 
                verticalAlign="bottom" 
                height={window.innerWidth < 768 ? 30 : 36}
                wrapperStyle={{
                  paddingTop: '15px',
                  fontSize: window.innerWidth < 768 ? '9px' : '11px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Enhanced 3D Charts Section */}
      <Dashboard3DCharts dashboardData={dashboardData} wasteData={wasteData} />

      {/* Enhanced Visual Analytics Charts */}
      <EnhancedVisualCharts />

      {/* Top Suppliers Section */}
      <div className="bg-white rounded-xl shadow-lg p-4 md:p-6">
        <h3 className="text-lg md:text-xl font-semibold text-gray-800 mb-4">Top Suppliers</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {dashboardData.top_suppliers.map((supplier, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-3 md:p-4 hover:bg-gray-50 cursor-pointer transition-colors">
              <div className="flex items-center mb-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-2 flex-shrink-0"></div>
                <h4 className="font-medium text-gray-800 text-xs md:text-sm leading-tight break-words">{supplier.supplier_name}</h4>
              </div>
              
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600">Items:</span>
                  <span className="font-medium">{supplier.total_items}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Out of Stock:</span>
                  <span className="font-medium text-red-600">{supplier.out_of_stock_items}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Value:</span>
                  <span className="font-medium text-green-600 text-xs break-all">
                    {supplier.stock_value.toLocaleString()} {supplier.purchase_currency}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Currency:</span>
                  <span className="font-medium">{supplier.purchase_currency}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Alerts */}
      {dashboardData.recent_alerts.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold text-gray-800">Recent Alerts</h3>
            <button
              onClick={() => setShowAlerts(!showAlerts)}
              className="flex items-center space-x-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
            >
              {showAlerts ? (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                  <span>Hide Alerts</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span>Show Alerts ({dashboardData.recent_alerts.length})</span>
                </>
              )}
            </button>
          </div>
          {showAlerts && (
            <div className="space-y-3">
              {dashboardData.recent_alerts.map((alert, index) => (
              <div 
                key={index}
                className={`p-4 rounded-lg border-l-4 cursor-pointer hover:bg-gray-50 ${
                  alert.priority === 'high' ? 'border-red-500 bg-red-50' :
                  alert.priority === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                  'border-blue-500 bg-blue-50'
                }`}
                onClick={() => onAlertClick && onAlertClick(alert)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-800">{alert.message}</p>
                    <p className="text-sm text-gray-600">
                      {getDepartmentName(alert.department)} • {alert.section}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      alert.priority === 'high' ? 'bg-red-100 text-red-800' :
                      alert.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {alert.priority.toUpperCase()}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(alert.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Quick Actions - Mobile Optimized */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl p-3 md:p-6 text-white">
        <h3 className="text-base md:text-lg lg:text-xl font-semibold mb-3 md:mb-4 flex items-center">
          ⚡ <span className="ml-2">Quick Actions</span>
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3 lg:gap-4">
          <button 
            className="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 md:p-3 lg:p-4 rounded-lg transition-all text-center cursor-pointer active:scale-95"
            onClick={() => {
              if (onProductClick) {
                onProductClick('low_stock', 'all');
              } else {
                window.location.href = '/products?status=low_stock';
              }
            }}
          >
            <div className="text-lg md:text-xl lg:text-2xl mb-1 md:mb-2">⚠️</div>
            <div className="text-xs md:text-sm font-medium leading-tight">Low Stock</div>
          </button>
          
          <button 
            className="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 md:p-3 lg:p-4 rounded-lg transition-all text-center cursor-pointer active:scale-95"
            onClick={() => {
              if (onProductClick) {
                onProductClick('near_expiry', 'all');
              } else {
                window.location.href = '/products?status=near_expiry';
              }
            }}
          >
            <div className="text-lg md:text-xl lg:text-2xl mb-1 md:mb-2">⏰</div>
            <div className="text-xs md:text-sm font-medium leading-tight">Near Expiry</div>
          </button>
          
          <div className="relative">
            <button 
              className="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 md:p-3 lg:p-4 rounded-lg transition-all text-center cursor-pointer w-full active:scale-95"
              onClick={() => setShowExportDropdown(!showExportDropdown)}
            >
              <div className="text-lg md:text-xl lg:text-2xl mb-1 md:mb-2">📊</div>
              <div className="text-xs md:text-sm font-medium leading-tight">Export</div>
            </button>
            
            {showExportDropdown && (
              <div className="absolute top-full left-0 mt-2 w-40 md:w-48 bg-white rounded-lg shadow-lg border z-50">
                <div className="py-1 md:py-2">
                  <button
                    onClick={() => handleExport('inventory')}
                    className="w-full px-3 md:px-4 py-1.5 md:py-2 text-left hover:bg-gray-100 text-xs md:text-sm text-gray-700"
                  >
                    📋 Inventory
                  </button>
                  <button
                    onClick={() => handleExport('dashboard-excel')}
                    className="w-full px-3 md:px-4 py-1.5 md:py-2 text-left hover:bg-gray-100 text-xs md:text-sm text-gray-700"
                  >
                    📊 Dashboard
                  </button>
                  <button
                    onClick={() => handleExport('dashboard-pdf')}
                    className="w-full px-3 md:px-4 py-1.5 md:py-2 text-left hover:bg-gray-100 text-xs md:text-sm text-gray-700"
                  >
                    📄 PDF Report
                  </button>
                  <button
                    onClick={() => handleExport('expiry-tracker')}
                    className="w-full px-3 md:px-4 py-1.5 md:py-2 text-left hover:bg-gray-100 text-xs md:text-sm text-gray-700"
                  >
                    ⏰ Expiry
                  </button>
                  <button
                    onClick={() => handleExport('return-forms')}
                    className="w-full px-3 md:px-4 py-1.5 md:py-2 text-left hover:bg-gray-100 text-xs md:text-sm text-gray-700"
                  >
                    🔄 Returns
                  </button>
                </div>
              </div>
            )}
          </div>
          
          <button 
            className="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 md:p-3 lg:p-4 rounded-lg transition-all text-center cursor-pointer active:scale-95"
            onClick={() => {
              if (onProductClick) {
                onProductClick('all', 'all');
              } else {
                window.location.href = '/products';
              }
            }}
          >
            <div className="text-lg md:text-xl lg:text-2xl mb-1 md:mb-2">📦</div>
            <div className="text-xs md:text-sm font-medium leading-tight">All Items</div>
          </button>
        </div>
      </div>

      {/* Floating Barcode Scanner Button - Repositioned to avoid watermark */}
      <div className="fixed bottom-20 right-4 md:bottom-24 md:right-6 z-50">
        <button
          onClick={() => setShowScanner(true)}
          className="w-14 h-14 md:w-16 md:h-16 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 flex items-center justify-center ring-2 ring-white ring-opacity-30"
          title="⚡ Scan Barcode - Lightning Fast Scanner"
        >
          <Camera size={window.innerWidth > 768 ? 26 : 22} />
        </button>
      </div>

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

      {/* Product Details Modal */}
      <ProductDetailsModal
        product={selectedProduct}
        isOpen={showProductDetails}
        onClose={() => {
          setShowProductDetails(false);
          setSelectedProduct(null);
        }}
      />

      {/* Advanced Barcode Features Modal */}
      {showAdvancedFeatures && (
        <AdvancedBarcodeFeatures
          onClose={() => setShowAdvancedFeatures(false)}
        />
      )}
    </div>
  );
};

export default EnhancedDashboard;