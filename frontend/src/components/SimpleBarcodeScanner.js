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
      setError('');
      
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });

      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          setCameraReady(true);
          console.log('✅ Camera ready');
        };
      }
      
    } catch (err) {
      console.error('Camera error:', err);
      setError('❌ Camera not available. Using manual entry.');
      setManualMode(true);
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
          
          {/* Camera Scanner */}
          {!manualMode && (
            <div className="space-y-3">
              
              {/* Camera View */}
              <div className="relative bg-black rounded-lg overflow-hidden">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-64 object-cover"
                />
                <canvas ref={canvasRef} className="hidden" />
                
                {/* Scanning overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-48 h-24 border-2 border-green-400 rounded-lg bg-green-400 bg-opacity-10">
                    <div className="absolute -top-6 left-0 bg-green-500 text-white text-xs px-2 py-1 rounded">
                      Aim here
                    </div>
                  </div>
                </div>
                
                {scanning && (
                  <div className="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                    📱 Scanning...
                  </div>
                )}
              </div>
              
              {/* Camera Controls */}
              <div className="flex space-x-2">
                {!cameraReady ? (
                  <button
                    onClick={startCamera}
                    className="flex-1 bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 flex items-center justify-center space-x-2"
                  >
                    <Camera size={16} />
                    <span>Start Camera</span>
                  </button>
                ) : !scanning ? (
                  <button
                    onClick={startScanning}
                    className="flex-1 bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 flex items-center justify-center space-x-2"
                  >
                    <Zap size={16} />
                    <span>Start Scanning</span>
                  </button>
                ) : (
                  <button
                    onClick={stopScanning}
                    className="flex-1 bg-red-500 text-white py-3 rounded-lg hover:bg-red-600"
                  >
                    Stop Scanning
                  </button>
                )}
                
                <button
                  onClick={() => setManualMode(true)}
                  className="bg-gray-500 text-white px-4 py-3 rounded-lg hover:bg-gray-600"
                  title="Manual Entry"
                >
                  <Keyboard size={16} />
                </button>
              </div>
            </div>
          )}

          {/* Manual Entry */}
          {manualMode && (
            <div className="space-y-3">
              <div className="text-center">
                <h3 className="font-semibold text-gray-800">⌨️ Manual Entry</h3>
                <p className="text-sm text-gray-600">Type barcode for instant lookup</p>
              </div>
              
              <form onSubmit={handleManualSubmit} className="space-y-3">
                <input
                  type="text"
                  value={barcode}
                  onChange={(e) => setBarcode(e.target.value)}
                  placeholder="Enter barcode (e.g. 3222471081716)"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg text-center font-mono text-lg focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
                
                <div className="flex space-x-2">
                  <button
                    type="submit"
                    disabled={!barcode.trim() || loading}
                    className="flex-1 bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 disabled:opacity-50 font-medium"
                  >
                    {loading ? '⚡ Finding...' : '🔍 Find Product'}
                  </button>
                  
                  <button
                    type="button"
                    onClick={() => setBarcode('3222471081716')}
                    className="bg-purple-500 text-white px-4 py-3 rounded-lg hover:bg-purple-600"
                    title="Test barcode"
                  >
                    <Package size={16} />
                  </button>
                </div>
              </form>
              
              {!manualMode && detectorRef.current && (
                <button
                  onClick={() => setManualMode(false)}
                  className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 text-sm"
                >
                  📱 Back to Camera
                </button>
              )}
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

          {/* Instructions */}
          <div className="bg-gray-50 p-3 rounded-lg text-center">
            <h4 className="font-medium text-gray-800">📱 Quick Tips</h4>
            <p className="text-xs text-gray-600 mt-1">
              Hold barcode 4-6 inches from camera • Good lighting • Steady hands
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleBarcodeScanner;