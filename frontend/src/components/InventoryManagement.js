import React, { useState, useEffect } from "react";
import axios from "axios";
import { 
  Warehouse, 
  Plus, 
  Edit, 
  Package,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Search,
  Filter,
  AlertCircle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const InventoryManagement = () => {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  const [showStockModal, setShowStockModal] = useState(false);
  const [showInventoryModal, setShowInventoryModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [stockTransaction, setStockTransaction] = useState({
    transaction_type: "received",
    quantity: "",
    reason: "",
    reference: ""
  });
  const [inventoryUpdate, setInventoryUpdate] = useState({
    min_stock: "",
    max_stock: "",
    location: ""
  });

  useEffect(() => {
    fetchInventory();
  }, [showLowStockOnly]);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (showLowStockOnly) params.append('low_stock_only', 'true');
      
      const response = await axios.get(`${API}/inventory?${params}`);
      setInventory(response.data);
      setError(null);
    } catch (err) {
      setError("Failed to fetch inventory");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStockTransaction = async (e) => {
    e.preventDefault();
    try {
      const transactionData = {
        product_id: selectedProduct.product_id,
        transaction_type: stockTransaction.transaction_type,
        quantity: parseInt(stockTransaction.quantity),
        reason: stockTransaction.reason,
        reference: stockTransaction.reference
      };

      await axios.post(`${API}/stock-transactions`, transactionData);
      
      setShowStockModal(false);
      setSelectedProduct(null);
      resetStockForm();
      fetchInventory();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create stock transaction");
    }
  };

  const handleInventoryUpdate = async (e) => {
    e.preventDefault();
    try {
      const updateData = {
        min_stock: parseInt(inventoryUpdate.min_stock),
        max_stock: parseInt(inventoryUpdate.max_stock),
        location: inventoryUpdate.location
      };

      await axios.put(`${API}/inventory/${selectedProduct.product_id}`, updateData);
      
      setShowInventoryModal(false);
      setSelectedProduct(null);
      resetInventoryForm();
      fetchInventory();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update inventory settings");
    }
  };

  const openStockModal = (item) => {
    setSelectedProduct(item);
    resetStockForm();
    setShowStockModal(true);
  };

  const openInventoryModal = (item) => {
    setSelectedProduct(item);
    setInventoryUpdate({
      min_stock: item.min_stock?.toString() || "",
      max_stock: item.max_stock?.toString() || "",
      location: item.location || ""
    });
    setShowInventoryModal(true);
  };

  const resetStockForm = () => {
    setStockTransaction({
      transaction_type: "received",
      quantity: "",
      reason: "",
      reference: ""
    });
  };

  const resetInventoryForm = () => {
    setInventoryUpdate({
      min_stock: "",
      max_stock: "",
      location: ""
    });
  };

  const getStockStatusBadge = (currentStock, minStock) => {
    if (currentStock === 0) {
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">Out of Stock</span>;
    } else if (currentStock < minStock) {
      return <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Low Stock</span>;
    }
    return <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">In Stock</span>;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inventory Management</h1>
          <p className="text-gray-600 mt-1">Monitor and manage your stock levels</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowLowStockOnly(!showLowStockOnly)}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
              showLowStockOnly 
                ? "bg-red-600 text-white" 
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            <AlertTriangle size={16} />
            <span>Low Stock Only</span>
          </button>
          <button
            onClick={fetchInventory}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Package size={16} />
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

      {/* Inventory Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Stock</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock Levels</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {inventory.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                            <Warehouse className="text-indigo-600" size={20} />
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{item.product_name}</div>
                          <div className="text-sm text-gray-500">SKU: {item.product_sku}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-lg font-semibold text-gray-900">
                        {item.current_stock || 0}
                      </div>
                      <div className="text-sm text-gray-500">units</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        <div>Min: {item.min_stock || 0}</div>
                        <div>Max: {item.max_stock || 0}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {item.location || "Not specified"}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        <div>Cost: {formatCurrency((item.current_stock || 0) * (item.cost_price || 0))}</div>
                        <div className="text-gray-500">Retail: {formatCurrency((item.current_stock || 0) * (item.unit_price || 0))}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStockStatusBadge(item.current_stock || 0, item.min_stock || 10)}
                      {item.is_low_stock && (
                        <div className="mt-1">
                          <AlertTriangle className="text-red-500 inline mr-1" size={14} />
                          <span className="text-xs text-red-600">Reorder needed</span>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => openStockModal(item)}
                          className="text-blue-600 hover:text-blue-900 flex items-center"
                          title="Update Stock"
                        >
                          <Package size={16} />
                        </button>
                        <button
                          onClick={() => openInventoryModal(item)}
                          className="text-green-600 hover:text-green-900 flex items-center"
                          title="Edit Settings"
                        >
                          <Edit size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {inventory.length === 0 && !loading && (
              <div className="text-center py-12">
                <Warehouse size={48} className="text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {showLowStockOnly ? "No low stock items found" : "No inventory found"}
                </h3>
                <p className="text-gray-500">
                  {showLowStockOnly 
                    ? "All your products are adequately stocked." 
                    : "Add some products to start managing inventory."
                  }
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Stock Transaction Modal */}
      {showStockModal && selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Update Stock</h2>
              <p className="text-sm text-gray-600 mt-1">{selectedProduct.product_name}</p>
              <p className="text-sm text-gray-500">Current Stock: {selectedProduct.current_stock || 0} units</p>
            </div>
            <form onSubmit={handleStockTransaction} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Transaction Type *</label>
                <select
                  value={stockTransaction.transaction_type}
                  onChange={(e) => setStockTransaction({...stockTransaction, transaction_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="received">Stock Received (+)</option>
                  <option value="sold">Stock Sold (-)</option>
                  <option value="adjusted">Stock Adjustment (=)</option>
                  <option value="damaged">Damaged Stock (-)</option>
                  <option value="expired">Expired Stock (-)</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quantity *
                  {stockTransaction.transaction_type === 'adjusted' && (
                    <span className="text-xs text-gray-500 ml-1">(new total stock)</span>
                  )}
                </label>
                <input
                  type="number"
                  required
                  min="0"
                  value={stockTransaction.quantity}
                  onChange={(e) => setStockTransaction({...stockTransaction, quantity: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter quantity"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Reason</label>
                <input
                  type="text"
                  value={stockTransaction.reason}
                  onChange={(e) => setStockTransaction({...stockTransaction, reason: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter reason for stock change"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Reference</label>
                <input
                  type="text"
                  value={stockTransaction.reference}
                  onChange={(e) => setStockTransaction({...stockTransaction, reference: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Purchase order, receipt number, etc."
                />
              </div>

              <div className="flex justify-end space-x-4 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowStockModal(false);
                    setSelectedProduct(null);
                    resetStockForm();
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Update Stock
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inventory Settings Modal */}
      {showInventoryModal && selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Inventory Settings</h2>
              <p className="text-sm text-gray-600 mt-1">{selectedProduct.product_name}</p>
            </div>
            <form onSubmit={handleInventoryUpdate} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Minimum Stock *</label>
                  <input
                    type="number"
                    required
                    min="0"
                    value={inventoryUpdate.min_stock}
                    onChange={(e) => setInventoryUpdate({...inventoryUpdate, min_stock: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Min stock"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Maximum Stock *</label>
                  <input
                    type="number"
                    required
                    min="0"
                    value={inventoryUpdate.max_stock}
                    onChange={(e) => setInventoryUpdate({...inventoryUpdate, max_stock: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Max stock"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Storage Location</label>
                <input
                  type="text"
                  value={inventoryUpdate.location}
                  onChange={(e) => setInventoryUpdate({...inventoryUpdate, location: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Warehouse location, aisle, shelf, etc."
                />
              </div>

              <div className="flex justify-end space-x-4 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowInventoryModal(false);
                    setSelectedProduct(null);
                    resetInventoryForm();
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Update Settings
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inventory Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100">
              <Package className="text-blue-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Items</p>
              <p className="text-2xl font-bold text-gray-900">{inventory.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-red-100">
              <AlertTriangle className="text-red-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Low Stock</p>
              <p className="text-2xl font-bold text-gray-900">
                {inventory.filter(item => item.is_low_stock).length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-yellow-100">
              <Package className="text-yellow-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Out of Stock</p>
              <p className="text-2xl font-bold text-gray-900">
                {inventory.filter(item => (item.current_stock || 0) === 0).length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100">
              <TrendingUp className="text-green-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Value</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(
                  inventory.reduce((total, item) => 
                    total + ((item.current_stock || 0) * (item.cost_price || 0)), 0
                  )
                )}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InventoryManagement;