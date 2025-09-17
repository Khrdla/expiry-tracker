import React, { useState, useEffect, useRef } from 'react';
import { Html5QrcodeScanner, Html5QrcodeScanType } from 'html5-qrcode';
import { X, Camera, CameraOff, AlertCircle, Package, CheckCircle, RefreshCw, Keyboard, Zap } from 'lucide-react';

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
  const [scanStats, setScanStats] = useState({ successful: 0, failed: 0 });
  
  const scannerRef = useRef(null);
  const scannerInstanceRef = useRef(null);
  const lastScanTime = useRef(0);
  const isMountedRef = useRef(true);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const MAX_RETRY_ATTEMPTS = 2;
  const SCAN_COOLDOWN = 150; // Reduced to 150ms for sub-second response

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (isOpen) {
      console.log('🚀 Scanner modal opened, initializing camera...');
      initializeCamera();
      resetScanner();
    } else {
      console.log('🔒 Scanner modal closed, cleaning up...');
      cleanup();
    }
  }, [isOpen]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  const initializeCamera = async () => {
    try {
      console.log('🔍 Initializing camera...');
      
      // Check if mediaDevices API is available first
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera API not available in this browser');
      }
      
      // Try with basic constraints first
      let constraints = { video: true };
      
      try {
        // Try enhanced constraints for better quality
        constraints = {
          video: {
            facingMode: 'environment', // Prefer back camera
            width: { ideal: 1280, min: 640 },
            height: { ideal: 720, min: 480 }
          }
        };
        
        console.log('🔍 Requesting camera with enhanced constraints:', constraints);
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        
        setCameraPermission(true);
        console.log('✅ Camera access granted with enhanced constraints');
        
        // Stop the test stream
        stream.getTracks().forEach(track => track.stop());
        
      } catch (enhancedError) {
        console.warn('⚠️ Enhanced camera constraints failed, trying basic constraints:', enhancedError);
        
        // Fallback to basic constraints
        constraints = { video: true };
        console.log('🔍 Requesting camera with basic constraints:', constraints);
        
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        setCameraPermission(true);
        console.log('✅ Camera access granted with basic constraints');
        
        // Stop the test stream
        stream.getTracks().forEach(track => track.stop());
      }
      
    } catch (error) {
      console.error('❌ Camera initialization error:', error);
      setCameraPermission(false);
      
      let errorMessage = '❌ Camera access denied. ';
      
      if (error.name === 'NotAllowedError') {
        errorMessage += 'Please allow camera access and try again.';
      } else if (error.name === 'NotFoundError') {
        errorMessage += 'No camera found on this device.';
      } else if (error.name === 'NotReadableError') {
        errorMessage += 'Camera is being used by another app. Close other camera apps and try again.';
      } else if (error.name === 'OverconstrainedError') {
        errorMessage += 'Camera constraints not supported. Try refreshing the page.';
      } else if (error.message.includes('not available')) {
        errorMessage += 'Camera API not supported in this browser. Please use Chrome, Firefox, or Safari.';
      } else {
        errorMessage += `${error.message || 'Unknown camera error'}`;
      }
      
      setError(errorMessage);
    }
  };

  const startScanning = async () => {
    if (!isMountedRef.current) return;
    
    try {
      resetScanner();
      setIsScanning(true);

      // Initialize Html5QrcodeScanner with optimized detection configuration
      const config = {
        fps: 5, // Lower FPS for better detection accuracy
        qrbox: function(viewfinderWidth, viewfinderHeight) {
          // Dynamic scan area - make it larger and more flexible
          const minEdgePercentage = 0.7; // 70% of the smaller dimension
          const minEdgeSize = Math.min(viewfinderWidth, viewfinderHeight);
          const calculatedSize = Math.floor(minEdgeSize * minEdgePercentage);
          return {
            width: Math.min(calculatedSize, 400),
            height: Math.min(calculatedSize * 0.6, 240) // Rectangular for barcodes
          };
        },
        aspectRatio: 1.777778, // 16:9 aspect ratio
        disableFlip: false,
        experimentalFeatures: {
          useBarCodeDetectorIfSupported: true
        },
        supportedScanTypes: [
          Html5QrcodeScanType.SCAN_TYPE_CAMERA
        ],
        showTorchButtonIfSupported: true,
        showZoomSliderIfSupported: true,
        defaultZoomValueIfSupported: 2,
        videoConstraints: {
          facingMode: "environment", // Back camera preferred
          width: { ideal: 1920, min: 640 },
          height: { ideal: 1080, min: 480 },
          frameRate: { ideal: 30, min: 10 },
          focusMode: "continuous",
          advanced: [
            { focusMode: "continuous" },
            { zoom: 1.5 }
          ]
        }
      };
      
      console.log('🔍 Starting scanner with config:', config);

      if (scannerInstanceRef.current) {
        await cleanup();
      }

      // Dynamic import to avoid build issues
      const { Html5QrcodeScanner } = await import('html5-qrcode');
      
      console.log('✅ Html5QrcodeScanner imported successfully');
      
      scannerInstanceRef.current = new Html5QrcodeScanner(
        "qr-reader",
        config,
        true // verbose logging enabled for debugging
      );

      console.log('✅ Html5QrcodeScanner instance created');

      scannerInstanceRef.current.render(
        (decodedText) => {
          console.log('🎯 SUCCESS: Barcode detected:', decodedText);
          if (isMountedRef.current) {
            handleSuccessfulScan(decodedText);
          }
        },
        (errorMessage) => {
          // Filter out common scanning messages that aren't real errors
          const ignoredMessages = [
            'No MultiFormat Readers',
            'NotFoundException', 
            'No QR code found',
            'QR code parse error', 
            'Unable to detect a valid barcode',
            'No barcode or QR code detected'
          ];
          
          const isIgnoredMessage = ignoredMessages.some(msg => errorMessage.includes(msg));
          
          if (!isIgnoredMessage) {
            console.warn('⚠️ Scan error:', errorMessage);
          } else {
            // Log scanning attempts for debugging (but less frequently)
            if (Math.random() < 0.01) { // Log only 1% of attempts to avoid console spam
              console.log('🔍 Scanning...', errorMessage);
            }
          }
        }
      );
      
      console.log('✅ Scanner render initiated');

    } catch (error) {
      console.error('❌ Start scanning error:', error);
      console.error('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      });
      
      if (error.message.includes('Cannot access camera')) {
        setError('❌ Cannot access camera. Please grant camera permission and try again.');
        setCameraPermission(false);
      } else if (error.message.includes('Permission denied')) {
        setError('❌ Camera permission denied. Please allow camera access in your browser settings.');
        setCameraPermission(false);
      } else {
        handleScanError(error);
      }
    }
  };

  const handleSuccessfulScan = async (barcode) => {
    if (!barcode || barcode === lastScanned || loading || !isMountedRef.current) return;
    
    // Prevent rapid duplicate scans
    const now = Date.now();
    if (now - lastScanTime.current < SCAN_COOLDOWN) return;
    lastScanTime.current = now;

    // Trigger haptic feedback for successful scan
    triggerHapticFeedback();
    
    setLastScanned(barcode);
    setScanAttempts(prev => prev + 1);
    
    // Stop scanning immediately for faster response
    await stopScanning();
    
    await processBarcode(barcode);
  };

  const processBarcode = async (barcode) => {
    if (!isMountedRef.current) return;
    
    setLoading(true);
    setError('');
    setSuccess('');

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
        setScanStats(prev => ({ ...prev, successful: prev.successful + 1 }));
        setRetryCount(0);
        
        // Trigger success haptic feedback
        triggerSuccessHapticFeedback();
        
        // Call the callback with product data
        if (onProductFound) {
          onProductFound(product);
        }
        
        // Auto-close after success with slight delay
        setTimeout(() => {
          if (isMountedRef.current) {
            onClose();
          }
        }, 1200);
        
      } else if (response.status === 404) {
        setError('❌ Product not found in inventory');
        setScanStats(prev => ({ ...prev, failed: prev.failed + 1 }));
        handleScanFailure();
      } else {
        setError('❌ Error looking up product');
        setScanStats(prev => ({ ...prev, failed: prev.failed + 1 }));
        handleScanFailure();
      }
    } catch (error) {
      console.error('Barcode lookup error:', error);
      setError('❌ Network error - please try again');
      setScanStats(prev => ({ ...prev, failed: prev.failed + 1 }));
      handleScanFailure();
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  const handleScanFailure = () => {
    setRetryCount(prev => prev + 1);
    if (retryCount >= MAX_RETRY_ATTEMPTS) {
      setError('❌ Multiple scan failures. Try manual entry or reposition barcode.');
      setShowManualInput(true);
    } else {
      // Auto-retry with brief delay
      setTimeout(() => {
        if (!isScanning && isMountedRef.current) {
          startScanning();
        }
      }, 1000);
    }
  };

  const handleScanError = (error) => {
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
      setShowManualInput(true);
    }
    
    stopScanning();
  };

  const stopScanning = async () => {
    setIsScanning(false);
    
    if (scannerInstanceRef.current) {
      try {
        await scannerInstanceRef.current.clear();
        scannerInstanceRef.current = null;
      } catch (error) {
        console.warn('Error stopping scanner:', error);
      }
    }
  };

  const cleanup = async () => {
    await stopScanning();
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

  const triggerHapticFeedback = () => {
    // Trigger haptic feedback on mobile devices
    if (navigator.vibrate) {
      navigator.vibrate(100); // Short vibration for scan detection
    }
  };

  const triggerSuccessHapticFeedback = () => {
    // Trigger success haptic feedback
    if (navigator.vibrate) {
      navigator.vibrate([100, 50, 100]); // Success pattern
    }
  };

  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (manualBarcode.trim()) {
      processBarcode(manualBarcode.trim());
      setManualBarcode('');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-2 md:p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-auto max-h-screen overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 md:p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 md:w-10 md:h-10 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
              <Zap size={16} className="text-white md:hidden" />
              <Zap size={20} className="text-white hidden md:block" />
            </div>
            <div>
              <h2 className="text-lg md:text-xl font-bold text-gray-800">⚡ Fast Barcode Scanner</h2>
              <p className="text-xs md:text-sm text-gray-600">Lightning-fast multi-format scanning</p>
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
              <h3 className="text-base md:text-lg font-semibold text-gray-800 mb-2">🔒 Camera Access Required</h3>
              <div className="text-sm md:text-base text-gray-600 mb-4 space-y-2">
                <p>To scan barcodes, please allow camera access in your browser.</p>
                <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg">
                  <p><strong>📱 Mobile:</strong> Tap the camera icon in address bar</p>
                  <p><strong>💻 Desktop:</strong> Click the camera icon next to the URL</p>
                  <p><strong>🔒 Secure:</strong> Camera access is required for barcode scanning only</p>
                </div>
              </div>
              <div className="space-y-2">
                <button
                  onClick={initializeCamera}
                  className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors text-sm md:text-base w-full sm:w-auto"
                >
                  🎥 Grant Camera Access
                </button>
                <br />
                <button
                  onClick={() => setShowManualInput(true)}
                  className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors text-sm md:text-base w-full sm:w-auto"
                >
                  ⌨️ Enter Barcode Manually
                </button>
              </div>
            </div>
          )}

          {/* Scanner Interface */}
          {cameraPermission === true && (
            <div className="space-y-4">
              {/* Scanner Controls */}
              <div className="flex flex-col sm:flex-row justify-center space-y-2 sm:space-y-0 sm:space-x-2">
                {!isScanning ? (
                  <>
                    <button
                      onClick={startScanning}
                      className="flex items-center justify-center space-x-2 bg-gradient-to-r from-green-500 to-green-600 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:from-green-600 hover:to-green-700 transition-all text-sm md:text-base shadow-lg"
                    >
                      <Camera size={16} className="md:hidden" />
                      <Camera size={20} className="hidden md:block" />
                      <span>⚡ Start Fast Scan</span>
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
                      placeholder="Enter barcode manually (e.g., 3222471081716)"
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

              {/* Enhanced Html5-qrcode Scanner */}
              {isScanning && (
                <div className="relative">
                  <div className="border-2 border-gray-300 rounded-lg overflow-hidden bg-black relative">
                    {/* Scanner container - html5-qrcode will inject here */}
                    <div 
                      id="qr-reader" 
                      className="w-full"
                      style={{ 
                        minHeight: window.innerWidth > 768 ? '400px' : '300px',
                        maxHeight: window.innerWidth > 768 ? '400px' : '300px'
                      }}
                    />
                    
                    {/* Enhanced Scanning Overlay */}
                    <div className="absolute inset-0 pointer-events-none">
                      <div className="relative w-full h-full">
                        {/* Format indicators */}
                        <div className="absolute top-2 left-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs">
                          📱 All Formats: EAN, UPC, Code128, QR
                        </div>
                        
                        {/* Enhanced Instructions */}
                        <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-80 text-white px-3 md:px-4 py-2 rounded-lg text-center max-w-xs">
                          <p className="text-xs md:text-sm font-medium text-green-400">🎯 Barcode Detection Active</p>
                          <p className="text-xs text-gray-300 mt-1">Hold phone 6-12 inches from barcode</p>
                          <p className="text-xs text-gray-300">Keep barcode horizontal & well-lit</p>
                        </div>
                        
                        {/* Scan area guide */}
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="border-2 border-green-400 border-dashed rounded-lg bg-transparent" 
                               style={{
                                 width: '280px',
                                 height: '120px',
                                 opacity: 0.6
                               }}>
                            <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-green-400 text-xs font-medium">
                              📊 Barcode Scan Area
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Status Messages */}
              {loading && (
                <div className="flex items-center justify-center space-x-2 p-3 md:p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="animate-spin rounded-full h-4 w-4 md:h-5 md:w-5 border-b-2 border-blue-500"></div>
                  <span className="text-blue-700 text-sm md:text-base">⚡ Fast lookup in progress...</span>
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

              {/* Enhanced Scan Statistics */}
              {(scanAttempts > 0 || scanStats.successful > 0) && (
                <div className="text-center space-y-1 bg-gradient-to-r from-blue-50 to-green-50 p-3 rounded-lg border">
                  <div className="text-xs text-gray-600">
                    Session Stats: ✅ {scanStats.successful} successful | ❌ {scanStats.failed} failed
                  </div>
                  {scanAttempts > 0 && (
                    <div className="text-xs text-gray-500">
                      Current attempts: {scanAttempts} | Retries: {retryCount}/{MAX_RETRY_ATTEMPTS}
                    </div>
                  )}
                </div>
              )}

              {/* Enhanced Instructions */}
              <div className="text-center text-xs md:text-sm text-gray-600 space-y-2 bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border">
                <p>⚡ <strong>Lightning-Fast Scanning Tips:</strong></p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-left">
                  <p>📱 Use back camera for best results</p>
                  <p>💡 Ensure good lighting</p>
                  <p>🎯 Hold steady, close to barcode</p>
                  <p>🔄 Auto-retry on scan failures</p>
                  <p>📊 Supports: EAN, UPC, Code128, QR</p>
                  <p>⚡ Sub-second response time</p>
                </div>
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
              <p className="text-sm md:text-base text-gray-600">⚡ Initializing fast scanner...</p>
              <div className="text-xs text-gray-500 mt-4 bg-gray-50 p-3 rounded-lg">
                <p><strong>🔍 Debug Info:</strong></p>
                <p>📍 URL: {window.location.protocol}//{window.location.host}</p>
                <p>🔒 Secure: {window.location.protocol === 'https:' ? '✅ HTTPS' : '❌ HTTP (camera may not work)'}</p>
                <p>🌐 Browser: {navigator.userAgent.split(' ').slice(-2).join(' ')}</p>
                <p>📹 Camera API: {(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) ? '✅ Available' : '❌ Not available'}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BarcodeScanner;