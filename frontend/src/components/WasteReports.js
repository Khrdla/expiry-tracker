import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Calendar, Download, Filter, TrendingUp, TrendingDown, Package, Trash2, AlertTriangle, CheckCircle2, Plus, Search, X, Calculator, Camera, Scan } from 'lucide-react';
import BarcodeScanner from './BarcodeScanner';

const WasteReports = () => {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState('weekly');
  const [department, setDepartment] = useState('');
  const [section, setSection] = useState('');
  const [customDateRange, setCustomDateRange] = useState({
    startDate: '',
    endDate: ''
  });
  const [showCustomRange, setShowCustomRange] = useState(false);
  
  // Waste Entry Form States
  const [showAddForm, setShowAddForm] = useState(false);
  const [wasteEntries, setWasteEntries] = useState([]);
  const [currentEntry, setCurrentEntry] = useState({
    barcode: '',
    productName: '',
    product: null,
    quantity: '',
    wasteReason: 'damaged',
    notes: ''
  });
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [addingWaste, setAddingWaste] = useState(false);
  const [showBarcodeScanner, setShowBarcodeScanner] = useState(false);

  // Department and section options
  const departments = [
    { value: '', label: 'All Departments' },
    { value: '01-FMG', label: '01-FMG (Fresh & Food Grocery)' },
    { value: '01-CGD', label: '01-CGD (Consumer Goods & Drinks)' },
    { value: '01-OPSS', label: '01-OPSS (Operations & Special Services)' }
  ];

  const sections = [
    { value: '', label: 'All Sections' },
    { value: 'S010 - Beverage', label: 'S010 - Beverage' },
    { value: 'S014 - Ultra Fresh', label: 'S014 - Ultra Fresh' },
    { value: 'S016 - Delicateen', label: 'S016 - Delicateen' },
    { value: 'S018 - Frozen Food', label: 'S018 - Frozen Food' },
    { value: 'S015 - Dairy Products', label: 'S015 - Dairy Products' }
  ];

  const periods = [
    { value: 'daily', label: 'Daily', icon: '📅' },
    { value: 'weekly', label: 'Weekly', icon: '📊' },
    { value: 'yearly', label: 'Yearly', icon: '📈' }
  ];

  // Colors for currency charts
  const currencyColors = {
    YER: '#22c55e', // Green
    SAR: '#3b82f6', // Blue  
    EUR: '#f59e0b'  // Orange
  };

  useEffect(() => {
    fetchWasteReport();
  }, [period, department, section]);

  // Search product by barcode or name
  const searchProduct = async (searchTerm) => {
    if (!searchTerm.trim()) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      // Try barcode lookup first
      let response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/barcode/${searchTerm}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const product = await response.json();
        setSearchResults([product]);
      } else {
        // If barcode fails, search by product name
        response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/products?search=${encodeURIComponent(searchTerm)}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          setSearchResults(data.products || []);
        } else {
          setSearchResults([]);
        }
      }
    } catch (error) {
      console.error('Error searching products:', error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  // Handle product selection
  const selectProduct = (product) => {
    setCurrentEntry(prev => ({
      ...prev,
      product: product,
      barcode: product.barcode || '',
      productName: product.product_name || ''
    }));
    setSearchResults([]);
  };

  // Handle barcode scanner result
  const handleBarcodeFound = (product) => {
    console.log('📱 Barcode scanner found product:', product);
    selectProduct(product);
    setShowBarcodeScanner(false);
  };

  // Add waste entry to the list
  const addWasteEntry = () => {
    if (!currentEntry.product || !currentEntry.quantity) return;

    const wasteValue = parseFloat(currentEntry.quantity) * parseFloat(currentEntry.product.purchase_price || 0);
    const newEntry = {
      id: Date.now(),
      product: currentEntry.product,
      quantity: parseInt(currentEntry.quantity),
      wasteValue: wasteValue,
      wasteReason: currentEntry.wasteReason,
      notes: currentEntry.notes,
      addedAt: new Date().toISOString()
    };

    setWasteEntries(prev => [...prev, newEntry]);
    
    // Reset form
    setCurrentEntry({
      barcode: '',
      productName: '',
      product: null,
      quantity: '',
      wasteReason: 'damaged',
      notes: ''
    });
  };

  // Remove waste entry from list
  const removeWasteEntry = (entryId) => {
    setWasteEntries(prev => prev.filter(entry => entry.id !== entryId));
  };

  // Submit all waste entries to backend
  const submitWasteEntries = async () => {
    if (wasteEntries.length === 0) return;

    setAddingWaste(true);
    try {
      let successCount = 0;
      for (const entry of wasteEntries) {
        const wasteData = {
          product_id: entry.product.id,
          quantity_wasted: entry.quantity,
          waste_reason: entry.wasteReason,
          notes: entry.notes
        };

        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/waste/entries`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(wasteData)
        });

        if (response.ok) {
          successCount++;
        }
      }

      if (successCount > 0) {
        alert(`Successfully added ${successCount} waste entries!`);
        setWasteEntries([]);
        setShowAddForm(false);
        // Refresh the report
        fetchWasteReport();
      }
    } catch (error) {
      console.error('Error submitting waste entries:', error);
      alert('Failed to submit waste entries. Please try again.');
    } finally {
      setAddingWaste(false);
    }
  };

  // Calculate total waste value
  const getTotalWasteValue = () => {
    return wasteEntries.reduce((total, entry) => total + entry.wasteValue, 0);
  };

  // Group waste entries by currency
  const getWasteValueByCurrency = () => {
    const totals = { YER: 0, SAR: 0, EUR: 0 };
    wasteEntries.forEach(entry => {
      const currency = entry.product.purchase_currency || 'YER';
      if (currency in totals) {
        totals[currency] += entry.wasteValue;
      }
    });
    return totals;
  };

  const fetchWasteReport = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        period: period,
        ...(department && { department }),
        ...(section && { section }),
        ...(showCustomRange && customDateRange.startDate && { start_date: customDateRange.startDate }),
        ...(showCustomRange && customDateRange.endDate && { end_date: customDateRange.endDate })
      });

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/waste/reports?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setReportData(data);
      } else {
        console.error('Failed to fetch waste report');
        setReportData({
          currency_totals: { YER: 0, SAR: 0, EUR: 0 },
          total_entries: 0,
          total_quantity_wasted: 0
        });
      }
    } catch (error) {
      console.error('Error fetching waste report:', error);
      setReportData({
        currency_totals: { YER: 0, SAR: 0, EUR: 0 },
        total_entries: 0,
        total_quantity_wasted: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const params = new URLSearchParams({
        format: format,
        ...(department && { department }),
        ...(section && { section }),
        ...(showCustomRange && customDateRange.startDate && { start_date: customDateRange.startDate }),
        ...(showCustomRange && customDateRange.endDate && { end_date: customDateRange.endDate })
      });

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/export/waste-report/${period}?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `waste_report_${period}_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        console.error('Failed to export report');
      }
    } catch (error) {
      console.error('Error exporting report:', error);
    }
  };

  // Prepare chart data
  const chartData = reportData ? Object.entries(reportData.currency_totals)
    .filter(([currency, value]) => value > 0)
    .map(([currency, value]) => ({
      currency,
      value,
      displayValue: `${value.toLocaleString()} ${currency}`
    })) : [];

  const pieData = chartData.map((item, index) => ({
    ...item,
    fill: currencyColors[item.currency] || '#8884d8'
  }));

  const formatCurrency = (value, currency) => {
    return `${parseFloat(value).toLocaleString()} ${currency}`;
  };

  const getReportTotalWasteValue = () => {
    if (!reportData) return 0;
    return Object.values(reportData.currency_totals).reduce((sum, value) => sum + value, 0);
  };

  const formatDateRange = () => {
    if (!reportData) return '';
    const start = new Date(reportData.start_date).toLocaleDateString();
    const end = new Date(reportData.end_date).toLocaleDateString();
    return `${start} - ${end}`;
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Trash2 size={32} className="text-red-500" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Waste Reports</h1>
              <p className="text-gray-600">Track damaged and unsellable product waste by currency and time period</p>
            </div>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              showAddForm 
                ? 'bg-gray-500 text-white hover:bg-gray-600' 
                : 'bg-green-500 text-white hover:bg-green-600'
            }`}
          >
            {showAddForm ? <X size={20} /> : <Plus size={20} />}
            <span>{showAddForm ? 'Close Form' : 'Add Waste Entry'}</span>
          </button>
        </div>
      </div>

      {/* Add Waste Entry Form */}
      {showAddForm && (
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center space-x-3 mb-6">
            <div className="bg-red-100 p-2 rounded-full">
              <Plus size={20} className="text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Add Waste Entry</h2>
              <p className="text-sm text-gray-600">Enter barcode or product name, quantity, and reason</p>
            </div>
          </div>

          {/* Search Product */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                🔍 Search by Barcode or Product Name
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={currentEntry.barcode || currentEntry.productName}
                  onChange={(e) => {
                    const value = e.target.value;
                    setCurrentEntry(prev => ({
                      ...prev,
                      barcode: /^\d+$/.test(value) ? value : '',
                      productName: !/^\d+$/.test(value) ? value : ''
                    }));
                    searchProduct(value);
                  }}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent pr-10"
                  placeholder="Enter barcode number or product name..."
                />
                <Search size={20} className="absolute right-3 top-3 text-gray-400" />
                
                {/* Search Results Dropdown */}
                {searchResults.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {searchResults.map((product, index) => (
                      <div
                        key={index}
                        onClick={() => selectProduct(product)}
                        className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                      >
                        <div className="font-medium text-gray-900">{product.product_name}</div>
                        <div className="text-sm text-gray-600">
                          {product.barcode && `Barcode: ${product.barcode} • `}
                          {product.purchase_price} {product.purchase_currency} • {product.department}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {searching && (
                <p className="text-sm text-gray-500 mt-1">🔍 Searching products...</p>
              )}
            </div>

            {/* Selected Product Display */}
            {currentEntry.product && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Package size={16} className="text-green-600" />
                  <span className="font-medium text-green-800">Selected Product</span>
                </div>
                <p className="font-semibold text-gray-900">{currentEntry.product.product_name}</p>
                <p className="text-sm text-gray-600">
                  {currentEntry.product.department} • {currentEntry.product.section}
                </p>
                <p className="text-sm text-gray-600">
                  Purchase Price: <span className="font-medium">{currentEntry.product.purchase_price} {currentEntry.product.purchase_currency}</span>
                </p>
                {currentEntry.product.barcode && (
                  <p className="text-sm text-gray-600">Barcode: {currentEntry.product.barcode}</p>
                )}
              </div>
            )}
          </div>

          {/* Quantity and Details */}
          {currentEntry.product && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  📦 Quantity Wasted *
                </label>
                <input
                  type="number"
                  min="1"
                  value={currentEntry.quantity}
                  onChange={(e) => setCurrentEntry(prev => ({ ...prev, quantity: e.target.value }))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Enter quantity"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ⚠️ Waste Reason
                </label>
                <select
                  value={currentEntry.wasteReason}
                  onChange={(e) => setCurrentEntry(prev => ({ ...prev, wasteReason: e.target.value }))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                >
                  <option value="damaged">💥 Damaged</option>
                  <option value="expired">⏰ Expired</option>
                  <option value="unsellable">❌ Unsellable</option>
                  <option value="contaminated">🦠 Contaminated</option>
                  <option value="broken_packaging">📦 Broken Packaging</option>
                  <option value="quality_issue">⚠️ Quality Issue</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  💰 Waste Value
                </label>
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <span className="text-lg font-bold text-red-900">
                    {currentEntry.quantity ? 
                      `${(parseFloat(currentEntry.quantity) * parseFloat(currentEntry.product.purchase_price || 0)).toLocaleString()} ${currentEntry.product.purchase_currency}` 
                      : '0.00'
                    }
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Notes */}
          {currentEntry.product && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📝 Notes (Optional)
              </label>
              <input
                type="text"
                value={currentEntry.notes}
                onChange={(e) => setCurrentEntry(prev => ({ ...prev, notes: e.target.value }))}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="Additional details about the waste..."
              />
            </div>
          )}

          {/* Add Button */}
          {currentEntry.product && currentEntry.quantity && (
            <div className="flex justify-end">
              <button
                onClick={addWasteEntry}
                className="flex items-center space-x-2 bg-red-500 text-white px-6 py-3 rounded-lg hover:bg-red-600 transition-colors font-medium"
              >
                <Plus size={16} />
                <span>Add to List</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Current Waste Entries List */}
      {wasteEntries.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="bg-orange-100 p-2 rounded-full">
                <Calculator size={20} className="text-orange-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Added Waste Entries ({wasteEntries.length})</h3>
                <p className="text-sm text-gray-600">Review and submit waste entries</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Total Waste Value</p>
              <p className="text-xl font-bold text-red-600">
                {getTotalWasteValue().toLocaleString()} (Multi-Currency)
              </p>
            </div>
          </div>

          {/* Currency Breakdown */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            {Object.entries(getWasteValueByCurrency()).map(([currency, value]) => (
              <div key={currency} className="bg-gray-50 p-3 rounded-lg text-center">
                <p className="text-sm font-medium text-gray-600">{currency}</p>
                <p className="text-lg font-bold text-gray-900">{value.toLocaleString()}</p>
              </div>
            ))}
          </div>

          {/* Entries Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 font-medium text-gray-700">Product</th>
                  <th className="text-center py-2 font-medium text-gray-700">Qty</th>
                  <th className="text-center py-2 font-medium text-gray-700">Price</th>
                  <th className="text-center py-2 font-medium text-gray-700">Waste Value</th>
                  <th className="text-center py-2 font-medium text-gray-700">Reason</th>
                  <th className="text-center py-2 font-medium text-gray-700">Action</th>
                </tr>
              </thead>
              <tbody>
                {wasteEntries.map((entry) => (
                  <tr key={entry.id} className="border-b border-gray-100">
                    <td className="py-3">
                      <div className="font-medium text-gray-900">{entry.product.product_name}</div>
                      <div className="text-xs text-gray-500">{entry.product.department}</div>
                    </td>
                    <td className="text-center py-3 font-medium">{entry.quantity}</td>
                    <td className="text-center py-3">
                      {entry.product.purchase_price} {entry.product.purchase_currency}
                    </td>
                    <td className="text-center py-3 font-bold text-red-600">
                      {entry.wasteValue.toLocaleString()} {entry.product.purchase_currency}
                    </td>
                    <td className="text-center py-3">
                      <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs">
                        {entry.wasteReason}
                      </span>
                    </td>
                    <td className="text-center py-3">
                      <button
                        onClick={() => removeWasteEntry(entry.id)}
                        className="text-red-500 hover:text-red-700 p-1"
                      >
                        <X size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end mt-6">
            <button
              onClick={submitWasteEntries}
              disabled={addingWaste}
              className="flex items-center space-x-2 bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 disabled:opacity-50 transition-colors font-medium"
            >
              {addingWaste ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 size={16} />
                  <span>Submit All Entries ({wasteEntries.length})</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          {/* Period Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Time Period</label>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              {periods.map(p => (
                <option key={p.value} value={p.value}>
                  {p.icon} {p.label}
                </option>
              ))}
            </select>
          </div>

          {/* Department Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Department</label>
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              {departments.map(dept => (
                <option key={dept.value} value={dept.value}>{dept.label}</option>
              ))}
            </select>
          </div>

          {/* Section Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Section</label>
            <select
              value={section}
              onChange={(e) => setSection(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              {sections.map(sect => (
                <option key={sect.value} value={sect.value}>{sect.label}</option>
              ))}
            </select>
          </div>

          {/* Custom Date Range Toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Custom Range</label>
            <button
              onClick={() => setShowCustomRange(!showCustomRange)}
              className={`w-full p-3 rounded-lg font-medium transition-colors ${
                showCustomRange 
                  ? 'bg-green-500 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Calendar size={16} className="inline mr-2" />
              {showCustomRange ? 'Custom Active' : 'Use Custom'}
            </button>
          </div>
        </div>

        {/* Custom Date Range Inputs */}
        {showCustomRange && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
              <input
                type="date"
                value={customDateRange.startDate}
                onChange={(e) => setCustomDateRange(prev => ({ ...prev, startDate: e.target.value }))}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
              <input
                type="date"
                value={customDateRange.endDate}
                onChange={(e) => setCustomDateRange(prev => ({ ...prev, endDate: e.target.value }))}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {/* Export Buttons */}
        <div className="flex space-x-4 pt-4 border-t">
          <button
            onClick={() => handleExport('excel')}
            className="flex items-center space-x-2 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
          >
            <Download size={16} />
            <span>Export Excel</span>
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="flex items-center space-x-2 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
          >
            <Download size={16} />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-lg shadow-sm border p-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
            <span className="ml-3 text-gray-600">Loading waste report...</span>
          </div>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            {/* YER Total */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">YER Waste Value</p>
                  <p className="text-2xl font-bold text-green-600">
                    {reportData ? formatCurrency(reportData.currency_totals.YER, 'YER') : '0 YER'}
                  </p>
                </div>
                <div className="bg-green-100 p-3 rounded-full">
                  <Package size={24} className="text-green-600" />
                </div>
              </div>
            </div>

            {/* SAR Total */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">SAR Waste Value</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {reportData ? formatCurrency(reportData.currency_totals.SAR, 'SAR') : '0 SAR'}
                  </p>
                </div>
                <div className="bg-blue-100 p-3 rounded-full">
                  <Package size={24} className="text-blue-600" />
                </div>
              </div>
            </div>

            {/* EUR Total */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">EUR Waste Value</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {reportData ? formatCurrency(reportData.currency_totals.EUR, 'EUR') : '0 EUR'}
                  </p>
                </div>
                <div className="bg-orange-100 p-3 rounded-full">
                  <Package size={24} className="text-orange-600" />
                </div>
              </div>
            </div>

            {/* Total Entries */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Entries</p>
                  <p className="text-2xl font-bold text-red-600">
                    {reportData ? reportData.total_entries.toLocaleString() : '0'}
                  </p>
                  <p className="text-sm text-gray-500">
                    {reportData ? `${reportData.total_quantity_wasted.toLocaleString()} items` : '0 items'}
                  </p>
                </div>
                <div className="bg-red-100 p-3 rounded-full">
                  <AlertTriangle size={24} className="text-red-600" />
                </div>
              </div>
            </div>
          </div>

          {/* Report Period Info */}
          <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Calendar size={20} className="text-gray-500" />
                <div>
                  <p className="font-medium text-gray-900">Report Period: {period.charAt(0).toUpperCase() + period.slice(1)}</p>
                  <p className="text-sm text-gray-600">{formatDateRange()}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">Generated</p>
                <p className="font-medium text-gray-900">
                  {reportData ? new Date(reportData.generated_at).toLocaleString() : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Charts */}
          {chartData.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Bar Chart */}
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Waste Value by Currency</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="currency" />
                    <YAxis />
                    <Tooltip formatter={(value, name) => [value.toLocaleString(), 'Waste Value']} />
                    <Bar dataKey="value" fill="#22c55e" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Pie Chart */}
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Waste Distribution</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ currency, value }) => `${currency}: ${value.toLocaleString()}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [value.toLocaleString(), 'Waste Value']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <CheckCircle2 size={48} className="text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Waste Data</h3>
              <p className="text-gray-600">No waste entries found for the selected period and filters.</p>
              <p className="text-sm text-gray-500 mt-2">This is good news - no damaged or unsellable products reported!</p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default WasteReports;