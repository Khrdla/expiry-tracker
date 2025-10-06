import React, { useState, useEffect } from 'react';
import { Camera, Package, Upload, Trash2, AlertTriangle, CheckCircle, X, Scan } from 'lucide-react';
import BarcodeScanner from './BarcodeScanner';

const InventoryScanning = () => {
  const [loading, setLoading] = useState(false);
  const [scans, setScans] = useState([]);
  const [showScanner, setShowScanner] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Form state
  const [formData, setFormData] = useState({
    zone_type: 'SA',
    zone_number: '',
    barcode: '',
    quantity_scanned: ''
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    loadInventoryScans();
  }, []);

  const loadInventoryScans = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${BACKEND_URL}/api/inventory-scans`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setScans(data.scans || []);
      } else {
        throw new Error('Failed to load inventory scans');
      }
    } catch (error) {
      setError('Failed to load inventory scans');
      console.error('Error loading scans:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBarcodeScanned = (barcode) => {
    setFormData(prev => ({ ...prev, barcode }));
    setShowScanner(false);
    
    // Auto-advance to quantity field after successful scan
    setTimeout(() => {
      document.querySelector('input[placeholder="Enter quantity"]')?.focus();
    }, 300);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.zone_number || !formData.barcode || !formData.quantity_scanned) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const scanRequest = {
        zone_type: formData.zone_type,
        zone_number: parseInt(formData.zone_number),
        barcode: formData.barcode,
        quantity_scanned: parseFloat(formData.quantity_scanned)
      };

      const response = await fetch(`${BACKEND_URL}/api/inventory-scans`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(scanRequest)
      });
      
      if (response.ok) {
        const result = await response.json();
        setSuccess(`✅ Added ${result.quantity_added} units of ${result.item_description}`);
        
        // Reset form for next scan, keeping zone info
        setFormData({
          zone_type: formData.zone_type,
          zone_number: formData.zone_number,
          barcode: '',
          quantity_scanned: ''
        });
        
        // Auto-focus on barcode field for next scan
        setTimeout(() => {
          document.querySelector('input[placeholder="Tap to scan or enter barcode"]')?.focus();
        }, 500);
        
        loadInventoryScans();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add inventory scan');
      }
    } catch (error) {
      setError(error.message);
      console.error('Error adding scan:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${BACKEND_URL}/api/inventory-scans/export`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        // Extract filename from response headers or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        const filename = contentDisposition 
          ? contentDisposition.split('filename=')[1]?.replace(/"/g, '') 
          : `Inventory_Scan_Report_${new Date().toISOString().slice(0,10)}.xlsx`;
        
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        setSuccess('Inventory report exported successfully!');
      } else {
        throw new Error('Failed to export inventory report');
      }
    } catch (error) {
      setError(error.message);
      console.error('Export error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to clear all inventory scans? This action cannot be undone.')) {
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${BACKEND_URL}/api/inventory-scans/clear`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const result = await response.json();
        setSuccess(`Successfully cleared ${result.deleted_count} inventory scans`);
        setScans([]);
      } else {
        throw new Error('Failed to clear inventory scans');
      }
    } catch (error) {
      setError(error.message);
      console.error('Clear error:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value || 0);
  };

  // Calculate summary statistics
  const summary = scans.reduce((acc, scan) => {
    acc.totalItemsScanned += 1;
    acc.totalSaQuantity += scan.qty_scanned_sa || 0;
    acc.totalWhQuantity += scan.qty_scanned_wh || 0;
    acc.totalVarianceValue += scan.variance_value || 0;
    return acc;
  }, {
    totalItemsScanned: 0,
    totalSaQuantity: 0,
    totalWhQuantity: 0,
    totalVarianceValue: 0
  });

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Package className="text-blue-600" />
            Inventory Scanning
          </h1>
          <p className="text-gray-600 mt-2">Scan and track inventory across Selling Area and Warehouse zones</p>
        </div>

        {/* Alert Messages */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-3">
            <AlertTriangle size={20} className="flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Error</p>
              <p className="text-sm">{error}</p>
            </div>
            <button onClick={() => setError('')} className="ml-auto">
              <X size={16} />
            </button>
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-start gap-3">
            <CheckCircle size={20} className="flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Success</p>
              <p className="text-sm">{success}</p>
            </div>
            <button onClick={() => setSuccess('')} className="ml-auto">
              <X size={16} />
            </button>
          </div>
        )}

        {/* Inventory Scanning Form */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-6">Add Inventory Scan</h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Zone Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Zone Type <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.zone_type}
                  onChange={(e) => setFormData({...formData, zone_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="SA">SA (Selling Area)</option>
                  <option value="WH">WH (Warehouse)</option>
                </select>
              </div>

              {/* Zone Number */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Zone Number <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  placeholder="Enter Zone Number"
                  value={formData.zone_number}
                  onChange={(e) => setFormData({...formData, zone_number: e.target.value})}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      // Move to barcode field
                      document.querySelector('input[placeholder="Tap to scan or enter barcode"]')?.focus();
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  required
                />
                {/* Mobile Next Button */}
                <div className="mt-2 sm:hidden">
                  <button
                    type="button"
                    onClick={() => {
                      document.querySelector('input[placeholder="Tap to scan or enter barcode"]')?.focus();
                    }}
                    disabled={!formData.zone_number}
                    className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    Next → Barcode
                  </button>
                </div>
              </div>

              {/* Barcode Scanner */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Barcode <span className="text-red-500">*</span>
                </label>
                <div className="flex gap-2">
                  <input
                    ref={(el) => {
                      if (el) {
                        // Auto-open camera on focus
                        el.addEventListener('focus', () => {
                          if (!formData.barcode) {
                            setShowScanner(true);
                          }
                        });
                      }
                    }}
                    type="text"
                    placeholder="Tap to scan or enter barcode"
                    value={formData.barcode}
                    onChange={(e) => setFormData({...formData, barcode: e.target.value})}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        // Move to quantity field
                        document.querySelector('input[placeholder="Enter quantity"]')?.focus();
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowScanner(true)}
                    className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-1"
                  >
                    <Camera size={16} />
                    Scan
                  </button>
                </div>
                {/* Mobile Enter/Next Button */}
                <div className="mt-2 sm:hidden">
                  <button
                    type="button"
                    onClick={() => {
                      if (formData.barcode) {
                        document.querySelector('input[placeholder="Enter quantity"]')?.focus();
                      } else {
                        setShowScanner(true);
                      }
                    }}
                    className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 flex items-center justify-center gap-2"
                  >
                    {formData.barcode ? 'Next → Quantity' : '📷 Open Camera'}
                  </button>
                </div>
              </div>

              {/* Quantity Scanned */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quantity Scanned <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="Enter quantity"
                  value={formData.quantity_scanned}
                  onChange={(e) => setFormData({...formData, quantity_scanned: e.target.value})}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      // Submit the form if all fields are filled
                      if (formData.zone_number && formData.barcode && formData.quantity_scanned) {
                        handleSubmit(e);
                      }
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  required
                />
                {/* Mobile Submit Button */}
                <div className="mt-2 sm:hidden">
                  <button
                    type="button"
                    onClick={(e) => {
                      if (formData.zone_number && formData.barcode && formData.quantity_scanned) {
                        handleSubmit(e);
                      }
                    }}
                    disabled={!formData.zone_number || !formData.barcode || !formData.quantity_scanned || loading}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:bg-gray-400 flex items-center justify-center gap-2"
                  >
                    {loading ? 'Adding...' : '✓ Add to Inventory'}
                  </button>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
              >
                <Package size={16} />
                {loading ? 'Adding...' : 'Add to Inventory Log'}
              </button>
            </div>
          </form>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Items Scanned</p>
                <p className="text-2xl font-bold text-gray-900">{summary.totalItemsScanned}</p>
              </div>
              <Package className="h-8 w-8 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">SA Quantity</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(summary.totalSaQuantity)}</p>
              </div>
              <Scan className="h-8 w-8 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">WH Quantity</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(summary.totalWhQuantity)}</p>
              </div>
              <Scan className="h-8 w-8 text-orange-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Variance Value</p>
                <p className="text-2xl font-bold text-red-600">${formatCurrency(summary.totalVarianceValue)}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <button
            onClick={handleExport}
            disabled={loading || scans.length === 0}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Upload size={20} />
            Export Inventory Report
          </button>
          
          <button
            onClick={handleClearAll}
            disabled={loading || scans.length === 0}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Trash2 size={20} />
            Clear All Scans
          </button>
        </div>

        {/* Inventory Scans Table */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold">Scanned Inventory ({scans.length})</h2>
          </div>
          
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-600 mt-2">Loading...</p>
            </div>
          ) : scans.length === 0 ? (
            <div className="p-8 text-center">
              <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No inventory scans yet. Start scanning to track your inventory.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item Details</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department/Section</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Zone Info</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantities</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Variance</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date Scanned</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {scans.map((scan) => (
                    <tr key={scan.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{scan.item_number}</div>
                          <div className="text-sm text-gray-500">{scan.description}</div>
                          <div className="text-xs text-gray-400">Barcode: {scan.barcode}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm text-gray-900">{scan.department}</div>
                          <div className="text-sm text-gray-500">{scan.section}</div>
                          <div className="text-xs text-gray-400">{scan.family}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            scan.zone_type === 'SA' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-orange-100 text-orange-800'
                          }`}>
                            {scan.zone_type}
                          </span>
                          <div className="text-sm text-gray-500 mt-1">Zone: {scan.zone_number}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          <div>SA: {formatCurrency(scan.qty_scanned_sa)}</div>
                          <div>WH: {formatCurrency(scan.qty_scanned_wh)}</div>
                          <div className="font-medium">Total: {formatCurrency(scan.total_inventory_scan)}</div>
                          <div className="text-gray-500">System: {formatCurrency(scan.system_stock)}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm ${scan.variance_qty >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          <div>Qty: {scan.variance_qty >= 0 ? '+' : ''}{formatCurrency(scan.variance_qty)}</div>
                          <div>Value: {scan.variance_value >= 0 ? '+$' : '-$'}{formatCurrency(Math.abs(scan.variance_value))}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(scan.date_scanned).toLocaleDateString()}
                        <div className="text-xs">
                          {new Date(scan.date_scanned).toLocaleTimeString()}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Barcode Scanner Modal */}
      {showScanner && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Scan Barcode</h3>
              <button
                onClick={() => setShowScanner(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={24} />
              </button>
            </div>
            <BarcodeScanner
              onScan={handleBarcodeScanned}
              onClose={() => setShowScanner(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryScanning;