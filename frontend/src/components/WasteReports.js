import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Calendar, Download, Filter, TrendingUp, TrendingDown, Package, Trash2, AlertTriangle, CheckCircle2 } from 'lucide-react';

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

  const getTotalWasteValue = () => {
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
        <div className="flex items-center space-x-3 mb-4">
          <Trash2 size={32} className="text-red-500" />
          <h1 className="text-3xl font-bold text-gray-900">Waste Reports</h1>
        </div>
        <p className="text-gray-600">Track damaged and unsellable product waste by currency and time period</p>
      </div>

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