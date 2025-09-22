import React, { useState, useEffect } from 'react';
import { 
  QrCode, Package, Search, History, BookOpen, 
  Star, TrendingUp, AlertCircle, Clock, Filter,
  Camera, Smartphone, Zap, Target, Activity
} from 'lucide-react';

const AdvancedBarcodeFeatures = ({ onClose }) => {
  const [activeFeature, setActiveFeature] = useState('bulk-scan');
  const [scanHistory, setScanHistory] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [bulkScanResults, setBulkScanResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Load scan history and favorites from localStorage
  useEffect(() => {
    const savedHistory = JSON.parse(localStorage.getItem('barcode_history') || '[]');
    const savedFavorites = JSON.parse(localStorage.getItem('barcode_favorites') || '[]');
    setScanHistory(savedHistory.slice(0, 20)); // Keep last 20 scans
    setFavorites(savedFavorites);
  }, []);

  // Save to localStorage when data changes
  useEffect(() => {
    localStorage.setItem('barcode_history', JSON.stringify(scanHistory));
  }, [scanHistory]);

  useEffect(() => {
    localStorage.setItem('barcode_favorites', JSON.stringify(favorites));
  }, [favorites]);

  const addToHistory = (barcode, product) => {
    const historyItem = {
      barcode,
      product,
      timestamp: new Date().toISOString(),
      id: Date.now()
    };
    
    setScanHistory(prev => {
      const filtered = prev.filter(item => item.barcode !== barcode);
      return [historyItem, ...filtered].slice(0, 20);
    });
  };

  const addToFavorites = (barcode, product) => {
    if (!favorites.find(fav => fav.barcode === barcode)) {
      const favoriteItem = {
        barcode,
        product,
        addedAt: new Date().toISOString(),
        id: Date.now()
      };
      setFavorites(prev => [favoriteItem, ...prev].slice(0, 50));
    }
  };

  const removeFromFavorites = (barcode) => {
    setFavorites(prev => prev.filter(fav => fav.barcode !== barcode));
  };

  const lookupBarcode = async (barcode) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/barcode/${barcode}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const product = await response.json();
        addToHistory(barcode, product);
        return product;
      }
      return null;
    } catch (error) {
      console.error('Barcode lookup error:', error);
      return null;
    }
  };

  // Bulk Scan Feature
  const BulkScanFeature = () => {
    const [barcodes, setBarcodes] = useState('');
    const [scanning, setScanning] = useState(false);

    const handleBulkScan = async () => {
      const barcodeList = barcodes.split('\n').filter(b => b.trim()).map(b => b.trim());
      if (barcodeList.length === 0) return;

      setScanning(true);
      setBulkScanResults([]);
      
      const results = [];
      for (let i = 0; i < barcodeList.length; i++) {
        const barcode = barcodeList[i];
        setBulkScanResults(prev => [...prev, { 
          barcode, 
          status: 'scanning', 
          product: null, 
          index: i + 1,
          total: barcodeList.length 
        }]);
        
        const product = await lookupBarcode(barcode);
        
        setBulkScanResults(prev => 
          prev.map(item => 
            item.barcode === barcode 
              ? { ...item, status: product ? 'found' : 'not-found', product }
              : item
          )
        );
        
        // Small delay to prevent overwhelming the API
        if (i < barcodeList.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }
      
      setScanning(false);
    };

    return (
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-xl">
          <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center space-x-2">
            <Package className="text-blue-500" />
            <span>Bulk Barcode Scanner</span>
          </h3>
          <p className="text-gray-600 mb-4">
            Scan multiple barcodes at once. Enter one barcode per line.
          </p>
          
          <div className="space-y-4">
            <textarea
              value={barcodes}
              onChange={(e) => setBarcodes(e.target.value)}
              placeholder="Enter barcodes (one per line):&#10;3222471081716&#10;8905039227683&#10;3222474131326"
              className="w-full h-32 p-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500"
              disabled={scanning}
            />
            
            <div className="flex space-x-3">
              <button
                onClick={handleBulkScan}
                disabled={!barcodes.trim() || scanning}
                className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center space-x-2"
              >
                <QrCode size={16} />
                <span>{scanning ? 'Scanning...' : 'Start Bulk Scan'}</span>
              </button>
              
              <button
                onClick={() => setBarcodes('')}
                disabled={scanning}
                className="bg-gray-500 text-white px-4 py-3 rounded-lg hover:bg-gray-600 disabled:opacity-50"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Bulk Scan Results */}
        {bulkScanResults.length > 0 && (
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h4 className="text-lg font-semibold mb-4">Bulk Scan Results</h4>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {bulkScanResults.map((result, index) => (
                <div key={result.barcode} className="flex items-center space-x-3 p-3 border rounded-lg">
                  <div className="text-sm text-gray-500 w-12">
                    {result.index}/{result.total}
                  </div>
                  
                  <div className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                    {result.barcode}
                  </div>
                  
                  <div className="flex-1">
                    {result.status === 'scanning' && (
                      <div className="flex items-center space-x-2 text-blue-600">
                        <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                        <span>Scanning...</span>
                      </div>
                    )}
                    
                    {result.status === 'found' && result.product && (
                      <div className="text-green-600">
                        <div className="font-medium">{result.product.product_name}</div>
                        <div className="text-xs text-gray-500">
                          {result.product.department} • {result.product.supplier}
                        </div>
                      </div>
                    )}
                    
                    {result.status === 'not-found' && (
                      <div className="text-red-600">Product not found</div>
                    )}
                  </div>
                  
                  <div className="w-6">
                    {result.status === 'found' && (
                      <button
                        onClick={() => addToFavorites(result.barcode, result.product)}
                        className="text-yellow-500 hover:text-yellow-600"
                        title="Add to favorites"
                      >
                        <Star size={16} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Scan History Feature
  const ScanHistoryFeature = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-green-50 to-blue-50 p-6 rounded-xl">
        <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center space-x-2">
          <History className="text-green-500" />
          <span>Scan History</span>
        </h3>
        <p className="text-gray-600">
          View your recent barcode scans and quickly access previously scanned products.
        </p>
      </div>

      {scanHistory.length > 0 ? (
        <div className="bg-white rounded-xl shadow-lg">
          <div className="p-4 border-b">
            <h4 className="font-semibold">Recent Scans ({scanHistory.length})</h4>
          </div>
          <div className="divide-y max-h-96 overflow-y-auto">
            {scanHistory.map((item) => (
              <div key={item.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-gray-800">
                      {item.product.product_name}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      <span className="font-mono bg-gray-100 px-2 py-1 rounded mr-2">
                        {item.barcode}
                      </span>
                      <span>{item.product.department}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(item.timestamp).toLocaleString()}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => addToFavorites(item.barcode, item.product)}
                      className="p-2 text-yellow-500 hover:text-yellow-600 hover:bg-yellow-50 rounded-full"
                      title="Add to favorites"
                    >
                      <Star size={16} />
                    </button>
                    
                    <button
                      onClick={() => lookupBarcode(item.barcode)}
                      className="p-2 text-blue-500 hover:text-blue-600 hover:bg-blue-50 rounded-full"
                      title="Scan again"
                    >
                      <Search size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-white p-8 rounded-xl shadow-lg text-center">
          <History size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No scan history yet</p>
          <p className="text-sm text-gray-400">Your recent barcode scans will appear here</p>
        </div>
      )}
    </div>
  );

  // Favorites Feature
  const FavoritesFeature = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-6 rounded-xl">
        <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center space-x-2">
          <Star className="text-yellow-500" />
          <span>Favorite Products</span>
        </h3>
        <p className="text-gray-600">
          Quick access to your frequently scanned products and favorites.
        </p>
      </div>

      {favorites.length > 0 ? (
        <div className="bg-white rounded-xl shadow-lg">
          <div className="p-4 border-b">
            <h4 className="font-semibold">Saved Favorites ({favorites.length})</h4>
          </div>
          <div className="divide-y max-h-96 overflow-y-auto">
            {favorites.map((item) => (
              <div key={item.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-gray-800">
                      {item.product.product_name}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      <span className="font-mono bg-gray-100 px-2 py-1 rounded mr-2">
                        {item.barcode}
                      </span>
                      <span>{item.product.department}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Added {new Date(item.addedAt).toLocaleDateString()}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => lookupBarcode(item.barcode)}
                      className="p-2 text-blue-500 hover:text-blue-600 hover:bg-blue-50 rounded-full"
                      title="Scan again"
                    >
                      <Search size={16} />
                    </button>
                    
                    <button
                      onClick={() => removeFromFavorites(item.barcode)}
                      className="p-2 text-red-500 hover:text-red-600 hover:bg-red-50 rounded-full"
                      title="Remove from favorites"
                    >
                      <AlertCircle size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-white p-8 rounded-xl shadow-lg text-center">
          <Star size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No favorites yet</p>
          <p className="text-sm text-gray-400">Add products to favorites for quick access</p>
        </div>
      )}
    </div>
  );

  // Smart Analytics Feature
  const SmartAnalyticsFeature = () => {
    const [analytics, setAnalytics] = useState({
      totalScans: scanHistory.length,
      uniqueProducts: new Set(scanHistory.map(s => s.barcode)).size,
      topDepartments: {},
      scanFrequency: {}
    });

    useEffect(() => {
      // Calculate analytics from scan history
      const departmentCounts = {};
      const frequencyCounts = {};
      
      scanHistory.forEach(scan => {
        const dept = scan.product.department;
        const barcode = scan.barcode;
        
        departmentCounts[dept] = (departmentCounts[dept] || 0) + 1;
        frequencyCounts[barcode] = (frequencyCounts[barcode] || 0) + 1;
      });
      
      setAnalytics({
        totalScans: scanHistory.length,
        uniqueProducts: new Set(scanHistory.map(s => s.barcode)).size,
        topDepartments: departmentCounts,
        scanFrequency: frequencyCounts
      });
    }, [scanHistory]);

    return (
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-xl">
          <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center space-x-2">
            <TrendingUp className="text-purple-500" />
            <span>Smart Analytics</span>
          </h3>
          <p className="text-gray-600">
            Insights and patterns from your barcode scanning activity.
          </p>
        </div>

        {/* Analytics Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl shadow-lg text-center">
            <div className="text-2xl font-bold text-blue-600">{analytics.totalScans}</div>
            <div className="text-sm text-gray-600">Total Scans</div>
          </div>
          
          <div className="bg-white p-4 rounded-xl shadow-lg text-center">
            <div className="text-2xl font-bold text-green-600">{analytics.uniqueProducts}</div>
            <div className="text-sm text-gray-600">Unique Products</div>
          </div>
          
          <div className="bg-white p-4 rounded-xl shadow-lg text-center">
            <div className="text-2xl font-bold text-purple-600">{favorites.length}</div>
            <div className="text-sm text-gray-600">Favorites</div>
          </div>
          
          <div className="bg-white p-4 rounded-xl shadow-lg text-center">
            <div className="text-2xl font-bold text-orange-600">
              {Object.keys(analytics.topDepartments).length}
            </div>
            <div className="text-sm text-gray-600">Departments</div>
          </div>
        </div>

        {/* Top Departments */}
        {Object.keys(analytics.topDepartments).length > 0 && (
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h4 className="text-lg font-semibold mb-4">Top Scanned Departments</h4>
            <div className="space-y-3">
              {Object.entries(analytics.topDepartments)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([dept, count]) => (
                  <div key={dept} className="flex items-center justify-between">
                    <span className="font-medium">{dept}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${(count / Math.max(...Object.values(analytics.topDepartments))) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600 w-8">{count}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const features = {
    'bulk-scan': { name: 'Bulk Scanner', icon: Package, component: BulkScanFeature },
    'history': { name: 'Scan History', icon: History, component: ScanHistoryFeature },
    'favorites': { name: 'Favorites', icon: Star, component: FavoritesFeature },
    'analytics': { name: 'Smart Analytics', icon: TrendingUp, component: SmartAnalyticsFeature }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-screen overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-500 to-purple-600 text-white">
          <div className="flex items-center space-x-3">
            <Activity className="text-white" size={24} />
            <div>
              <h2 className="text-xl font-bold">Advanced Barcode Features</h2>
              <p className="text-blue-100 text-sm">Enhanced scanning capabilities and analytics</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
          >
            <AlertCircle size={20} />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar Navigation */}
          <div className="w-64 bg-gray-50 border-r p-4 overflow-y-auto">
            <nav className="space-y-2">
              {Object.entries(features).map(([key, feature]) => (
                <button
                  key={key}
                  onClick={() => setActiveFeature(key)}
                  className={`w-full text-left p-3 rounded-lg transition-colors flex items-center space-x-3 ${
                    activeFeature === key
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <feature.icon size={18} />
                  <span>{feature.name}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {features[activeFeature] && React.createElement(features[activeFeature].component)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedBarcodeFeatures;