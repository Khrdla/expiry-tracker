import React, { useState, useEffect } from "react";
import axios from "axios";
import { 
  BarChart3, 
  FileText, 
  Download, 
  AlertTriangle,
  DollarSign,
  Package,
  TrendingUp,
  Calendar,
  Filter,
  AlertCircle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Reports = () => {
  const [activeTab, setActiveTab] = useState("low-stock");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Report data states
  const [lowStockReport, setLowStockReport] = useState([]);
  const [inventoryValueReport, setInventoryValueReport] = useState({
    items: [],
    summary: { total_cost_value: 0, total_retail_value: 0, potential_profit: 0 }
  });
  const [stockTransactions, setStockTransactions] = useState([]);

  useEffect(() => {
    fetchReportData();
  }, [activeTab]);

  const fetchReportData = async () => {
    setLoading(true);
    setError(null);
    try {
      switch (activeTab) {
        case "low-stock":
          await fetchLowStockReport();
          break;
        case "inventory-value":
          await fetchInventoryValueReport();
          break;
        case "stock-movements":
          await fetchStockTransactions();
          break;
        default:
          break;
      }
    } catch (err) {
      setError("Failed to fetch report data");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLowStockReport = async () => {
    const response = await axios.get(`${API}/reports/low-stock`);
    setLowStockReport(response.data);
  };

  const fetchInventoryValueReport = async () => {
    const response = await axios.get(`${API}/reports/inventory-value`);
    setInventoryValueReport(response.data);
  };

  const fetchStockTransactions = async () => {
    const response = await axios.get(`${API}/stock-transactions?limit=50`);
    setStockTransactions(response.data);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTransactionIcon = (type) => {
    const iconProps = { size: 16, className: "mr-2" };
    switch (type) {
      case 'received':
        return <TrendingUp {...iconProps} className="mr-2 text-green-600" />;
      case 'sold':
        return <TrendingUp {...iconProps} className="mr-2 text-blue-600" style={{transform: 'rotate(180deg)'}} />;
      case 'adjusted':
        return <Package {...iconProps} className="mr-2 text-purple-600" />;
      case 'damaged':
      case 'expired':
        return <AlertTriangle {...iconProps} className="mr-2 text-red-600" />;
      default:
        return <Package {...iconProps} className="mr-2 text-gray-600" />;
    }
  };

  const getTransactionColor = (type) => {
    switch (type) {
      case 'received': return 'text-green-600';
      case 'sold': return 'text-blue-600';
      case 'adjusted': return 'text-purple-600';
      case 'damaged':
      case 'expired': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const exportToCSV = (data, filename) => {
    // Simple CSV export functionality
    const csvContent = data.map(row => Object.values(row).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const tabs = [
    { id: "low-stock", label: "Low Stock Report", icon: AlertTriangle },
    { id: "inventory-value", label: "Inventory Value", icon: DollarSign },
    { id: "stock-movements", label: "Stock Movements", icon: Package }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Reports & Analytics</h1>
          <p className="text-gray-600 mt-1">Generate and view comprehensive inventory reports</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={fetchReportData}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Filter size={16} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="text-red-500 mr-2" size={20} />
            <p className="text-red-700">{error}</p>
            <button 
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <Icon size={16} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              {/* Low Stock Report */}
              {activeTab === "low-stock" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">Low Stock Items</h2>
                    <button
                      onClick={() => exportToCSV(lowStockReport, 'low-stock-report.csv')}
                      className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors flex items-center space-x-2"
                    >
                      <Download size={16} />
                      <span>Export CSV</span>
                    </button>
                  </div>

                  {lowStockReport.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Stock</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Minimum Stock</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Shortage</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit Price</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reorder Value</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {lowStockReport.map((item, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm font-medium text-gray-900">{item.product_name}</div>
                                <div className="text-sm text-gray-500">SKU: {item.product_sku}</div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="text-sm font-medium text-red-600">{item.current_stock}</span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="text-sm text-gray-900">{item.min_stock}</span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                  -{item.shortage}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="text-sm text-gray-900">{formatCurrency(item.unit_price)}</span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="text-sm font-medium text-gray-900">
                                  {formatCurrency(item.shortage * item.unit_price)}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <AlertTriangle size={48} className="text-green-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Low Stock Items</h3>
                      <p className="text-gray-500">All products are adequately stocked!</p>
                    </div>
                  )}
                </div>
              )}

              {/* Inventory Value Report */}
              {activeTab === "inventory-value" && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">Inventory Value Analysis</h2>
                    <button
                      onClick={() => exportToCSV(inventoryValueReport.items, 'inventory-value-report.csv')}
                      className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors flex items-center space-x-2"
                    >
                      <Download size={16} />
                      <span>Export CSV</span>
                    </button>
                  </div>

                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
                      <div className="flex items-center">
                        <div className="p-3 rounded-full bg-blue-100">
                          <DollarSign className="text-blue-600" size={24} />
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-blue-700">Total Cost Value</p>
                          <p className="text-2xl font-bold text-blue-900">
                            {formatCurrency(inventoryValueReport.summary.total_cost_value)}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-green-50 rounded-xl p-6 border border-green-200">
                      <div className="flex items-center">
                        <div className="p-3 rounded-full bg-green-100">
                          <TrendingUp className="text-green-600" size={24} />
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-green-700">Total Retail Value</p>
                          <p className="text-2xl font-bold text-green-900">
                            {formatCurrency(inventoryValueReport.summary.total_retail_value)}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-purple-50 rounded-xl p-6 border border-purple-200">
                      <div className="flex items-center">
                        <div className="p-3 rounded-full bg-purple-100">
                          <BarChart3 className="text-purple-600" size={24} />
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-purple-700">Potential Profit</p>
                          <p className="text-2xl font-bold text-purple-900">
                            {formatCurrency(inventoryValueReport.summary.potential_profit)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Detailed Table */}
                  {inventoryValueReport.items.length > 0 && (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cost Value</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Retail Value</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Profit Margin</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {inventoryValueReport.items.slice(0, 20).map((item, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm font-medium text-gray-900">{item.product_name}</div>
                                <div className="text-sm text-gray-500">SKU: {item.product_sku}</div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="text-sm text-gray-900">{item.current_stock}</span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="text-sm text-gray-900">{formatCurrency(item.inventory_cost_value)}</span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="text-sm text-gray-900">{formatCurrency(item.inventory_retail_value)}</span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className="text-sm font-medium text-green-600">
                                  {formatCurrency((item.inventory_retail_value || 0) - (item.inventory_cost_value || 0))}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Stock Movements Report */}
              {activeTab === "stock-movements" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">Recent Stock Movements</h2>
                    <button
                      onClick={() => exportToCSV(stockTransactions, 'stock-movements-report.csv')}
                      className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors flex items-center space-x-2"
                    >
                      <Download size={16} />
                      <span>Export CSV</span>
                    </button>
                  </div>

                  {stockTransactions.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date & Time</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Transaction</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reference</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {stockTransactions.map((transaction, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-gray-900">{formatDate(transaction.created_at)}</div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm font-medium text-gray-900">{transaction.product_name}</div>
                                <div className="text-sm text-gray-500">SKU: {transaction.product_sku}</div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className={`flex items-center text-sm ${getTransactionColor(transaction.transaction_type)}`}>
                                  {getTransactionIcon(transaction.transaction_type)}
                                  <span className="capitalize">{transaction.transaction_type}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`text-sm font-medium ${
                                  transaction.transaction_type === 'received' ? 'text-green-600' :
                                  transaction.transaction_type === 'sold' ? 'text-blue-600' :
                                  'text-red-600'
                                }`}>
                                  {transaction.transaction_type === 'received' ? '+' : 
                                   transaction.transaction_type === 'adjusted' ? '=' : '-'}
                                  {transaction.quantity}
                                </span>
                              </td>
                              <td className="px-6 py-4">
                                <div className="text-sm text-gray-900 max-w-xs truncate">
                                  {transaction.reason || "No reason specified"}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-gray-500">
                                  {transaction.reference || "—"}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Package size={48} className="text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Stock Movements</h3>
                      <p className="text-gray-500">No recent stock transactions found.</p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Reports;