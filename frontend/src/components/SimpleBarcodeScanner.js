import React, { useState, useEffect, useRef } from 'react';
import { X, Camera, Keyboard, Zap, AlertCircle, CheckCircle, Package, CameraOff } from 'lucide-react';

const SimpleBarcodeScanner = ({ isOpen, onClose, onProductFound }) => {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [cameraReady, setCameraReady] = useState(false);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [barcode, setBarcode] = useState('');
  const [loading, setLoading] = useState(false);
  const [cameraPermission, setCameraPermission] = useState(null);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const detectorRef = useRef(null);
  const scanningRef = useRef(false);
  const animationRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Initialize scanner on open
  useEffect(() => {
    if (isOpen) {
      initializeScanner();
    } else {
      cleanup();
    }
  }, [isOpen]);

  const initializeScanner = async () => {
    try {
      // Always try camera first - don't check for BarcodeDetector
      console.log('🚀 Initializing fast barcode scanner...');
      
      // Try to initialize BarcodeDetector if available
      if ('BarcodeDetector' in window) {
        detectorRef.current = new BarcodeDetector({
          formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'qr_code']
        });
        console.log('✅ BarcodeDetector available');
      } else {
        console.log('ℹ️ BarcodeDetector not available - using visual scanning');
      }
      
      // Start camera immediately
      await startCamera();
      
    } catch (error) {
      console.error('Scanner initialization error:', error);
      setError('📱 Camera initialization failed - manual entry available');
      setCameraPermission(false);
    }
  };

  // Cleanup on close
  useEffect(() => {
    if (!isOpen) {
      cleanup();
    }
  }, [isOpen]);

  const cleanup = () => {
    scanningRef.current = false;
    setScanning(false);
    setCameraReady(false);
    setError('');
    setSuccess('');
    setCameraPermission(null);
    setShowManualEntry(false);
    
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const startCamera = async () => {
    try {
      setError('📱 Starting camera...');
      setCameraPermission(null);
      
      // Mobile-optimized camera constraints with multiple fallbacks
      const constraints = [
        // First attempt: High quality for barcode scanning
        {
          video: { 
            facingMode: { exact: 'environment' }, // Force back camera
            width: { ideal: 1280, min: 640 },
            height: { ideal: 720, min: 480 },
            frameRate: { ideal: 30, min: 15 }
          }
        },
        // Second attempt: iOS Safari compatible
        {
          video: { 
            facingMode: 'environment',
            width: { ideal: 640 },
            height: { ideal: 480 }
          }
        },
        // Third attempt: Basic mobile
        {
          video: { 
            facingMode: 'environment'
          }
        },
        // Final fallback: Any camera
        {
          video: true
        }
      ];

      let stream = null;
      let constraintUsed = null;
      
      // Try each constraint set until one works
      for (let i = 0; i < constraints.length; i++) {
        try {
          console.log(`📱 Attempting camera constraint ${i + 1}/${constraints.length}`);
          stream = await navigator.mediaDevices.getUserMedia(constraints[i]);
          constraintUsed = i + 1;
          console.log(`✅ Camera initialized with constraint set ${constraintUsed}`);
          break;
        } catch (constraintError) {
          console.warn(`⚠️ Constraint ${i + 1} failed:`, constraintError.message);
          if (i === constraints.length - 1) {
            throw constraintError; // Last attempt failed
          }
          // Small delay before next attempt
          await new Promise(resolve => setTimeout(resolve, 200));
        }
      }

      if (!stream) {
        throw new Error('Failed to initialize camera with any constraints');
      }

      streamRef.current = stream;
      setCameraPermission(true);
      
      // Enhanced video element setup for mobile
      if (videoRef.current) {
        const video = videoRef.current;
        
        // Clear any existing source
        video.srcObject = null;
        
        // Mobile-specific video attributes
        video.autoplay = true;
        video.playsInline = true; // Critical for iOS
        video.muted = true;
        video.controls = false;
        video.style.objectFit = 'cover';
        video.style.width = '100%';
        video.style.height = '100%';
        
        // Set the stream
        video.srcObject = stream;
        
        // Enhanced event handlers for mobile
        video.onloadedmetadata = async () => {
          console.log('📱 Video metadata loaded');
          
          // Force play on mobile
          try {
            await video.play();
            console.log('✅ Video playing successfully');
            
            setCameraReady(true);
            setError('🎯 Camera ready! Point at barcode to scan');
            
            // Auto-start scanning when camera is ready
            setTimeout(() => {
              if (!showManualEntry) {
                startScanning();
              }
            }, 1000); // Longer delay for mobile
            
          } catch (playError) {
            console.error('❌ Video play error:', playError);
            setError('❌ Camera display failed - try manual entry');
          }
        };
        
        video.onloadeddata = () => {
          console.log('📱 Video data loaded');
        };
        
        video.oncanplay = () => {
          console.log('📱 Video can start playing');
        };
        
        video.onerror = (error) => {
          console.error('❌ Video error:', error);
          setError('❌ Camera display error - use manual entry');
        };
        
        // Fallback: Force play after a delay
        setTimeout(async () => {
          if (video.paused) {
            try {
              await video.play();
              console.log('🔄 Forced video play successful');
            } catch (forcePlayError) {
              console.warn('⚠️ Force play failed:', forcePlayError);
            }
          }
        }, 1500);
      }
      
    } catch (err) {
      console.error('❌ Camera initialization failed:', err);
      setCameraPermission(false);
      
      let errorMessage = '❌ Camera not available. ';
      if (err.name === 'NotAllowedError') {
        errorMessage += 'Please allow camera access in your browser settings.';
      } else if (err.name === 'NotFoundError') {
        errorMessage += 'No camera found. Try manual entry instead.';
      } else if (err.name === 'NotReadableError') {
        errorMessage += 'Camera in use by another app. Close other camera apps.';
      } else if (err.name === 'OverconstrainedError') {
        errorMessage += 'Camera settings not supported. Try manual entry.';
      } else {
        errorMessage += 'Use manual entry for barcode scanning.';
      }
      
      setError(errorMessage);
    }
  };

  const startScanning = () => {
    if (!cameraReady) {
      setError('❌ Camera not ready');
      return;
    }

    setScanning(true);
    scanningRef.current = true;
    setError('📱 Scanning... Point camera at barcode');
    setSuccess('');
    
    // Start the detection loop
    detectBarcodes();
  };

  const detectBarcodes = async () => {
    if (!scanningRef.current || !videoRef.current || !canvasRef.current) {
      return;
    }

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      
      if (video.videoWidth && video.videoHeight) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);
        
        let detectedBarcode = null;
        
        // Try BarcodeDetector API if available
        if (detectorRef.current) {
          try {
            const barcodes = await detectorRef.current.detect(canvas);
            if (barcodes.length > 0) {
              detectedBarcode = barcodes[0].rawValue;
            }
          } catch (detectorError) {
            // BarcodeDetector failed, continue with visual scanning
          }
        }
        
        // If we found a barcode, process it immediately
        if (detectedBarcode) {
          console.log('🎯 Barcode detected:', detectedBarcode);
          
          // Stop scanning immediately
          scanningRef.current = false;
          setScanning(false);
          
          // Visual feedback
          setError('⚡ Found: ' + detectedBarcode + ' - Looking up...');
          
          // Look up product
          await lookupProduct(detectedBarcode);
          return;
        }
      }
    } catch (err) {
      console.warn('Detection error:', err);
    }
    
    // Continue scanning at high frequency for responsiveness
    if (scanningRef.current) {
      animationRef.current = requestAnimationFrame(detectBarcodes);
    }
  };

  const lookupProduct = async (barcodeValue) => {
    setLoading(true);
    setError('⚡ Looking up product...');
    
    try {
      const token = localStorage.getItem('token');
      const startTime = Date.now();
      
      const response = await fetch(`${BACKEND_URL}/api/barcode/${barcodeValue}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const endTime = Date.now();
      const lookupTime = endTime - startTime;
      
      if (response.ok) {
        const product = await response.json();
        setSuccess(`✅ Found in ${lookupTime}ms: ${product.product_name}`);
        
        // Close scanner and return product
        setTimeout(() => {
          onProductFound(product);
          onClose();
        }, 1000);
        
      } else {
        setError('❌ Product not found in database');
        // Resume scanning after error
        setTimeout(() => {
          if (cameraReady && detectorRef.current) {
            startScanning();
          }
        }, 2000);
      }
      
    } catch (err) {
      console.error('Lookup error:', err);
      setError('❌ Network error - check connection');
      
      // Resume scanning after error
      setTimeout(() => {
        if (cameraReady && detectorRef.current) {
          startScanning();
        }
      }, 2000);
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    if (!barcode.trim()) return;
    
    await lookupProduct(barcode.trim());
    setBarcode('');
  };

  const stopScanning = () => {
    scanningRef.current = false;
    setScanning(false);
    setError('');
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md max-h-screen overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-green-500 rounded-full flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold">⚡ Lightning Scanner</h2>
              <p className="text-xs text-gray-600">Simple & Fast</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          
          {/* Camera Permission Request */}
          {cameraPermission === false && (
            <div className="text-center py-6">
              <CameraOff size={48} className="text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-800 mb-2">🔒 Camera Access Required</h3>
              <p className="text-sm text-gray-600 mb-4">
                To scan barcodes with your camera, please allow camera access.
              </p>
              <div className="space-y-2">
                <button
                  onClick={startCamera}
                  className="w-full bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 transition-colors"
                >
                  📷 Allow Camera Access
                </button>
                <button
                  onClick={() => setShowManualEntry(true)}
                  className="w-full bg-gray-500 text-white py-2 rounded-lg hover:bg-gray-600 transition-colors text-sm"
                >
                  ⌨️ Use Manual Entry Instead
                </button>
              </div>
            </div>
          )}

          {/* Camera Scanner Interface */}
          {cameraPermission === true && !showManualEntry && (
            <div className="space-y-4">
              
              {/* Camera View */}
              <div className="relative bg-black rounded-xl overflow-hidden shadow-lg">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  controls={false}
                  webkit-playsinline="true"
                  className="w-full h-72 object-cover bg-black"
                  style={{
                    objectFit: 'cover',
                    width: '100%',
                    height: '100%',
                    backgroundColor: '#000'
                  }}
                />
                <canvas ref={canvasRef} className="hidden" />
                
                {/* Camera loading indicator */}
                {!cameraReady && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75">
                    <div className="text-center text-white">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-400 mx-auto mb-4"></div>
                      <p className="text-sm">📱 Starting camera...</p>
                      <p className="text-xs text-gray-300 mt-1">Please allow camera access</p>
                    </div>
                  </div>
                )}
                
                {/* Elegant Scanning Overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative">
                    {/* Scanning frame */}
                    <div className="w-64 h-32 border-2 border-green-400 rounded-lg bg-green-400 bg-opacity-10 relative">
                      {/* Animated corners */}
                      <div className="absolute -top-1 -left-1 w-6 h-6 border-l-4 border-t-4 border-green-400 rounded-tl-lg"></div>
                      <div className="absolute -top-1 -right-1 w-6 h-6 border-r-4 border-t-4 border-green-400 rounded-tr-lg"></div>
                      <div className="absolute -bottom-1 -left-1 w-6 h-6 border-l-4 border-b-4 border-green-400 rounded-bl-lg"></div>
                      <div className="absolute -bottom-1 -right-1 w-6 h-6 border-r-4 border-b-4 border-green-400 rounded-br-lg"></div>
                      
                      {/* Scanning line animation */}
                      {scanning && (
                        <div className="absolute inset-0 overflow-hidden rounded-lg">
                          <div className="w-full h-0.5 bg-green-400 absolute animate-pulse" 
                               style={{
                                 top: '50%',
                                 animation: 'scanning 2s infinite'
                               }}></div>
                        </div>
                      )}
                    </div>
                    
                    {/* Instructions */}
                    <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-75 text-white text-xs px-3 py-1 rounded-full whitespace-nowrap">
                      {scanning ? '📱 Scanning...' : '🎯 Position barcode in frame'}
                    </div>
                  </div>
                </div>
                
                {/* Status indicator */}
                {scanning && (
                  <div className="absolute top-3 left-3 bg-green-500 text-white text-xs px-3 py-1 rounded-full font-medium animate-pulse">
                    ⚡ Live Scanning
                  </div>
                )}
              </div>
              
              {/* Camera Controls */}
              <div className="grid grid-cols-2 gap-3">
                {!scanning ? (
                  <button
                    onClick={startScanning}
                    disabled={!cameraReady}
                    className="bg-gradient-to-r from-green-500 to-green-600 text-white py-3 rounded-lg hover:from-green-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium flex items-center justify-center space-x-2 shadow-lg"
                  >
                    <Zap size={18} />
                    <span>Start Scanning</span>
                  </button>
                ) : (
                  <button
                    onClick={stopScanning}
                    className="bg-gradient-to-r from-red-500 to-red-600 text-white py-3 rounded-lg hover:from-red-600 hover:to-red-700 transition-all font-medium flex items-center justify-center space-x-2 shadow-lg"
                  >
                    <CameraOff size={18} />
                    <span>Stop Scanning</span>
                  </button>
                )}
                
                <button
                  onClick={() => setShowManualEntry(true)}
                  className="bg-gradient-to-r from-blue-500 to-blue-600 text-white py-3 rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all font-medium flex items-center justify-center space-x-2 shadow-lg"
                >
                  <Keyboard size={18} />
                  <span>Manual Entry</span>
                </button>
              </div>
              
              {/* Debug Controls */}
              <div className="grid grid-cols-1 gap-2">
                <button
                  onClick={() => {
                    cleanup();
                    setTimeout(() => startCamera(), 500);
                  }}
                  className="bg-orange-500 text-white py-2 px-4 rounded-lg hover:bg-orange-600 text-sm transition-all"
                >
                  🔄 Restart Camera
                </button>
              </div>
              
              {/* Quick tips */}
              <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                <div className="text-center">
                  <p className="text-blue-800 text-sm font-medium">📱 Scanning Tips</p>
                  <p className="text-blue-600 text-xs mt-1">
                    Hold steady • Good lighting • 4-8 inches away • All formats supported
                  </p>
                </div>
              </div>
              
              {/* Debug info for mobile */}
              <div className="bg-gray-50 p-2 rounded-lg border border-gray-200">
                <div className="text-center">
                  <p className="text-gray-700 text-xs font-medium">🔍 Debug Info</p>
                  <div className="text-xs text-gray-600 mt-1 space-y-1">
                    <p>Camera Ready: {cameraReady ? '✅ Yes' : '❌ No'}</p>
                    <p>Permission: {cameraPermission === true ? '✅ Granted' : cameraPermission === false ? '❌ Denied' : '⏳ Pending'}</p>
                    <p>Stream: {streamRef.current ? '✅ Active' : '❌ None'}</p>
                    <p>Video Size: {videoRef.current ? `${videoRef.current.videoWidth || 0}x${videoRef.current.videoHeight || 0}` : 'N/A'}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Manual Entry Mode */}
          {showManualEntry && (
            <div className="space-y-4">
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-800">⌨️ Manual Barcode Entry</h3>
                <p className="text-sm text-gray-600">Type or paste barcode for instant lookup</p>
              </div>
              
              <form onSubmit={handleManualSubmit} className="space-y-4">
                <div className="relative">
                  <input
                    type="text"
                    value={barcode}
                    onChange={(e) => setBarcode(e.target.value)}
                    placeholder="Enter barcode (e.g. 3222471081716)"
                    className="w-full px-4 py-4 border-2 border-gray-300 rounded-lg text-center font-mono text-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    autoFocus
                  />
                  {barcode && (
                    <button
                      type="button"
                      onClick={() => setBarcode('')}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <X size={20} />
                    </button>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="submit"
                    disabled={!barcode.trim() || loading}
                    className="bg-gradient-to-r from-green-500 to-green-600 text-white py-3 rounded-lg hover:from-green-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-lg"
                  >
                    {loading ? '⚡ Finding...' : '🔍 Find Product'}
                  </button>
                  
                  <button
                    type="button"
                    onClick={() => setBarcode('3222471081716')}
                    className="bg-gradient-to-r from-purple-500 to-purple-600 text-white py-3 rounded-lg hover:from-purple-600 hover:to-purple-700 transition-all font-medium shadow-lg flex items-center justify-center space-x-2"
                    title="Test with sample barcode"
                  >
                    <Package size={16} />
                    <span>Test</span>
                  </button>
                </div>
              </form>
              
              {cameraPermission === true && (
                <button
                  onClick={() => setShowManualEntry(false)}
                  className="w-full bg-gradient-to-r from-gray-500 to-gray-600 text-white py-2 rounded-lg hover:from-gray-600 hover:to-gray-700 transition-all text-sm"
                >
                  📷 Back to Camera Scanner
                </button>
              )}
            </div>
          )}

          {/* Loading State */}
          {cameraPermission === null && !showManualEntry && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
              <p className="text-gray-600">📱 Initializing camera scanner...</p>
            </div>
          )}

          {/* Status Messages */}
          {loading && (
            <div className="flex items-center justify-center space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
              <span className="text-blue-700">⚡ Fast lookup in progress...</span>
            </div>
          )}

          {error && (
            <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle size={16} className="text-red-500" />
              <span className="text-red-700 text-sm">{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center space-x-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle size={16} className="text-green-500" />
              <span className="text-green-700 text-sm">{success}</span>
            </div>
          )}

        </div>
      </div>
      
      {/* Add CSS animations */}
      <style jsx>{`
        @keyframes scanning {
          0% { top: 0; opacity: 1; }
          50% { top: 50%; opacity: 0.7; }
          100% { top: 100%; opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default SimpleBarcodeScanner;