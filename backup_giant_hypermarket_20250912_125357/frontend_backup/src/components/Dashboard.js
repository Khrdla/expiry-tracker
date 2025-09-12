import React, { useState, useEffect } from "react";
import axios from "axios";
import { 
  Package, 
  Users, 
  Tags, 
  AlertTriangle, 
  DollarSign, 
  TrendingUp,
  Warehouse,
  ShoppingCart
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
  <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className={`text-2xl font-bold ${color}`}>{value}</p>
        {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
      </div>
      <div className={`p-3 rounded-full bg-opacity-10 ${color.replace('text-', 'bg-')}`}>
        <Icon size={24} className={color} />
      </div>
    </div>
  </div>
);

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_products: 0,
    total_categories: 0,
    total_suppliers: 0,
    low_stock_items: 0,
    total_inventory_value: 0,
    recent_transactions: 0
  });
  const [lowStockItems, setLowStockItems] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch dashboard stats
      const statsResponse = await axios.get(`${API}/dashboard/stats`);
      setStats(statsResponse.data);

      // Fetch low stock items
      const lowStockResponse = await axios.get(`${API}/reports/low-stock`);
      setLowStockItems(lowStockResponse.data.slice(0, 5)); // Show top 5

      // Fetch recent transactions
      const transactionsResponse = await axios.get(`${API}/stock-transactions?limit=5`);
      setRecentTransactions(transactionsResponse.data);

    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="text-red-500 mr-2" size={20} />
          <p className="text-red-700">{error}</p>
          <button 
            onClick={fetchDashboardData}
            className="ml-auto bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome to Giant Hypermarket Inventory Management</p>
        </div>
        <button 
          onClick={fetchDashboardData}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <TrendingUp size={16} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Products"
          value={stats.total_products.toLocaleString()}
          icon={Package}
          color="text-blue-600"
          subtitle="Active inventory items"
        />
        <StatCard
          title="Categories"
          value={stats.total_categories}
          icon={Tags}
          color="text-green-600"
          subtitle="Product categories"
        />
        <StatCard
          title="Suppliers"
          value={stats.total_suppliers}
          icon={Users}
          color="text-purple-600"
          subtitle="Active suppliers"
        />
        <StatCard
          title="Low Stock Alerts"
          value={stats.low_stock_items}
          icon={AlertTriangle}
          color="text-red-600"
          subtitle="Items below minimum"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <StatCard
          title="Inventory Value"
          value={formatCurrency(stats.total_inventory_value)}
          icon={DollarSign}
          color="text-emerald-600"
          subtitle="Total stock value"
        />
        <StatCard
          title="Recent Transactions"
          value={stats.recent_transactions}
          icon={ShoppingCart}
          color="text-orange-600"
          subtitle="Last 7 days"
        />
      </div>

      {/* Low Stock Alert Section */}
      {lowStockItems.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="text-red-500" size={20} />
              <h2 className="text-xl font-semibold text-gray-900">Low Stock Alerts</h2>
              <span className="bg-red-100 text-red-700 px-2 py-1 rounded-full text-sm font-medium">
                {lowStockItems.length} items
              </span>
            </div>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {lowStockItems.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-red-50 rounded-lg border border-red-100">
                  <div className="flex items-center space-x-3">
                    <Warehouse className="text-red-500" size={16} />
                    <div>
                      <p className="font-medium text-gray-900">{item.product_name}</p>
                      <p className="text-sm text-gray-500">SKU: {item.product_sku}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-red-700">
                      {item.current_stock} / {item.min_stock}
                    </p>
                    <p className="text-xs text-gray-500">
                      Need {item.shortage} more
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Recent Transactions */}
      {recentTransactions.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Recent Stock Transactions</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {recentTransactions.map((transaction, index) => (
                <div key={index} className="flex items-center justify-between p-4 hover:bg-gray-50 rounded-lg transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-full ${
                      transaction.transaction_type === 'received' ? 'bg-green-100 text-green-600' :
                      transaction.transaction_type === 'sold' ? 'bg-blue-100 text-blue-600' :
                      'bg-red-100 text-red-600'
                    }`}>
                      <Package size={16} />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{transaction.product_name}</p>
                      <p className="text-sm text-gray-500">{transaction.product_sku}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-medium ${
                      transaction.transaction_type === 'received' ? 'text-green-600' :
                      transaction.transaction_type === 'sold' ? 'text-blue-600' :
                      'text-red-600'
                    }`}>
                      {transaction.transaction_type === 'received' ? '+' : '-'}{transaction.quantity}
                    </p>
                    <p className="text-xs text-gray-500 capitalize">
                      {transaction.transaction_type} • {formatDate(transaction.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {stats.total_products === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Warehouse size={48} className="text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Welcome to Your Inventory System</h3>
          <p className="text-gray-500 mb-6">Get started by adding your first products, categories, and suppliers.</p>
          <div className="flex justify-center space-x-4">
            <a href="/products" className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
              Add Products
            </a>
            <a href="/categories" className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300 transition-colors">
              Add Categories
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;