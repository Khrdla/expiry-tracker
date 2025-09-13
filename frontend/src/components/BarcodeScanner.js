import React, { useState, useEffect, useRef } from 'react';
import { BrowserMultiFormatReader, DecodeHintType, BarcodeFormat } from '@zxing/browser';
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
  const [availableCameras, setAvailableCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState('');
  const [scanStats, setScanStats] = useState({ successful: 0, failed: 0 });
  
  const videoRef = useRef(null);
  const codeReaderRef = useRef(null);
  const scanningRef = useRef(false);
  const lastScanTime = useRef(0);
  const animationRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const MAX_RETRY_ATTEMPTS = 2;
  const SCAN_COOLDOWN = 150; // Reduced to 150ms for sub-second response
  const SCAN_TIMEOUT = 10000; // 10 seconds timeout for each scan attempt

  // Initialize ZXing reader with optimized settings
  useEffect(() => {
    const hints = new Map();
    // Enable all barcode formats for comprehensive support
    hints.set(DecodeHintType.POSSIBLE_FORMATS, [
      BarcodeFormat.EAN_13,
      BarcodeFormat.EAN_8,
      BarcodeFormat.UPC_A,
      BarcodeFormat.UPC_E,
      BarcodeFormat.CODE_128,
      BarcodeFormat.CODE_39,
      BarcodeFormat.CODE_93,
      BarcodeFormat.CODABAR,
      BarcodeFormat.ITF,
      BarcodeFormat.QR_CODE,
      BarcodeFormat.DATA_MATRIX,
      BarcodeFormat.PDF_417
    ]);
    
    // Optimize for accuracy and speed
    hints.set(DecodeHintType.TRY_HARDER, true);
    hints.set(DecodeHintType.ALSO_INVERTED, true);

    codeReaderRef.current = new BrowserMultiFormatReader(hints);
    
    return () => {
      if (codeReaderRef.current) {
        codeReaderRef.current.reset();
      }
    };
  }, []);

  useEffect(() => {
    if (isOpen) {
      initializeCamera();
      resetScanner();
    } else {
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
      // Get available cameras
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');
      setAvailableCameras(videoDevices);
      
      // Prefer back camera for better barcode scanning
      const backCamera = videoDevices.find(device => 
        device.label.toLowerCase().includes('back') || 
        device.label.toLowerCase().includes('rear') ||
        device.label.toLowerCase().includes('environment')
      );
      
      setSelectedCamera(backCamera?.deviceId || videoDevices[0]?.deviceId || '');
      setCameraPermission(true);
    } catch (error) {
      console.error('Camera initialization error:', error);
      setCameraPermission(false);
      setError('❌ Camera access denied. Please allow camera access and try again.');
    }
  };

  const startScanning = async () => {
    if (!codeReaderRef.current || !videoRef.current || !selectedCamera) {
      setError('❌ Scanner not ready. Please try again.');
      return;
    }

    try {
      resetScanner();
      setIsScanning(true);
      scanningRef.current = true;

      // Enhanced camera constraints for better barcode detection
      const constraints = {
        deviceId: selectedCamera,
        width: { ideal: 1920, min: 1280 },
        height: { ideal: 1080, min: 720 },
        frameRate: { ideal: 60, min: 30 },
        focusMode: 'continuous',
        exposureMode: 'continuous',
        whiteBalanceMode: 'continuous'
      };

      // Start continuous scanning with optimized settings
      await codeReaderRef.current.decodeFromVideoDevice(
        selectedCamera,
        videoRef.current,
        (result, err) => {
          if (result && scanningRef.current) {
            handleSuccessfulScan(result.getText());
          } else if (err && scanningRef.current) {
            // Only handle actual errors, not "not found" messages
            if (err.name !== 'NotFoundException') {
              console.warn('Scan error:', err);
            }
          }
        }
      );

      // Add scanning animation
      startScanAnimation();

    } catch (error) {
      console.error('Start scanning error:', error);
      handleScanError(error);
    }
  };

  const handleSuccessfulScan = async (barcode) => {
    if (!barcode || barcode === lastScanned || loading || !scanningRef.current) return;
    
    // Prevent rapid duplicate scans
    const now = Date.now();
    if (now - lastScanTime.current < SCAN_COOLDOWN) return;
    lastScanTime.current = now;

    // Trigger haptic feedback for successful scan
    triggerHapticFeedback();
    
    setLastScanned(barcode);
    setScanAttempts(prev => prev + 1);
    
    // Stop scanning immediately for faster response
    stopScanning();
    
    await processBarcode(barcode);
  };

  const processBarcode = async (barcode) => {
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
          onClose();
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
      setLoading(false);
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
        if (!isScanning && scanningRef.current) {
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

  const stopScanning = () => {
    scanningRef.current = false;
    setIsScanning(false);
    
    if (codeReaderRef.current) {
      try {
        codeReaderRef.current.reset();
      } catch (error) {
        console.warn('Error stopping scanner:', error);
      }
    }
    
    stopScanAnimation();
  };

  const cleanup = () => {
    stopScanning();
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
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

  const startScanAnimation = () => {
    const scanLine = document.getElementById('scan-line');
    if (scanLine) {
      scanLine.style.animation = 'scanAnimation 2s ease-in-out infinite';
    }
  };

  const stopScanAnimation = () => {
    const scanLine = document.getElementById('scan-line');
    if (scanLine) {
      scanLine.style.animation = 'none';
    }
  };

  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (manualBarcode.trim()) {
      processBarcode(manualBarcode.trim());
      setManualBarcode('');
    }
  };

  const switchCamera = () => {
    const currentIndex = availableCameras.findIndex(cam => cam.deviceId === selectedCamera);
    const nextIndex = (currentIndex + 1) % availableCameras.length;
    setSelectedCamera(availableCameras[nextIndex]?.deviceId || '');
    
    if (isScanning) {
      stopScanning();
      setTimeout(() => startScanning(), 500);
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
              <h3 className="text-base md:text-lg font-semibold text-gray-800 mb-2">Camera Access Required</h3>
              <p className="text-sm md:text-base text-gray-600 mb-4">Please allow camera access to scan barcodes</p>
              <button
                onClick={initializeCamera}
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
                    {availableCameras.length > 1 && (
                      <button
                        onClick={switchCamera}
                        className="flex items-center space-x-2 bg-purple-500 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:bg-purple-600 transition-colors text-sm md:text-base"
                      >
                        <RefreshCw size={16} className="md:hidden" />
                        <RefreshCw size={20} className="hidden md:block" />
                        <span>Switch Camera</span>
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

              {/* Enhanced Video Scanner */}
              {isScanning && (
                <div className="relative">
                  <div className="border-2 border-gray-300 rounded-lg overflow-hidden bg-black relative">
                    <video
                      ref={videoRef}
                      className="w-full h-auto"
                      style={{ 
                        minHeight: window.innerWidth > 768 ? '400px' : '300px',
                        maxHeight: window.innerWidth > 768 ? '400px' : '300px',
                        objectFit: 'cover'
                      }}
                      playsInline
                      muted
                    />
                    
                    {/* Enhanced Scanning Overlay */}
                    <div className="absolute inset-0 pointer-events-none">
                      <div className="relative w-full h-full">
                        {/* Main Scanning Frame */}
                        <div className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 ${window.innerWidth > 768 ? 'w-80 h-40' : 'w-64 h-32'} border-2 border-green-400 rounded-lg bg-green-400 bg-opacity-10`}>
                          {/* Corner indicators */}
                          <div className="absolute -top-1 -left-1 w-8 h-8 border-t-4 border-l-4 border-green-400 rounded-tl-lg"></div>
                          <div className="absolute -top-1 -right-1 w-8 h-8 border-t-4 border-r-4 border-green-400 rounded-tr-lg"></div>
                          <div className="absolute -bottom-1 -left-1 w-8 h-8 border-b-4 border-l-4 border-green-400 rounded-bl-lg"></div>
                          <div className="absolute -bottom-1 -right-1 w-8 h-8 border-b-4 border-r-4 border-green-400 rounded-br-lg"></div>
                          
                          {/* Animated scan line */}
                          <div 
                            id="scan-line" 
                            className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-green-400 to-transparent opacity-80"
                            style={{
                              animation: isScanning ? 'scanAnimation 2s ease-in-out infinite' : 'none'
                            }}
                          ></div>
                        </div>
                        
                        {/* Format indicators */}
                        <div className="absolute top-2 left-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs">
                          📱 All Formats: EAN, UPC, Code128, QR
                        </div>
                        
                        {/* Instructions */}
                        <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-70 text-white px-3 md:px-4 py-2 rounded-lg">
                          <p className="text-xs md:text-sm text-center font-medium">Position barcode within the green frame</p>
                          <p className="text-xs text-center text-gray-300">⚡ Lightning-fast detection enabled</p>
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
            </div>
          )}
        </div>
      </div>
      
      {/* Add CSS for scan animation */}
      <style jsx>{`
        @keyframes scanAnimation {
          0% { top: 0; opacity: 0; }
          50% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
      `}</style>
    </div>
  );
};

export default BarcodeScanner;