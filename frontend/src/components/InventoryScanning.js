import React, { useState, useEffect, useRef } from 'react';
import { Camera, Package, Upload, Trash2, AlertTriangle, CheckCircle, X, Scan, Volume2 } from 'lucide-react';
import SimpleMobileBarcodeScanner from './SimpleMobileBarcodeScanner';

const InventoryScanning = () => {
  const [loading, setLoading] = useState(false);
  const [scans, setScans] = useState([]);
  const [showScanner, setShowScanner] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [scanFlash, setScanFlash] = useState(false);
  const [currentZoneScans, setCurrentZoneScans] = useState(0);
  const [zoneSet, setZoneSet] = useState(false);
  
  // Form state - focus on continuous scanning
  const [zoneData, setZoneData] = useState({
    zone_type: 'SA',
    zone_number: ''
  });
  
  const [scanData, setScanData] = useState({
    barcode: '',
    quantity_scanned: ''
  });

  // Refs for field focus management
  const barcodeRef = useRef(null);
  const quantityRef = useRef(null);
  const zoneNumberRef = useRef(null);
  
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    loadInventoryScans();
    // Auto-focus zone number on initial load
    if (!zoneSet && zoneNumberRef.current) {
      zoneNumberRef.current.focus();
    }
  }, []);

  // Update current zone scan count when scans change
  useEffect(() => {
    if (zoneSet && zoneData.zone_number) {
      const currentZoneCount = scans.filter(scan => 
        scan.zone_type === zoneData.zone_type && 
        scan.zone_number === parseInt(zoneData.zone_number)
      ).length;
      setCurrentZoneScans(currentZoneCount);
    }
  }, [scans, zoneData, zoneSet]);

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

  // Audio and visual feedback functions
  const playBeepSound = () => {
    try {
      // Create a simple beep sound
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
      console.log('Audio not available:', error);
    }
  };

  const showScanFlash = () => {
    setScanFlash(true);
    setTimeout(() => setScanFlash(false), 200);
  };

  const handleBarcodeScanned = (barcode) => {
    setScanData(prev => ({ ...prev, barcode }));
    setShowScanner(false);
    
    // Play beep and show flash
    playBeepSound();
    showScanFlash();
    
    // Auto-advance to quantity field after successful scan
    setTimeout(() => {
      if (quantityRef.current) {
        quantityRef.current.focus();
      }
    }, 300);
  };

  const handleZoneNumberSet = () => {
    if (zoneData.zone_number) {
      setZoneSet(true);
      // Auto-focus barcode field for first scan
      setTimeout(() => {
        if (barcodeRef.current) {
          barcodeRef.current.focus();
        }
      }, 200);
    }
  };

  const handleQuantitySubmit = async () => {
    if (!zoneData.zone_number || !scanData.barcode || !scanData.quantity_scanned) {
      setError('Please complete barcode and quantity');
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const scanRequest = {
        zone_type: zoneData.zone_type,
        zone_number: parseInt(zoneData.zone_number),
        barcode: scanData.barcode,
        quantity_scanned: parseFloat(scanData.quantity_scanned)
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
        
        // Show brief success message with next action indicator
        setSuccess(`✅ ${result.item_description} - ${result.quantity_added} units | 📷 Opening camera...`);
        setTimeout(() => setSuccess(''), 3000);
        
        // Reset scan data for next item (keep zone data)
        setScanData({
          barcode: '',
          quantity_scanned: ''
        });
        
        // Automatically open camera scanner for next scan (continuous workflow)
        setTimeout(() => {
          setShowScanner(true);
        }, 300);
        
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

        {/* Zone Setup Section */}
        {!zoneSet && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4 text-blue-900">📍 Set Up Scanning Zone</h2>
            <p className="text-blue-700 mb-6">Choose your zone to begin continuous scanning. Zone will remain active until you change it.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {/* Zone Type */}
              <div>
                <label className="block text-sm font-medium text-blue-900 mb-2">Zone Type</label>
                <select
                  value={zoneData.zone_type}
                  onChange={(e) => setZoneData({...zoneData, zone_type: e.target.value})}
                  className="w-full px-4 py-3 text-lg border border-blue-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="SA">🏪 SA (Selling Area)</option>
                  <option value="WH">📦 WH (Warehouse)</option>
                </select>
              </div>

              {/* Zone Number */}
              <div>
                <label className="block text-sm font-medium text-blue-900 mb-2">Zone Number</label>
                <input
                  ref={zoneNumberRef}
                  type="number"
                  placeholder="e.g., 01, 02, 03..."
                  value={zoneData.zone_number}
                  onChange={(e) => setZoneData({...zoneData, zone_number: e.target.value})}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleZoneNumberSet();
                    }
                  }}
                  className="w-full px-4 py-3 text-lg border border-blue-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <button
              onClick={handleZoneNumberSet}
              disabled={!zoneData.zone_number}
              className="w-full px-6 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
            >
              <Scan size={20} />
              Start Scanning Zone {zoneData.zone_type}{zoneData.zone_number ? zoneData.zone_number.padStart(2, '0') : ''}
            </button>
          </div>
        )}

        {/* Continuous Scanning Section */}
        {zoneSet && (
          <div className={`bg-white rounded-lg shadow-lg mb-8 transition-all duration-200 ${scanFlash ? 'bg-green-100 shadow-green-200' : ''}`}>
            {/* Zone Header with Live Counter */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 rounded-t-lg">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-semibold">🎯 Zone: {zoneData.zone_type}{zoneData.zone_number.padStart(2, '0')}</h2>
                  <p className="text-blue-100">Continuous Scanning Active</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold">{currentZoneScans}</div>
                  <div className="text-sm text-blue-100">SKUs Scanned</div>
                </div>
              </div>
              <button
                onClick={() => {
                  setZoneSet(false);
                  setScanData({barcode: '', quantity_scanned: ''});
                }}
                className="mt-2 px-3 py-1 bg-blue-500 hover:bg-blue-400 text-white text-sm rounded"
              >
                📝 Change Zone
              </button>
            </div>

            {/* Scanning Form */}
            <div className="p-6">
              {/* Barcode Input */}
              <div className="mb-6">
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  📷 Scan Barcode
                </label>
                
                {/* Mobile-First Barcode Input */}
                <div className="space-y-3">
                  <input
                    ref={barcodeRef}
                    type="text"
                    placeholder="Enter barcode or tap camera button"
                    value={scanData.barcode}
                    onChange={(e) => setScanData({...scanData, barcode: e.target.value})}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && scanData.barcode) {
                        e.preventDefault();
                        if (quantityRef.current) {
                          quantityRef.current.focus();
                        }
                      }
                    }}
                    className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />

                  {/* Camera Scanner Buttons */}
                  <div className="grid grid-cols-1 gap-3">
                    <button
                      type="button"
                      onClick={() => setShowScanner(true)}
                      className="w-full px-6 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 flex items-center justify-center gap-3"
                    >
                      📷 Open Camera Scanner
                    </button>
                    
                    {/* Quick Native Scanner Button for iOS/Android */}
                    <button
                      type="button"
                      onClick={() => {
                        // For mobile devices, suggest using device camera
                        if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
                          alert('💡 Tip: Use your device\'s camera app to scan the barcode, then enter the number in the field above.');
                        } else {
                          setShowScanner(true);
                        }
                      }}
                      className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
                    >
                      📱 Use Device Camera
                    </button>
                  </div>
                </div>

                {/* Barcode Format Help */}
                <div className="mt-3 bg-gray-50 rounded-lg p-3 text-sm text-gray-600">
                  <div className="font-medium mb-1">💡 Scanning Tips:</div>
                  <div className="space-y-1">
                    <div>• Tap "Open Camera Scanner" for built-in scanner</div>
                    <div>• Or use "Device Camera" → scan → enter number manually</div>
                    <div>• Barcode usually 8-13 digits (e.g., 1234567890123)</div>
                  </div>
                </div>
              </div>

              {/* Quantity Input */}
              <div className="mb-6">
                <label className="block text-lg font-medium text-gray-700 mb-3">
                  📊 Quantity Scanned
                </label>
                <input
                  ref={quantityRef}
                  type="number"
                  step="0.01"
                  placeholder="Enter quantity"
                  value={scanData.quantity_scanned}
                  onChange={(e) => setScanData({...scanData, quantity_scanned: e.target.value})}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && scanData.quantity_scanned) {
                      e.preventDefault();
                      handleQuantitySubmit();
                    }
                  }}
                  className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-lg focus:ring-green-500 focus:border-green-500"
                  disabled={!scanData.barcode}
                />

                {/* Submit Button */}
                <button
                  onClick={handleQuantitySubmit}
                  disabled={loading || !scanData.barcode || !scanData.quantity_scanned}
                  className="mt-3 w-full px-6 py-4 bg-green-600 text-white text-lg font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      Adding...
                    </>
                  ) : (
                    <>
                      <CheckCircle size={20} />
                      ✓ Add → 📷 Auto Scan Next
                    </>
                  )}
                </button>
              </div>

              {/* Quick Instructions */}
              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
                <div className="font-medium mb-2">📋 Scanning Workflow:</div>
                <div className="space-y-1">
                  <div>1. Tap barcode field → camera opens automatically</div>
                  <div>2. Scan barcode → beep + flash → auto-advance to quantity</div>
                  <div>3. Enter quantity → press Enter or tap "Add & Continue"</div>
                  <div>4. Form resets → ready for next scan in same zone</div>
                </div>
              </div>
            </div>
          </div>
        )}

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
        <SimpleMobileBarcodeScanner
          onScan={handleBarcodeScanned}
          onClose={() => setShowScanner(false)}
        />
      )}
    </div>
  );
};

export default InventoryScanning;