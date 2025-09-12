import React, { useState, useEffect, useRef } from 'react';
import BarcodeScannerComponent from 'react-qr-barcode-scanner';
import { X, Camera, CameraOff, AlertCircle, Package, CheckCircle, RefreshCw, Keyboard } from 'lucide-react';

const BarcodeScanner = ({ isOpen, onClose, onProductFound }) => {
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState('');
  const [lastScanned, setLastScanned] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [cameraPermission, setCameraPermission] = useState(null);
  const [showManualInput, setShowManualInput] = useState(false);
  const [manualBarcode, setManualBarcode] = useState('');
  const [scanAttempts, setScanAttempts] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const scannerRef = useRef(null);
  const lastScanTime = useRef(0);

  const BACKEND_URL = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
  const MAX_RETRY_ATTEMPTS = 3;
  const SCAN_COOLDOWN = 2000; // 2 seconds between scans

  useEffect(() => {
    if (isOpen) {
      checkCameraPermission();
      resetScanner();
    } else {
      // Cleanup when closing
      setIsScanning(false);
      resetScanner();
    }
  }, [isOpen]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isScanning) {
        setIsScanning(false);
      }
    };
  }, []);

  const checkCameraPermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      setCameraPermission(true);
      stream.getTracks().forEach(track => track.stop()); // Stop the test stream
    } catch (error) {
      setCameraPermission(false);
      setError('Camera access denied. Please allow camera access and try again.');
    }
  };

  const processBarcode = async (barcode) => {
    if (!barcode || barcode === lastScanned || loading) return;
    
    // Prevent rapid duplicate scans
    const now = Date.now();
    if (now - lastScanTime.current < SCAN_COOLDOWN) return;
    lastScanTime.current = now;
    
    setLastScanned(barcode);
    setLoading(true);
    setError('');
    setSuccess('');
    setScanAttempts(prev => prev + 1);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/barcode/${barcode}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const product = await response.json();
        setSuccess(`✅ Found: ${product.product_name}`);
        setRetryCount(0);
        setScanAttempts(0);
        
        // Call the callback with product data
        if (onProductFound) {
          onProductFound(product);
        }
        
        // Auto-close after success
        setTimeout(() => {
          onClose();
        }, 1500);
        
      } else if (response.status === 404) {
        setError('❌ Product not found in inventory');
        handleScanFailure();
      } else {
        setError('❌ Error looking up product');
        handleScanFailure();
      }
    } catch (error) {
      console.error('Barcode lookup error:', error);
      setError('❌ Network error - please try again');
      handleScanFailure();
    } finally {
      setLoading(false);
    }
  };

  const handleScanFailure = () => {
    setRetryCount(prev => prev + 1);
    if (retryCount >= MAX_RETRY_ATTEMPTS) {
      setError('❌ Multiple scan failures. Try manual entry.');
      setShowManualInput(true);
      setIsScanning(false);
    }
  };

  const handleBarcodeScan = (result) => {
    if (result && typeof result === 'string') {
      processBarcode(result.trim());
    }
  };

  const handleError = (error) => {
    console.error('Barcode scanner error:', error);
    
    // Handle different types of errors
    if (error?.name === 'NotAllowedError') {
      setError('❌ Camera access denied. Please allow camera access.');
      setCameraPermission(false);
    } else if (error?.name === 'NotFoundError') {
      setError('❌ No camera found on this device.');
      setShowManualInput(true);
    } else if (error?.name === 'NotReadableError') {
      setError('❌ Camera is being used by another app.');
      setShowManualInput(true);
    } else {
      setError('❌ Scanner error - trying manual entry');
      handleScanFailure();
    }
    
    setIsScanning(false);
  };

  const resetScanner = () => {
    setError('');
    setSuccess('');
    setLastScanned('');
    setRetryCount(0);
    setScanAttempts(0);
    setShowManualInput(false);
    setManualBarcode('');
    lastScanTime.current = 0;
  };

  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (manualBarcode.trim()) {
      processBarcode(manualBarcode.trim());
      setManualBarcode('');
    }
  };

  const startScanning = () => {
    resetScanner();
    setIsScanning(true);
    // Give a moment for the camera to initialize
    setTimeout(() => {
      if (scannerRef.current) {
        console.log('Scanner started successfully');
      }
    }, 500);
  };

  const stopScanning = () => {
    setIsScanning(false);
    // Clear any pending scans
    lastScanTime.current = 0;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-2 md:p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-auto max-h-screen overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 md:p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 md:w-10 md:h-10 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
              <Package size={16} className="text-white md:hidden" />
              <Package size={20} className="text-white hidden md:block" />
            </div>
            <div>
              <h2 className="text-lg md:text-xl font-bold text-gray-800">Barcode Scanner</h2>
              <p className="text-xs md:text-sm text-gray-600">Scan product barcode for details</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X size={20} className="text-gray-600 md:hidden" />
            <X size={24} className="text-gray-600 hidden md:block" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 md:p-6">
          {/* Camera Permission Check */}
          {cameraPermission === false && (
            <div className="text-center py-6 md:py-8">
              <CameraOff size={40} className="text-gray-400 mx-auto mb-4 md:hidden" />
              <CameraOff size={48} className="text-gray-400 mx-auto mb-4 hidden md:block" />
              <h3 className="text-base md:text-lg font-semibold text-gray-800 mb-2">Camera Access Required</h3>
              <p className="text-sm md:text-base text-gray-600 mb-4">Please allow camera access to scan barcodes</p>
              <button
                onClick={checkCameraPermission}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors text-sm md:text-base"
              >
                Grant Camera Access
              </button>
            </div>
          )}

          {/* Scanner Interface */}
          {cameraPermission === true && (
            <div className="space-y-4">
              {/* Scanner Controls */}
              <div className="flex flex-col sm:flex-row justify-center space-y-2 sm:space-y-0 sm:space-x-4">
                {!isScanning ? (
                  <>
                    <button
                      onClick={startScanning}
                      className="flex items-center justify-center space-x-2 bg-green-500 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:bg-green-600 transition-colors text-sm md:text-base"
                    >
                      <Camera size={16} className="md:hidden" />
                      <Camera size={20} className="hidden md:block" />
                      <span>Start Camera Scan</span>
                    </button>
                    <button
                      onClick={() => setShowManualInput(!showManualInput)}
                      className="flex items-center justify-center space-x-2 bg-blue-500 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:bg-blue-600 transition-colors text-sm md:text-base"
                    >
                      <Keyboard size={16} className="md:hidden" />
                      <Keyboard size={20} className="hidden md:block" />
                      <span>Manual Entry</span>
                    </button>
                  </>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={stopScanning}
                      className="flex items-center space-x-2 bg-red-500 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:bg-red-600 transition-colors text-sm md:text-base"
                    >
                      <CameraOff size={16} className="md:hidden" />
                      <CameraOff size={20} className="hidden md:block" />
                      <span>Stop Scanning</span>
                    </button>
                    {retryCount > 0 && (
                      <button
                        onClick={startScanning}
                        className="flex items-center space-x-2 bg-orange-500 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:bg-orange-600 transition-colors text-sm md:text-base"
                      >
                        <RefreshCw size={16} className="md:hidden" />
                        <RefreshCw size={20} className="hidden md:block" />
                        <span>Retry</span>
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Manual Input */}
              {showManualInput && (
                <div className="space-y-4 p-4 bg-gray-50 rounded-lg border">
                  <h4 className="font-semibold text-gray-800 text-center">Manual Barcode Entry</h4>
                  <form onSubmit={handleManualSubmit} className="space-y-3">
                    <input
                      type="text"
                      value={manualBarcode}
                      onChange={(e) => setManualBarcode(e.target.value)}
                      placeholder="Enter barcode manually"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-lg font-mono"
                      autoFocus
                    />
                    <button
                      type="submit"
                      disabled={!manualBarcode.trim() || loading}
                      className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {loading ? 'Looking up...' : 'Search Product'}
                    </button>
                  </form>
                </div>
              )}

              {/* Scanner Component */}
              {isScanning && (
                <div className="relative">
                  <div className="border-2 border-gray-300 rounded-lg overflow-hidden bg-black">
                    <BarcodeScannerComponent
                      ref={scannerRef}
                      width="100%"
                      height={window.innerWidth > 768 ? 300 : 250}
                      onUpdate={(err, result) => {
                        if (result && result.text) {
                          handleBarcodeScan(result.text);
                        } else if (err && err.name !== 'NotFoundException') {
                          // Only handle actual errors, not "no barcode found" messages
                          handleError(err);
                        }
                      }}
                      facingMode="environment" // Use back camera on mobile
                    />
                  </div>
                  
                  {/* Scanning Overlay */}
                  <div className="absolute inset-0 pointer-events-none">
                    <div className="relative w-full h-full">
                      {/* Scanning Frame */}
                      <div className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 ${window.innerWidth > 768 ? 'w-64 h-64' : 'w-40 h-40'} border-2 border-green-500 rounded-lg`}>
                        <div className="absolute top-0 left-0 w-6 h-6 md:w-8 md:h-8 border-t-4 border-l-4 border-green-500 rounded-tl-lg"></div>
                        <div className="absolute top-0 right-0 w-6 h-6 md:w-8 md:h-8 border-t-4 border-r-4 border-green-500 rounded-tr-lg"></div>
                        <div className="absolute bottom-0 left-0 w-6 h-6 md:w-8 md:h-8 border-b-4 border-l-4 border-green-500 rounded-bl-lg"></div>
                        <div className="absolute bottom-0 right-0 w-6 h-6 md:w-8 md:h-8 border-b-4 border-r-4 border-green-500 rounded-br-lg"></div>
                      </div>
                      
                      {/* Instructions */}
                      <div className="absolute bottom-2 md:bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-70 text-white px-3 md:px-4 py-1 md:py-2 rounded-lg">
                        <p className="text-xs md:text-sm text-center">Position barcode within the frame</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Status Messages */}
              {loading && (
                <div className="flex items-center justify-center space-x-2 p-3 md:p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="animate-spin rounded-full h-4 w-4 md:h-5 md:w-5 border-b-2 border-blue-500"></div>
                  <span className="text-blue-700 text-sm md:text-base">Looking up product...</span>
                </div>
              )}

              {error && (
                <div className="flex items-center space-x-2 p-3 md:p-4 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle size={16} className="text-red-500 md:hidden" />
                  <AlertCircle size={20} className="text-red-500 hidden md:block" />
                  <span className="text-red-700 text-sm md:text-base">{error}</span>
                </div>
              )}

              {success && (
                <div className="flex items-center space-x-2 p-3 md:p-4 bg-green-50 border border-green-200 rounded-lg">
                  <CheckCircle size={16} className="text-green-500 md:hidden" />
                  <CheckCircle size={20} className="text-green-500 hidden md:block" />
                  <span className="text-green-700 text-sm md:text-base">{success}</span>
                </div>
              )}

              {/* Scan Statistics */}
              {scanAttempts > 0 && (
                <div className="text-center text-xs text-gray-500 bg-gray-50 p-2 rounded">
                  Scan attempts: {scanAttempts} | Retries: {retryCount}/{MAX_RETRY_ATTEMPTS}
                </div>
              )}

              {/* Instructions */}
              <div className="text-center text-xs md:text-sm text-gray-600 space-y-2 bg-blue-50 p-3 rounded-lg">
                <p>📱 <strong>Scanning Tips:</strong></p>
                <p>• Use back camera for better results</p>
                <p>• Ensure good lighting</p>
                <p>• Hold steady and close to barcode</p>
                <p>• Try manual entry if camera fails</p>
                {retryCount > 0 && (
                  <p className="text-orange-600 font-medium">• Having trouble? Try the "Manual Entry" option</p>
                )}
              </div>
            </div>
          )}

          {/* Loading Camera */}
          {cameraPermission === null && (
            <div className="text-center py-6 md:py-8">
              <div className="animate-spin rounded-full h-8 w-8 md:h-12 md:w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
              <p className="text-sm md:text-base text-gray-600">Checking camera access...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BarcodeScanner;