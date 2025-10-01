import React, { useState, useEffect, useRef } from 'react';
import { FileText, Download, Upload, Signature, User, Building, Search, Camera, CheckCircle, XCircle, Clock, DollarSign, AlertTriangle, Scan, QrCode } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const EnhancedReturnForm = ({ user }) => {
  const [returnData, setReturnData] = useState({
    // Return Form Metadata (not item-specific)
    supplier: '',
    department: '',
    section: '',
    
    // Enhanced Supervisor Selection (Dropdown)
    selected_supervisor: '', // This will be selected from dropdown
    prepared_by_supervisor: '', // This will be auto-filled from selected_supervisor
    supervisor_signature: '',
    supervisor_timestamp: '',
    
    // Section Manager (Default: Imad Qejji)
    section_manager_name: user?.full_name || user?.username || 'Imad Qejji',
    section_manager_signature: '',
    section_manager_timestamp: '',
    
    // Manual Signatures (With default names)
    department_head_name: 'Idder EL-Fermi', // Default name with dropdown option
    general_manager_name: 'Ahmed Massouni', // Default name
    department_head_signature: '', // Blank for manual signature
    general_manager_signature: '', // Blank for manual signature
    finance_signature: '', // Blank for manual signature + stamp
    
    // Status tracking with enhanced validation
    supervisor_approved: false,
    section_manager_approved: false,
    ready_for_export: false, // Only true when both supervisor selected and section manager approved
    
    // Additional Fields
    return_date: new Date().toISOString().split('T')[0],
    reference_number: `RTN-${Date.now()}`,
    notes: ''
  });

  // Supervisor options for dropdown
  const supervisorOptions = [
    { value: '', label: 'Select Supervisor...' },
    { value: 'Mahmoud Badr', label: 'Mahmoud Badr' },
    { value: 'Abdelhamed Mostafa', label: 'Abdelhamed Mostafa' }
  ];

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [submittedReturnId, setSubmittedReturnId] = useState(null);
  const [showBarcodeScanner, setShowBarcodeScanner] = useState(false);
  const [currencyRates, setCurrencyRates] = useState({});
  const [usdValue, setUsdValue] = useState(0);
  
  // Multi-Item Management State
  const [returnItems, setReturnItems] = useState([]);
  const [currentItem, setCurrentItem] = useState({
    id: null,
    product_code: '',
    product_name: '',
    barcode: '',
    quantity: '',
    purchase_price: '',
    purchase_currency: 'YER',
    total_value: '0.00',
    expiry_date: '',
    reason_for_return: '',
    is_foc: false,
    foc_reason: '',
    supplier: ''
  });
  
  // FOC and Summary Management
  const [focFilterActive, setFocFilterActive] = useState(false);
  const [itemSummary, setItemSummary] = useState({
    totalItems: 0,
    normalItems: 0,
    focItems: 0,
    totalNormalQty: 0,
    totalFocQty: 0,
    totalNormalValue: 0,
    supplierCount: 0
  });

  // Barcode scanning refs
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const scannerActiveRef = useRef(false);

  // Fetch current exchange rates
  useEffect(() => {
    fetchCurrencyRates();
  }, []);

  // Calculate USD value when price or currency changes
  useEffect(() => {
    calculateUSDValue();
  }, [returnData.purchase_price, returnData.purchase_currency, returnData.quantity, returnData.is_foc, currencyRates]);

  const fetchCurrencyRates = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/currency/rates`);
      if (response.ok) {
        const data = await response.json();
        setCurrencyRates(data.exchange_rates);
      }
    } catch (error) {
      console.error('Error fetching currency rates:', error);
    }
  };

  const calculateUSDValue = () => {
    const price = parseFloat(returnData.purchase_price) || 0;
    const quantity = parseFloat(returnData.quantity) || 0;
    const currency = returnData.purchase_currency;
    const rate = currencyRates[currency] || 1;
    
    // FOC Logic: If item is FOC, set price to 0 and total value to 0
    const effectivePrice = returnData.is_foc ? 0 : price;
    const totalOriginal = returnData.is_foc ? 0 : (effectivePrice * quantity);
    const totalUSD = totalOriginal * rate;
    
    setReturnData(prev => ({
      ...prev,
      total_value: totalOriginal.toFixed(2),
      total_value_usd: totalUSD.toFixed(2),
      // Auto-set purchase_price to 0 when FOC is enabled
      purchase_price: returnData.is_foc ? '0' : prev.purchase_price
    }));
    
    setUsdValue(totalUSD);
  };

  // Handle FOC toggle and update pricing logic
  const handleFOCToggle = (checked) => {
    setReturnData(prev => ({
      ...prev,
      is_foc: checked,
      // Clear purchase price when FOC is enabled, restore when disabled
      purchase_price: checked ? '0' : prev.purchase_price,
      // Clear FOC reason when unchecking
      foc_reason: checked ? prev.foc_reason : ''
    }));
    
    // Show appropriate message
    if (checked) {
      setMessage({ 
        type: 'info', 
        text: '🆓 FOC Mode Enabled: Unit price set to 0, item excluded from total cost calculation' 
      });
    } else {
      setMessage({ 
        type: 'info', 
        text: '💰 Normal Pricing Mode: Regular cost calculation applied' 
      });
    }
    
    setTimeout(() => setMessage({ type: '', text: '' }), 3000);
  };

  // Handle supervisor selection and auto-fill prepared_by field
  const handleSupervisorChange = (selectedValue) => {
    setReturnData(prev => ({
      ...prev,
      selected_supervisor: selectedValue,
      prepared_by_supervisor: selectedValue, // Auto-fill prepared by field
      supervisor_approved: false, // Reset approval when supervisor changes
      ready_for_export: false // Reset export readiness
    }));
  };

  // Enhanced search with auto-suggestions
  const performProductSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      setShowSuggestions(false);
      return;
    }

    setLookupLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/search?q=${encodeURIComponent(query)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data || []);
        setShowSuggestions(true);
        
        if (data.length === 0) {
          setMessage({ 
            type: 'warning', 
            text: `⚠️ No products found for "${query}". Please check the barcode or product name.` 
          });
        } else {
          setMessage({ type: '', text: '' });
        }
      } else {
        setMessage({ type: 'error', text: 'Search failed. Please try again.' });
      }
    } catch (error) {
      console.error('Search error:', error);
      setMessage({ type: 'error', text: 'Network error during search.' });
    } finally {
      setLookupLoading(false);
    }
  };

  // Auto-fill form with selected product
  const selectProduct = (product) => {
    console.log('📦 Auto-filling Return Form with Master Data:', product);
    
    setReturnData(prev => ({
      ...prev,
      product_code: product.item_number || product.barcode || '',
      product_name: product.product_name || '',
      barcode: product.barcode || product.item_number || '',
      purchase_price: product.purchase_price ? product.purchase_price.toString() : '',
      purchase_currency: product.purchase_currency || product.currency || 'YER',
      supplier: product.supplier || 'Unknown Supplier',
      department: product.department || '',
      section: product.section || '',
      expiry_date: product.expiry_date ? product.expiry_date.split('T')[0] : '',
    }));

    setSearchQuery(product.product_name || '');
    setShowSuggestions(false);
    setMessage({ 
      type: 'success', 
      text: `✅ Product "${product.product_name}" auto-filled successfully!` 
    });
    
    setTimeout(() => setMessage({ type: '', text: '' }), 3000);
  };

  // Barcode scanning functionality
  const startBarcodeScanner = async () => {
    try {
      setShowBarcodeScanner(true);
      scannerActiveRef.current = true;

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        
        // Start scanning loop
        setTimeout(() => scanForBarcode(), 1000);
      }
    } catch (error) {
      console.error('Camera error:', error);
      setMessage({ 
        type: 'error', 
        text: 'Could not access camera. Please type barcode manually.' 
      });
      setShowBarcodeScanner(false);
    }
  };

  const scanForBarcode = async () => {
    if (!scannerActiveRef.current || !videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0);

      try {
        // Use ZXing library for barcode detection
        if (window.ZXing) {
          const codeReader = new window.ZXing.BrowserBarcodeReader();
          const result = await codeReader.decodeFromCanvas(canvas);
          
          if (result) {
            const barcode = result.text;
            console.log('📷 Barcode detected:', barcode);
            
            stopBarcodeScanner();
            setSearchQuery(barcode);
            performProductSearch(barcode);
            
            setMessage({ 
              type: 'success', 
              text: `📷 Barcode scanned: ${barcode}. Searching...` 
            });
            return;
          }
        }
      } catch (error) {
        // Continue scanning on error
      }
    }

    // Continue scanning
    setTimeout(() => scanForBarcode(), 100);
  };

  const stopBarcodeScanner = () => {
    scannerActiveRef.current = false;
    
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    
    setShowBarcodeScanner(false);
  };

  // Enhanced approval function with validation
  const approveBySupervisor = () => {
    // Validate supervisor selection
    if (!returnData.selected_supervisor) {
      setMessage({ 
        type: 'error', 
        text: '❌ Please select a supervisor from the dropdown first!' 
      });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      return;
    }

    const now = new Date();
    const timestamp = `${now.getDate().toString().padStart(2, '0')}/${(now.getMonth() + 1).toString().padStart(2, '0')}/${now.getFullYear()} - ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    setReturnData(prev => ({
      ...prev,
      supervisor_approved: true,
      supervisor_timestamp: timestamp,
      supervisor_signature: `Digital Signature - ${prev.selected_supervisor}`
    }));
    
    setMessage({ 
      type: 'success', 
      text: `✅ Supervisor approval by ${returnData.selected_supervisor} added with timestamp!` 
    });
    setTimeout(() => setMessage({ type: '', text: '' }), 3000);
  };

  const approveBySectionManager = () => {
    if (!returnData.section_manager_name.trim()) {
      setMessage({ 
        type: 'error', 
        text: '❌ Section Manager field is required!' 
      });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      return;
    }

    const now = new Date();
    const timestamp = `${now.getDate().toString().padStart(2, '0')}/${(now.getMonth() + 1).toString().padStart(2, '0')}/${now.getFullYear()} - ${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    setReturnData(prev => ({
      ...prev,
      section_manager_approved: true,
      section_manager_timestamp: timestamp,
      section_manager_signature: `Digital Signature - ${prev.section_manager_name}`,
      // Ready for export only if supervisor is selected AND section manager approved
      ready_for_export: prev.selected_supervisor && prev.supervisor_approved
    }));
    
    setMessage({ 
      type: 'success', 
      text: '✅ Section Manager approval by Imad Qejji added with timestamp!' 
    });
    setTimeout(() => setMessage({ type: '', text: '' }), 3000);
  };

  // Enhanced export function with strict validation
  const handleExport = async (format) => {
    // Enhanced validation rules
    if (!returnData.selected_supervisor) {
      setMessage({ 
        type: 'error', 
        text: '❌ Please select a supervisor from the dropdown before export!' 
      });
      setTimeout(() => setMessage({ type: '', text: '' }), 5000);
      return;
    }

    if (!returnData.section_manager_name.trim()) {
      setMessage({ 
        type: 'error', 
        text: '❌ Section Manager field must be filled before export!' 
      });
      setTimeout(() => setMessage({ type: '', text: '' }), 5000);
      return;
    }

    if (!returnData.supervisor_approved || !returnData.section_manager_approved) {
      setMessage({ 
        type: 'error', 
        text: '❌ Both Supervisor and Section Manager digital approvals required before export!' 
      });
      setTimeout(() => setMessage({ type: '', text: '' }), 5000);
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // First save the return form
      const saveResponse = await fetch(`${BACKEND_URL}/api/return-forms`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(returnData)
      });

      if (saveResponse.ok) {
        const savedForm = await saveResponse.json();
        const formId = savedForm.id || savedForm._id;

        // Then export with approvals
        const exportResponse = await fetch(`${BACKEND_URL}/api/export/return-form/${formId}?format=${format}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (exportResponse.ok) {
          const blob = await exportResponse.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `return_form_${returnData.reference_number}.${format}`;
          a.click();
          window.URL.revokeObjectURL(url);

          setMessage({ 
            type: 'success', 
            text: `✅ Return form exported as ${format.toUpperCase()} with all approvals and signatures!` 
          });
        } else {
          setMessage({ type: 'error', text: 'Export failed. Please try again.' });
        }
      } else {
        setMessage({ type: 'error', text: 'Failed to save return form before export.' });
      }
    } catch (error) {
      console.error('Export error:', error);
      setMessage({ type: 'error', text: 'Network error during export.' });
    } finally {
      setLoading(false);
      setTimeout(() => setMessage({ type: '', text: '' }), 5000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 pb-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Enhanced Return Form</h1>
            <p className="text-gray-600 mt-1">Create supplier return with barcode scanning & approvals</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Reference: <span className="font-mono">{returnData.reference_number}</span></p>
            <p className="text-sm text-gray-500">Date: {returnData.return_date}</p>
          </div>
        </div>
      </div>

      {/* Message Display */}
      {message.text && (
        <div className={`mb-6 p-4 rounded-lg border-l-4 ${
          message.type === 'success' ? 'bg-green-50 border-green-400 text-green-800' :
          message.type === 'error' ? 'bg-red-50 border-red-400 text-red-800' :
          message.type === 'warning' ? 'bg-yellow-50 border-yellow-400 text-yellow-800' :
          'bg-blue-50 border-blue-400 text-blue-800'
        }`}>
          {message.text}
        </div>
      )}

      {/* Barcode Scanner Modal */}
      {showBarcodeScanner && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Barcode Scanner</h3>
              <button 
                onClick={stopBarcodeScanner}
                className="text-gray-500 hover:text-gray-700"
              >
                <XCircle size={24} />
              </button>
            </div>
            
            <div className="relative">
              <video 
                ref={videoRef}
                className="w-full h-48 bg-black rounded"
                playsInline
                muted
              />
              <canvas 
                ref={canvasRef}
                className="hidden"
              />
              
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-32 h-32 border-2 border-red-500 bg-transparent"></div>
              </div>
            </div>
            
            <p className="text-sm text-gray-600 mt-2 text-center">
              Position barcode within the red square
            </p>
          </div>
        </div>
      )}

      {/* Product Search Section */}
      <div className="mb-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center space-x-2 mb-4">
          <Search className="text-blue-600" size={20} />
          <h3 className="text-lg font-semibold text-blue-800">Product Lookup</h3>
        </div>
        
        <div className="flex space-x-4">
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Search by barcode, product code, or product name..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                performProductSearch(e.target.value);
              }}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            
            {/* Auto-suggestion dropdown */}
            {showSuggestions && searchResults.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
                {searchResults.slice(0, 5).map((product, index) => (
                  <div
                    key={index}
                    onClick={() => selectProduct(product)}
                    className="p-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                  >
                    <div className="font-medium text-gray-800">{product.product_name}</div>
                    <div className="text-sm text-gray-600">
                      {product.barcode || product.item_number} • {product.supplier} • {product.purchase_price} {product.purchase_currency}
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {lookupLoading && (
              <div className="absolute right-3 top-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              </div>
            )}
          </div>
          
          <button
            onClick={startBarcodeScanner}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center space-x-2"
          >
            <Camera size={20} />
            <span>Scan Barcode</span>
          </button>
        </div>
      </div>

      {/* Supervisor Selection Section */}
      <div className="mb-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center space-x-2 mb-4">
          <User className="text-blue-600" size={20} />
          <h3 className="text-lg font-semibold text-blue-800">Supervisor Selection</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Supervisor *</label>
            <select
              value={returnData.selected_supervisor}
              onChange={(e) => handleSupervisorChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            >
              {supervisorOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              This will auto-fill the "Prepared by" field
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Prepared by Supervisor</label>
            <input
              type="text"
              value={returnData.prepared_by_supervisor}
              readOnly
              className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg"
              placeholder="Auto-filled from supervisor selection"
            />
          </div>
        </div>
      </div>

      {/* Product Details Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Product Code</label>
          <input
            type="text"
            value={returnData.product_code}
            onChange={(e) => setReturnData({...returnData, product_code: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Auto-filled from search"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Product Name</label>
          <input
            type="text"
            value={returnData.product_name}
            onChange={(e) => setReturnData({...returnData, product_name: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Auto-filled from search"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Barcode</label>
          <input
            type="text"
            value={returnData.barcode}
            onChange={(e) => setReturnData({...returnData, barcode: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Scanned or manual entry"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Supplier</label>
          <input
            type="text"
            value={returnData.supplier}
            onChange={(e) => setReturnData({...returnData, supplier: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Auto-filled from search"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Quantity</label>
          <input
            type="number"
            min="1"
            value={returnData.quantity}
            onChange={(e) => setReturnData({...returnData, quantity: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Enter quantity to return"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Purchase Price</label>
          <div className="flex space-x-2">
            <input
              type="number"
              step="0.01"
              value={returnData.purchase_price}
              onChange={(e) => setReturnData({...returnData, purchase_price: e.target.value})}
              className={`flex-1 px-3 py-2 border rounded-lg focus:ring-2 ${
                returnData.is_foc 
                  ? 'border-orange-300 bg-orange-50 text-orange-600 cursor-not-allowed' 
                  : 'border-gray-300 focus:ring-blue-500'
              }`}
              placeholder={returnData.is_foc ? "0 (FOC)" : "Unit price"}
              disabled={returnData.is_foc}
            />
            <select
              value={returnData.purchase_currency}
              onChange={(e) => setReturnData({...returnData, purchase_currency: e.target.value})}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="YER">YER</option>
              <option value="SAR">SAR</option>
              <option value="EUR">EUR</option>
              <option value="USD">USD</option>
            </select>
          </div>
        </div>

        {/* FOC (Free of Cost) Toggle */}
        <div className="col-span-2">
          <div className={`p-4 rounded-lg border-2 ${returnData.is_foc ? 'bg-orange-50 border-orange-300' : 'bg-gray-50 border-gray-200'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="foc-toggle"
                  checked={returnData.is_foc}
                  onChange={(e) => handleFOCToggle(e.target.checked)}
                  className="w-5 h-5 text-orange-600 bg-gray-100 border-gray-300 rounded focus:ring-orange-500 focus:ring-2"
                />
                <label htmlFor="foc-toggle" className="ml-3 text-sm font-medium text-gray-700">
                  FOC (Free of Cost)
                </label>
                {returnData.is_foc && (
                  <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                    🆓 FOC
                  </span>
                )}
              </div>
              
              {returnData.is_foc && (
                <div className="text-sm text-orange-600 font-medium">
                  Unit Price: 0 • Total Value: 0
                </div>
              )}
            </div>
            
            {returnData.is_foc && (
              <div className="mt-3">
                <label className="block text-sm font-medium text-orange-700 mb-1">FOC Reason (Optional)</label>
                <input
                  type="text"
                  value={returnData.foc_reason}
                  onChange={(e) => setReturnData({...returnData, foc_reason: e.target.value})}
                  className="w-full px-3 py-2 border border-orange-300 rounded-lg focus:ring-2 focus:ring-orange-500 bg-white"
                  placeholder="e.g., Promotional item, Sample, Expired promotion..."
                />
              </div>
            )}
            
            <div className="text-xs text-gray-500 mt-2">
              {returnData.is_foc 
                ? "💡 FOC items are excluded from total cost calculation but remain visible in reports"
                : "💰 Check this box if the item is Free of Cost (no monetary value)"
              }
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Return Value</label>
          <div className="space-y-3">
            {/* Supplier Currency (Primary) */}
            <div className={`p-3 border rounded-lg ${
              returnData.is_foc 
                ? 'bg-orange-50 border-orange-200' 
                : 'bg-blue-50 border-blue-200'
            }`}>
              <div className={`text-sm font-medium mb-1 ${
                returnData.is_foc ? 'text-orange-800' : 'text-blue-800'
              }`}>
                Total Value (Supplier Currency) {returnData.is_foc && '• FOC'}
              </div>
              <div className={`text-lg font-bold ${
                returnData.is_foc ? 'text-orange-900' : 'text-blue-900'
              }`}>
                {returnData.total_value} {returnData.purchase_currency}
                {returnData.is_foc && (
                  <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                    🆓 FREE
                  </span>
                )}
              </div>
            </div>
            
            {/* USD Equivalent (Secondary) */}
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="text-sm font-medium text-green-800 mb-1">
                USD Equivalent (Reporting)
              </div>
              <div className="text-lg font-bold text-green-900">
                ${returnData.total_value_usd} USD
              </div>
              {currencyRates[returnData.purchase_currency] && (
                <div className="text-xs text-green-600 mt-1">
                  Rate: 1 {returnData.purchase_currency} = {currencyRates[returnData.purchase_currency].toFixed(4)} USD
                </div>
              )}
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Reason for Return</label>
          <select
            value={returnData.reason_for_return}
            onChange={(e) => setReturnData({...returnData, reason_for_return: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select reason</option>
            <option value="expired">Expired</option>
            <option value="damaged">Damaged</option>
            <option value="defective">Defective</option>
            <option value="overstock">Overstock</option>
            <option value="wrong_delivery">Wrong Delivery</option>
            <option value="quality_issue">Quality Issue</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {/* FOC Summary & Controls */}
      <div className="mb-8 p-6 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg border border-orange-200">
        <h3 className="text-lg font-semibold text-orange-800 mb-4 flex items-center">
          🆓 FOC (Free of Cost) Summary
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Current Item FOC Status */}
          <div className="p-4 bg-white rounded-lg border border-orange-200">
            <div className="text-sm font-medium text-orange-700">Current Item</div>
            <div className="text-lg font-bold text-orange-900">
              {returnData.is_foc ? 'FOC Item' : 'Regular Item'}
            </div>
            <div className="text-xs text-orange-600">
              {returnData.is_foc ? 'Excluded from cost total' : 'Included in cost calculation'}
            </div>
          </div>
          
          {/* Item Value */}
          <div className="p-4 bg-white rounded-lg border border-orange-200">
            <div className="text-sm font-medium text-orange-700">Item Value</div>
            <div className="text-lg font-bold text-orange-900">
              {returnData.is_foc ? '0.00' : returnData.total_value} {returnData.purchase_currency}
            </div>
            <div className="text-xs text-orange-600">
              Qty: {returnData.quantity || 0}
            </div>
          </div>
          
          {/* FOC Reason */}
          <div className="p-4 bg-white rounded-lg border border-orange-200">
            <div className="text-sm font-medium text-orange-700">FOC Reason</div>
            <div className="text-sm text-orange-900">
              {returnData.foc_reason || (returnData.is_foc ? 'Not specified' : 'N/A - Regular item')}
            </div>
          </div>
        </div>
        
        {/* Quick Actions */}
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => handleFOCToggle(!returnData.is_foc)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              returnData.is_foc
                ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                : 'bg-orange-600 text-white hover:bg-orange-700'
            }`}
          >
            {returnData.is_foc ? '💰 Convert to Regular Item' : '🆓 Mark as FOC'}
          </button>
          
          {returnData.is_foc && (
            <div className="flex items-center text-sm text-orange-600">
              <span className="ml-2">💡 FOC items appear in reports but don't affect financial totals</span>
            </div>
          )}
        </div>
      </div>

      {/* Approvals & Signatures Section */}
      <div className="mb-8 p-6 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-6 flex items-center">
          <Signature className="mr-2" size={20} />
          Approvals & Signatures Workflow
        </h3>
        
        <div className="space-y-6">
          {/* Supervisor Approval (From Dropdown) */}
          <div className="flex items-center justify-between p-4 bg-white rounded-lg border">
            <div>
              <div className="font-medium text-gray-800">Supervisor Approval</div>
              <div className="text-sm text-gray-600">
                {returnData.selected_supervisor ? 
                  `Selected: ${returnData.selected_supervisor}` : 
                  'No supervisor selected'
                }
              </div>
              {returnData.supervisor_approved && (
                <>
                  <div className="text-sm text-green-600 font-medium mt-1">
                    ✅ Approved: {returnData.supervisor_timestamp}
                  </div>
                  <div className="text-xs text-gray-500">{returnData.supervisor_signature}</div>
                </>
              )}
              {!returnData.selected_supervisor && (
                <div className="text-sm text-red-600 mt-1">
                  ⚠️ Please select a supervisor from the dropdown above
                </div>
              )}
            </div>
            {!returnData.supervisor_approved ? (
              <button
                onClick={approveBySupervisor}
                disabled={!returnData.selected_supervisor}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <CheckCircle size={16} className="inline mr-1" />
                Approve
              </button>
            ) : (
              <div className="text-green-600">
                <CheckCircle size={24} />
              </div>
            )}
          </div>

          {/* Section Manager Approval (Default: Imad Qejji) */}
          <div className="flex items-center justify-between p-4 bg-white rounded-lg border">
            <div className="flex-1 mr-4">
              <div className="font-medium text-gray-800 mb-2">Section Manager (Digital Signature)</div>
              <input
                type="text"
                value={returnData.section_manager_name}
                onChange={(e) => setReturnData({...returnData, section_manager_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-blue-50"
                placeholder="Default: Imad Qejji"
                disabled={returnData.section_manager_approved}
              />
              <div className="text-xs text-blue-600 mt-1">
                ✅ Digital signature allowed for Section Manager
              </div>
              {returnData.section_manager_approved && (
                <>
                  <div className="text-sm text-green-600 font-medium mt-2">
                    ✅ Approved: {returnData.section_manager_timestamp}
                  </div>
                  <div className="text-xs text-gray-500">{returnData.section_manager_signature}</div>
                </>
              )}
            </div>
            {!returnData.section_manager_approved ? (
              <button
                onClick={approveBySectionManager}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <CheckCircle size={16} className="inline mr-1" />
                Approve
              </button>
            ) : (
              <div className="text-green-600">
                <CheckCircle size={24} />
              </div>
            )}
          </div>

          {/* Manual Signature Lines (For After-Printing) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <div className="font-medium text-orange-800 flex items-center">
                <AlertTriangle size={16} className="mr-2" />
                Department Head
              </div>
              <div className="mt-3">
                <label className="block text-sm font-medium text-orange-700 mb-2">Select Department Head:</label>
                <select
                  value={returnData.department_head_name}
                  onChange={(e) => setReturnData({...returnData, department_head_name: e.target.value})}
                  className="w-full px-3 py-2 border border-orange-300 bg-white rounded-lg focus:ring-2 focus:ring-orange-500"
                >
                  <option value="Idder EL-Fermi">Idder EL-Fermi</option>
                </select>
              </div>
              <div className="text-sm text-orange-700 mt-3">
                ⏳ Manual signature required after printing
              </div>
              <div className="mt-3 border-b-2 border-dashed border-orange-300 w-full h-8"></div>
              <div className="text-xs text-orange-600 mt-1">Signature & Date Line</div>
            </div>

            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="font-medium text-purple-800 flex items-center">
                <AlertTriangle size={16} className="mr-2" />
                General Manager
              </div>
              <div className="mt-3">
                <label className="block text-sm font-medium text-purple-700 mb-2">General Manager:</label>
                <input
                  type="text"
                  value={returnData.general_manager_name}
                  onChange={(e) => setReturnData({...returnData, general_manager_name: e.target.value})}
                  className="w-full px-3 py-2 border border-purple-300 bg-purple-50 rounded-lg focus:ring-2 focus:ring-purple-500"
                  placeholder="Ahmed Massouni"
                  readOnly
                />
              </div>
              <div className="text-sm text-purple-700 mt-3">
                ⏳ Manual signature required after printing
              </div>
              <div className="mt-3 border-b-2 border-dashed border-purple-300 w-full h-8"></div>
              <div className="text-xs text-purple-600 mt-1">Signature & Date Line</div>
            </div>
            
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="font-medium text-red-800 flex items-center">
                <AlertTriangle size={16} className="mr-2" />
                Finance Department
              </div>
              <div className="text-sm text-red-700 mt-3">
                ⏳ Manual signature + official stamp after printing
              </div>
              <div className="text-xs text-red-600 mt-2 p-2 bg-red-100 rounded">
                Requires both signature AND official stamp after printing
              </div>
              <div className="mt-3 border-b-2 border-dashed border-red-300 w-full h-8"></div>
              <div className="text-xs text-red-600 mt-1">Signature, Stamp & Date Line</div>
            </div>
          </div>
        </div>
      </div>

      {/* Export Controls */}
      <div className="flex space-x-4 justify-between items-center">
        <div className="flex items-center space-x-2">
          {returnData.ready_for_export ? (
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle size={20} />
              <span className="font-medium">Ready for Export</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-yellow-600">
              <Clock size={20} />
              <span>Pending Approvals</span>
            </div>
          )}
        </div>

        <div className="flex space-x-3">
          <button
            onClick={() => handleExport('pdf')}
            disabled={!returnData.ready_for_export || loading}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <FileText size={16} />
            <span>{loading ? 'Exporting...' : 'Export PDF'}</span>
          </button>
          
          <button
            onClick={() => handleExport('excel')}
            disabled={!returnData.ready_for_export || loading}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Download size={16} />
            <span>{loading ? 'Exporting...' : 'Export Excel'}</span>
          </button>
        </div>
      </div>

      {/* Enhanced Export Requirements Notice */}
      <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg">
        <div className="flex items-start space-x-2">
          <AlertTriangle className="text-blue-600 mt-1" size={16} />
          <div>
            <div className="font-medium text-blue-800">Enhanced Export Requirements</div>
            <div className="text-sm text-blue-700 mt-2 space-y-1">
              <div className="flex items-center">
                <CheckCircle size={14} className="text-green-600 mr-1" />
                <strong>Required for Export:</strong>
              </div>
              <div className="ml-4 space-y-1">
                • Supervisor selected from dropdown (Mahmoud Badr or Abdelhamed Mostafa)
                <br />
                • Section Manager field filled (Default: Imad Qejji)
                <br />
                • Both digital approvals completed
              </div>
              <div className="flex items-center mt-2">
                <Clock size={14} className="text-orange-600 mr-1" />
                <strong>After Export:</strong>
              </div>
              <div className="ml-4">
                • Department Head (Idder EL-Fermi): Manual signature on printed form
                <br />
                • General Manager (Ahmed Massouni): Manual signature on printed form
                <br />
                • Finance: Manual signature + official stamp on printed form
              </div>
              <div className="mt-2 p-2 bg-blue-100 rounded text-xs">
                📊 <strong>Currency Display:</strong> Shows supplier currency + USD equivalent for reporting
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedReturnForm;