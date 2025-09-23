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
import CleanCameraScanner from './CleanCameraScanner';
import AddWasteEntryModal from './AddWasteEntryModal';

const WasteReports = () => {
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

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

  useEffect(() => {
    loadWasteReports();
    loadWasteEntries();
    loadFilterOptions();
  }, [selectedPeriod, selectedCurrency, selectedDepartment, selectedSection]);

  const loadWasteReports = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
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
        setWasteData(data);
        setError('');
      } else {
        throw new Error('Failed to load waste reports');
      }
    } catch (error) {
      console.error('Waste reports error:', error);
      setError('Failed to load waste reports');
      setWasteData([]);
    } finally {
      setLoading(false);
    }
  };

  const loadWasteEntries = async () => {
    try {
      const token = localStorage.getItem('token');
      
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
        setWasteEntries(data.entries || []);
      }
    } catch (error) {
      console.error('Failed to load waste entries:', error);
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

  const searchProducts = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/products/search?q=${encodeURIComponent(query)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.products || []);
      }
    } catch (error) {
      console.error('Search error:', error);
    }
  };

  const handleProductSelect = (product) => {
    setSelectedProduct(product);
    setSearchTerm(product.product_name);
    setSearchResults([]);
  };

  const calculateWasteValue = () => {
    if (!selectedProduct || !wasteQuantity) return 0;
    return parseFloat(wasteQuantity) * (selectedProduct.purchase_price || 0);
  };

  const addToPendingEntries = () => {
    if (!selectedProduct || !wasteQuantity) return;
    
    const entry = {
      id: Date.now(),
      product: selectedProduct,
      quantity: parseFloat(wasteQuantity),
      reason: wasteReason,
      wasteValue: calculateWasteValue()
    };
    
    setPendingEntries(prev => [...prev, entry]);
    
    // Reset form
    setSelectedProduct(null);
    setSearchTerm('');
    setWasteQuantity('');
    setWasteReason('damaged');
  };

  const removePendingEntry = (entryId) => {
    setPendingEntries(prev => prev.filter(entry => entry.id !== entryId));
  };

  const submitAllEntries = async () => {
    if (pendingEntries.length === 0) return;
    
    try {
      const token = localStorage.getItem('token');
      
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
      
      setPendingEntries([]);
      loadWasteReports();
      loadWasteEntries();
      setError('');
      
    } catch (error) {
      console.error('Submit entries error:', error);
      setError('Failed to submit waste entries');
    }
  };

  const handleExport = async (format) => {
    try {
      const token = localStorage.getItem('token');
      
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
        a.download = `waste-report-${selectedPeriod}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export error:', error);
      setError(`Failed to export ${format}`);
    }
  };

  const formatCurrency = (amount, currency = 'USD') => {
    if (currency && ['YER', 'SAR', 'EUR'].includes(currency)) {
      return `${amount.toFixed(2)} ${currency}`;
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD'
    }).format(amount || 0);
  };

  const totalPendingValue = useMemo(() => {
    const totals = { YER: 0, SAR: 0, EUR: 0 };
    pendingEntries.forEach(entry => {
      const currency = entry.product.purchase_currency || 'YER';
      totals[currency] += entry.wasteValue;
    });
    return totals;
  }, [pendingEntries]);

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
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
                <Trash2 className="text-red-600" />
                Waste Reports
              </h1>
              <p className="text-gray-600 mt-1">
                Track and analyze product waste across departments
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
              <button
                onClick={() => setShowAddEntry(true)}
                className="flex items-center gap-2 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
              >
                <Plus size={18} />
                Add Waste Entry
              </button>
              
              <button
                onClick={() => setShowScanner(true)}
                className="flex items-center gap-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                <Camera size={18} />
                Scan Item
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

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Filters */}
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
                {filterOptions.departments?.map(dept => (
                  <option key={dept} value={dept}>{dept}</option>
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
                  <option key={section} value={section}>{section}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Quick Add Waste Entry */}
        <div className="mb-6 bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Plus className="text-green-600" />
            Quick Add Waste Entry
          </h3>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Product Search */}
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
                
                {/* Search Results Dropdown */}
                {searchResults.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {searchResults.map(product => (
                      <button
                        key={product.id}
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
              
              {/* Selected Product Info */}
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

            {/* Entry Form */}
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

              {/* Calculated Value */}
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

          {/* Pending Entries */}
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
                        <td className="px-4 py-2 text-sm">{entry.product.product_name}</td>
                        <td className="px-4 py-2 text-sm">{entry.quantity}</td>
                        <td className="px-4 py-2 text-sm capitalize">{entry.reason}</td>
                        <td className="px-4 py-2 text-sm font-medium">
                          {formatCurrency(entry.wasteValue, entry.product.purchase_currency)}
                        </td>
                        <td className="px-4 py-2 text-sm">
                          <button
                            onClick={() => removePendingEntry(entry.id)}
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

              {/* Totals by Currency */}
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

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
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

          <div className="bg-white rounded-lg shadow p-6">
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

          <div className="bg-white rounded-lg shadow p-6">
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

          <div className="bg-white rounded-lg shadow p-6">
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

        {/* Currency Breakdown */}
        {wasteData.currency_breakdown && wasteData.currency_breakdown.length > 0 && (
          <div className="mb-6 bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Waste by Currency</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {wasteData.currency_breakdown.map(item => (
                <div key={item.currency} className="bg-gray-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">{item.currency}</p>
                  <p className="text-xl font-bold text-gray-900">
                    {formatCurrency(item.total_value, item.currency)}
                  </p>
                  <p className="text-sm text-gray-500">
                    {item.total_items} items
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Charts */}
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
                  <Tooltip formatter={(value) => formatCurrency(value)} />
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
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Recent Waste Entries */}
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
                    <tr key={index} className="hover:bg-gray-50">
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
                        {entry.quantity_wasted}
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

      {/* Barcode Scanner Modal */}
      <CleanCameraScanner
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

export default WasteReports;