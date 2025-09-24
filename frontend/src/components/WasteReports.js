import React, { useState, useEffect, useMemo } from 'react';
import { 
  Trash2, 
  Plus, 
  Filter, 
  Download, 
  Calendar,
  TrendingUp,
  DollarSign,
  AlertTriangle,
  Package,
  Search,
  Camera,
  X,
  CheckCircle
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import EnhancedBarcodeScanner from './EnhancedBarcodeScanner';
import AddWasteEntryModal from './AddWasteEntryModal';

/**
 * Enhanced Waste Reports with Improved Data Handling
 * 
 * Fixes:
 * - Proper null/undefined handling for all data fields
 * - Fallback values to prevent displaying indices
 * - Enhanced error boundaries and logging
 * - Stable state management for product selection
 * - Improved chart data processing
 */
const EnhancedWasteReports = () => {
  const [wasteData, setWasteData] = useState([]);
  const [wasteEntries, setWasteEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPeriod, setSelectedPeriod] = useState('weekly');
  const [selectedCurrency, setSelectedCurrency] = useState('all');
  const [selectedDepartment, setSelectedDepartment] = useState('all');
  const [selectedSection, setSelectedSection] = useState('all');
  const [showAddEntry, setShowAddEntry] = useState(false);
  const [showScanner, setShowScanner] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [wasteQuantity, setWasteQuantity] = useState('');
  const [wasteReason, setWasteReason] = useState('damaged');
  const [pendingEntries, setPendingEntries] = useState([]);
  
  const [filterOptions, setFilterOptions] = useState({
    departments: [],
    sections: [],
    suppliers: []
  });

  // Enhanced debug info
  const [debugInfo, setDebugInfo] = useState({
    lastLoad: null,
    dataCount: 0,
    apiCalls: 0,
    errors: 0
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

  // Enhanced logging system
  const logActivity = (action, details = {}) => {
    const timestamp = new Date().toISOString();
    console.log(`[WasteReports] ${timestamp} - ${action}:`, details);
    
    setDebugInfo(prev => ({
      ...prev,
      lastActivity: timestamp,
      apiCalls: action.includes('API') ? prev.apiCalls + 1 : prev.apiCalls,
      errors: action.includes('ERROR') ? prev.errors + 1 : prev.errors
    }));
  };

  useEffect(() => {
    loadWasteReports();
    loadWasteEntries();
    loadFilterOptions();
  }, [selectedPeriod, selectedCurrency, selectedDepartment, selectedSection]);

  // Enhanced waste reports loading
  const loadWasteReports = async () => {
    try {
      setLoading(true);
      logActivity('API_CALL_WASTE_REPORTS', {
        period: selectedPeriod,
        currency: selectedCurrency,
        department: selectedDepartment
      });
      
      const token = localStorage.getItem('token');
      
      if (!token) {
        logActivity('ERROR_NO_TOKEN');
        setError('Authentication token not found');
        return;
      }
      
      const queryParams = new URLSearchParams({
        period: selectedPeriod,
        ...(selectedCurrency !== 'all' && { currency: selectedCurrency }),
        ...(selectedDepartment !== 'all' && { department: selectedDepartment }),
        ...(selectedSection !== 'all' && { section: selectedSection })
      });
      
      const response = await fetch(`${BACKEND_URL}/api/waste/reports?${queryParams.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        const processedData = processWasteData(data);
        
        logActivity('WASTE_REPORTS_SUCCESS', {
          summaryExists: !!processedData.summary,
          breakdownCount: processedData.department_breakdown?.length || 0
        });
        
        setWasteData(processedData);
        setError('');
        
        setDebugInfo(prev => ({
          ...prev,
          lastLoad: new Date().toISOString(),
          dataCount: processedData.department_breakdown?.length || 0
        }));
      } else {
        const errorText = await response.text();
        logActivity('WASTE_REPORTS_ERROR', {
          status: response.status,
          error: errorText
        });
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
    } catch (error) {
      logActivity('WASTE_REPORTS_EXCEPTION', { error: error.message });
      console.error('Waste reports error:', error);
      setError(`Failed to load waste reports: ${error.message}`);
      setWasteData([]);
    } finally {
      setLoading(false);
    }
  };

  // Enhanced waste data processing with debug logging
  const processWasteData = (rawData) => {
    console.log('🗑️ Processing Waste Data:', {
      rawData: rawData,
      departmentBreakdown: rawData?.department_breakdown
    });

    const processedData = {
      summary: {
        total_waste_value: safeNumber(rawData?.summary?.total_waste_value, 0),
        total_items_wasted: safeNumber(rawData?.summary?.total_items_wasted, 0),
        total_entries: safeNumber(rawData?.summary?.total_entries, 0)
      },
      currency_breakdown: processArray(rawData?.currency_breakdown, (item, index) => ({
        currency: safeString(item?.currency) || `Currency_${index + 1}`,
        total_value: safeNumber(item?.total_value, 0),
        total_items: safeNumber(item?.total_items, 0)
      })),
      department_breakdown: processArray(rawData?.department_breakdown, (item, index) => {
        const departmentName = item?.department || item?.name || `Department_${index + 1}`;
        console.log(`🏢 Processing department ${index}:`, {
          raw: item,
          extractedName: departmentName
        });
        
        return {
          department: departmentName,
          total_waste_value: safeNumber(item?.total_waste_value, 0),
          total_items: safeNumber(item?.total_items, 0)
        };
      }),
      reason_breakdown: processArray(rawData?.reason_breakdown, (item, index) => ({
        reason: safeString(item?.reason) || `Reason_${index + 1}`,
        total_waste_value: safeNumber(item?.total_waste_value, 0),
        percentage: safeNumber(item?.percentage, 0)
      }))
    };
    
    console.log('✅ Processed Waste Data:', {
      processedData: processedData,
      departmentNames: processedData.department_breakdown.map(d => d.department)
    });
    
    logActivity('WASTE_DATA_PROCESSED', {
      summaryValue: processedData.summary.total_waste_value,
      currencyCount: processedData.currency_breakdown.length,
      departmentCount: processedData.department_breakdown.length,
      departmentNames: processedData.department_breakdown.map(d => d.department)
    });
    
    return processedData;
  };

  // Enhanced waste entries loading
  const loadWasteEntries = async () => {
    try {
      logActivity('API_CALL_WASTE_ENTRIES');
      const token = localStorage.getItem('token');
      
      if (!token) {
        logActivity('ERROR_NO_TOKEN_ENTRIES');
        return;
      }
      
      const queryParams = new URLSearchParams({
        ...(selectedDepartment !== 'all' && { department: selectedDepartment }),
        ...(selectedSection !== 'all' && { section: selectedSection }),
        limit: '50'
      });
      
      const response = await fetch(`${BACKEND_URL}/api/waste/entries?${queryParams.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        const processedEntries = processWasteEntries(data.entries || []);
        
        logActivity('WASTE_ENTRIES_SUCCESS', { count: processedEntries.length });
        setWasteEntries(processedEntries);
      } else {
        logActivity('WASTE_ENTRIES_ERROR', { status: response.status });
      }
    } catch (error) {
      logActivity('WASTE_ENTRIES_EXCEPTION', { error: error.message });
      console.error('Failed to load waste entries:', error);
    }
  };

  // Enhanced waste entries processing
  const processWasteEntries = (rawEntries) => {
    if (!Array.isArray(rawEntries)) return [];
    
    return rawEntries.map((entry, index) => ({
      id: entry?.id || `entry_${index}_${Date.now()}`,
      date: entry?.date || new Date().toISOString(),
      product_name: safeName(entry?.product_name) || `Product ${index + 1}`,
      department: safeString(entry?.department) || 'Unknown Department',
      quantity_wasted: safeNumber(entry?.quantity_wasted, 0),
      waste_reason: safeString(entry?.waste_reason) || 'unknown',
      total_waste_value: safeNumber(entry?.total_waste_value, 0),
      purchase_currency: safeString(entry?.purchase_currency) || 'USD'
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
          sections: data?.sections?.length || 0
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

  // Enhanced product search
  const searchProducts = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    
    try {
      logActivity('PRODUCT_SEARCH', { query: query.trim() });
      const token = localStorage.getItem('token');
      
      if (!token) {
        logActivity('ERROR_NO_TOKEN_SEARCH');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/products/search?q=${encodeURIComponent(query)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        const processedResults = processSearchResults(data.products || []);
        
        logActivity('SEARCH_SUCCESS', { results: processedResults.length });
        setSearchResults(processedResults);
      } else {
        logActivity('SEARCH_ERROR', { status: response.status });
      }
    } catch (error) {
      logActivity('SEARCH_EXCEPTION', { error: error.message });
      console.error('Search error:', error);
    }
  };

  // Enhanced search results processing
  const processSearchResults = (results) => {
    if (!Array.isArray(results)) return [];
    
    return results.map((product, index) => ({
      id: product?.id || `search_${index}_${Date.now()}`,
      product_name: safeName(product?.product_name) || `Product ${index + 1}`,
      item_number: safeString(product?.item_number) || `ITM-${index + 1}`,
      department: safeString(product?.department) || 'Unknown Department',
      purchase_price: safeNumber(product?.purchase_price, 0),
      purchase_currency: safeString(product?.purchase_currency) || 'USD'
    }));
  };

  // Enhanced product selection
  const handleProductSelect = (product) => {
    logActivity('PRODUCT_SELECTED', { productId: product?.id });
    setSelectedProduct(product);
    setSearchTerm(product?.product_name || '');
    setSearchResults([]);
  };

  // Enhanced waste value calculation
  const calculateWasteValue = () => {
    if (!selectedProduct || !wasteQuantity) return 0;
    
    const quantity = safeNumber(wasteQuantity, 0);
    const price = safeNumber(selectedProduct.purchase_price, 0);
    
    return quantity * price;
  };

  // Enhanced pending entries management
  const addToPendingEntries = () => {
    if (!selectedProduct || !wasteQuantity) {
      logActivity('ERROR_INVALID_ENTRY_DATA');
      return;
    }
    
    const entry = {
      id: Date.now(),
      product: selectedProduct,
      quantity: safeNumber(wasteQuantity, 0),
      reason: wasteReason,
      wasteValue: calculateWasteValue()
    };
    
    logActivity('PENDING_ENTRY_ADDED', {
      productId: selectedProduct.id,
      quantity: entry.quantity,
      value: entry.wasteValue
    });
    
    setPendingEntries(prev => [...prev, entry]);
    
    // Reset form
    setSelectedProduct(null);
    setSearchTerm('');
    setWasteQuantity('');
    setWasteReason('damaged');
  };

  // Enhanced entries submission
  const submitAllEntries = async () => {
    if (pendingEntries.length === 0) return;
    
    try {
      logActivity('SUBMIT_ENTRIES_STARTED', { count: pendingEntries.length });
      const token = localStorage.getItem('token');
      
      if (!token) {
        logActivity('ERROR_NO_TOKEN_SUBMIT');
        setError('Authentication token not found');
        return;
      }
      
      for (const entry of pendingEntries) {
        const wasteEntry = {
          product_id: entry.product.id,
          quantity_wasted: entry.quantity,
          waste_reason: entry.reason,
          date: new Date().toISOString().split('T')[0]
        };
        
        await fetch(`${BACKEND_URL}/api/waste/entries`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(wasteEntry)
        });
      }
      
      logActivity('SUBMIT_ENTRIES_SUCCESS');
      setPendingEntries([]);
      loadWasteReports();
      loadWasteEntries();
      setError('');
      
    } catch (error) {
      logActivity('SUBMIT_ENTRIES_ERROR', { error: error.message });
      console.error('Submit entries error:', error);
      setError(`Failed to submit waste entries: ${error.message}`);
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
        period: selectedPeriod,
        ...(selectedCurrency !== 'all' && { currency: selectedCurrency }),
        ...(selectedDepartment !== 'all' && { department: selectedDepartment }),
        ...(selectedSection !== 'all' && { section: selectedSection })
      });
      
      const response = await fetch(`${BACKEND_URL}/api/export/waste-report/${selectedPeriod}?${queryParams.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `waste-report-${selectedPeriod}-${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
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

  const processArray = (array, processor) => {
    if (!Array.isArray(array)) return [];
    return array.map(processor).filter(Boolean);
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
      console.warn(`WasteReports filter fallback used for ${prefix}:`, item);
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

  // Enhanced total pending value calculation
  const totalPendingValue = useMemo(() => {
    const totals = { YER: 0, SAR: 0, EUR: 0 };
    pendingEntries.forEach(entry => {
      const currency = entry.product?.purchase_currency || 'YER';
      totals[currency] += safeNumber(entry.wasteValue, 0);
    });
    return totals;
  }, [pendingEntries]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading waste reports...</p>
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
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                <Trash2 className="text-red-600" />
                Enhanced Waste Reports
              </h1>
              <p className="text-gray-600 mt-1">
                Track and analyze product waste across departments
                {debugInfo.lastLoad && (
                  <span className="text-sm text-gray-400 ml-2">
                    • Updated {new Date(debugInfo.lastLoad).toLocaleTimeString()}
                  </span>
                )}
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
              <button
                onClick={() => setShowAddEntry(true)}
                className="flex items-center gap-2 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
              >
                <Plus size={18} />
                Add Entry
              </button>
              
              <button
                onClick={() => setShowScanner(true)}
                className="flex items-center gap-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                <Camera size={18} />
                Multi-Scan
              </button>
              
              <div className="relative group">
                <button className="flex items-center gap-2 bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors">
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
            </div>
          </div>
        </div>

        {/* Enhanced Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
            <AlertTriangle size={20} className="flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Waste Reports Error</p>
              <p className="text-sm">{error}</p>
              {debugInfo.errors > 0 && (
                <p className="text-xs mt-1">Total errors: {debugInfo.errors}</p>
              )}
            </div>
          </div>
        )}

        {/* Enhanced Filters */}
        <div className="mb-6 bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Filters & Settings</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Period</label>
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Currency</label>
              <select
                value={selectedCurrency}
                onChange={(e) => setSelectedCurrency(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Currencies</option>
                <option value="YER">YER</option>
                <option value="SAR">SAR</option>
                <option value="EUR">EUR</option>
              </select>
            </div>

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
          </div>
        </div>

        {/* Enhanced Quick Add Waste Entry */}
        <div className="mb-6 bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Plus className="text-green-600" />
            Quick Add Waste Entry
          </h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Enhanced Product Search */}
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Product (Barcode or Name)
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    searchProducts(e.target.value);
                  }}
                  placeholder="Search by barcode or product name..."
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
                
                {/* Enhanced Search Results Dropdown */}
                {searchResults.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {searchResults.map((product, index) => (
                      <button
                        key={`search-${index}`}
                        onClick={() => handleProductSelect(product)}
                        className="w-full text-left px-4 py-3 hover:bg-gray-100 border-b border-gray-100 last:border-b-0"
                      >
                        <div className="font-medium">{product.product_name}</div>
                        <div className="text-sm text-gray-500">
                          {product.item_number} | {product.department} | 
                          {formatCurrency(product.purchase_price, product.purchase_currency)}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Enhanced Selected Product Info */}
              {selectedProduct && (
                <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <h4 className="font-medium text-green-800">{selectedProduct.product_name}</h4>
                  <p className="text-sm text-green-600">
                    {selectedProduct.item_number} | {selectedProduct.department} | 
                    Price: {formatCurrency(selectedProduct.purchase_price, selectedProduct.purchase_currency)}
                  </p>
                </div>
              )}
            </div>

            {/* Enhanced Entry Form */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Quantity Wasted</label>
                <input
                  type="number"
                  value={wasteQuantity}
                  onChange={(e) => setWasteQuantity(e.target.value)}
                  placeholder="Enter quantity"
                  className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  min="0"
                  step="0.01"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Reason</label>
                <select
                  value={wasteReason}
                  onChange={(e) => setWasteReason(e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                >
                  <option value="damaged">Damaged</option>
                  <option value="expired">Expired</option>
                  <option value="unsellable">Unsellable</option>
                  <option value="contaminated">Contaminated</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Enhanced Calculated Value */}
              {selectedProduct && wasteQuantity && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-600">Waste Value:</p>
                  <p className="text-lg font-bold text-blue-800">
                    {formatCurrency(calculateWasteValue(), selectedProduct.purchase_currency)}
                  </p>
                </div>
              )}

              <button
                onClick={addToPendingEntries}
                disabled={!selectedProduct || !wasteQuantity}
                className="w-full bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Add to List
              </button>
            </div>
          </div>

          {/* Enhanced Pending Entries */}
          {pendingEntries.length > 0 && (
            <div className="mt-6 border-t border-gray-200 pt-6">
              <div className="flex justify-between items-center mb-4">
                <h4 className="font-semibold">Pending Entries ({pendingEntries.length})</h4>
                <button
                  onClick={submitAllEntries}
                  className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Submit All Entries
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {pendingEntries.map(entry => (
                      <tr key={entry.id} className="hover:bg-gray-50">
                        <td className="px-4 py-2 text-sm">{entry.product?.product_name || 'Unknown Product'}</td>
                        <td className="px-4 py-2 text-sm">{entry.quantity}</td>
                        <td className="px-4 py-2 text-sm capitalize">{entry.reason}</td>
                        <td className="px-4 py-2 text-sm font-medium">
                          {formatCurrency(entry.wasteValue, entry.product?.purchase_currency)}
                        </td>
                        <td className="px-4 py-2 text-sm">
                          <button
                            onClick={() => setPendingEntries(prev => prev.filter(e => e.id !== entry.id))}
                            className="text-red-600 hover:text-red-800"
                          >
                            <X size={16} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Enhanced Totals by Currency */}
              <div className="mt-4 grid grid-cols-3 gap-4">
                {Object.entries(totalPendingValue).map(([currency, value]) => (
                  <div key={currency} className="bg-gray-50 p-3 rounded-lg text-center">
                    <p className="text-xs text-gray-500">{currency} Total</p>
                    <p className="text-lg font-bold text-gray-900">
                      {formatCurrency(value, currency)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Enhanced Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Total Waste Value</p>
                <p className="text-2xl font-bold text-red-600">
                  {wasteData.summary ? formatCurrency(wasteData.summary.total_waste_value) : '$0'}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-red-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Items Wasted</p>
                <p className="text-2xl font-bold text-orange-600">
                  {wasteData.summary ? wasteData.summary.total_items_wasted.toLocaleString() : '0'}
                </p>
              </div>
              <Package className="h-8 w-8 text-orange-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Waste Entries</p>
                <p className="text-2xl font-bold text-blue-600">
                  {wasteData.summary ? wasteData.summary.total_entries.toLocaleString() : '0'}
                </p>
              </div>
              <Trash2 className="h-8 w-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Avg Per Entry</p>
                <p className="text-2xl font-bold text-purple-600">
                  {wasteData.summary && wasteData.summary.total_entries > 0 
                    ? formatCurrency(wasteData.summary.total_waste_value / wasteData.summary.total_entries)
                    : '$0'
                  }
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-600" />
            </div>
          </div>
        </div>

        {/* Enhanced Currency Breakdown */}
        {wasteData.currency_breakdown && wasteData.currency_breakdown.length > 0 && (
          <div className="mb-6 bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Waste by Currency</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {wasteData.currency_breakdown.map((item, index) => (
                <div key={`currency-${index}`} className="bg-gray-50 p-4 rounded-lg text-center hover:bg-gray-100 transition-colors">
                  <p className="text-sm text-gray-600">{item.currency}</p>
                  <p className="text-xl font-bold text-gray-900">
                    {formatCurrency(item.total_value, item.currency)}
                  </p>
                  <p className="text-sm text-gray-500">
                    {item.total_items.toLocaleString()} items
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Enhanced Charts */}
        {(wasteData.department_breakdown?.length > 0 || wasteData.reason_breakdown?.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Waste by Department */}
            {wasteData.department_breakdown && wasteData.department_breakdown.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Waste by Department</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={wasteData.department_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="department" />
                    <YAxis />
                    <Tooltip formatter={(value, name) => [formatCurrency(value), name]} />
                    <Legend />
                    <Bar dataKey="total_waste_value" fill="#8884d8" name="Waste Value" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Waste by Reason */}
            {wasteData.reason_breakdown && wasteData.reason_breakdown.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Waste by Reason</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={wasteData.reason_breakdown}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ reason, percentage }) => `${reason}: ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="total_waste_value"
                    >
                      {wasteData.reason_breakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [formatCurrency(value), 'Waste Value']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* Enhanced Recent Waste Entries */}
        {wasteEntries.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Waste Entries</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {wasteEntries.slice(0, 10).map((entry, index) => (
                    <tr key={`entry-${index}`} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(entry.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">
                        {entry.product_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {entry.department}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {entry.quantity_wasted.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                        {entry.waste_reason}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-red-600">
                        {formatCurrency(entry.total_waste_value, entry.purchase_currency)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Enhanced Barcode Scanner Modal */}
      <EnhancedBarcodeScanner
        isOpen={showScanner}
        onClose={() => setShowScanner(false)}
        onProductFound={(product) => {
          handleProductSelect(product);
          setShowScanner(false);
        }}
      />

      {/* Add Waste Entry Modal */}
      <AddWasteEntryModal
        isOpen={showAddEntry}
        onClose={() => setShowAddEntry(false)}
        onEntryAdded={() => {
          loadWasteReports();
          loadWasteEntries();
        }}
      />
    </div>
  );
};

export default EnhancedWasteReports;