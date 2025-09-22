import React, { useState, useEffect, useRef } from 'react';
import { X, Camera, Keyboard, Zap, AlertCircle, CheckCircle } from 'lucide-react';
import Quagga from 'quagga';

const MobileBarcodeScanner = ({ isOpen, onClose, onProductFound }) => {
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [manualMode, setManualMode] = useState(false);
  const [barcode, setBarcode] = useState('');
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const detectorRef = useRef(null);
  const scanIntervalRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Initialize on open
  useEffect(() => {
    if (isOpen) {
      initializeCamera();
    } else {
      cleanup();
    }
  }, [isOpen]);

  const cleanup = () => {
    // Stop QuaggaJS
    try {
      Quagga.stop();
    } catch (e) {
      // QuaggaJS not running
    }
    
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    
    setCameraActive(false);
    setError('');
    setSuccess('');
    setManualMode(false);
  };

  const initializeCamera = async () => {
    try {
      setError('📱 Initializing camera...');
      
      // Check if BarcodeDetector is available
      if ('BarcodeDetector' in window) {
        detectorRef.current = new BarcodeDetector({
          formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'qr_code']
        });
      }
      
      // Mobile-first camera initialization
      const constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: 640 },
          height: { ideal: 480 }
        }
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      
      if (videoRef.current) {
        const video = videoRef.current;
        
        // Force immediate srcObject assignment
        video.srcObject = stream;
        
        // Wait for video to be ready
        await new Promise((resolve, reject) => {
          video.onloadedmetadata = resolve;
          video.onerror = reject;
          
          // Fallback timeout
          setTimeout(() => resolve(), 3000);
        });
        
        // Force play
        await video.play();
        
        setCameraActive(true);
        setError('');
        
        // Start scanning immediately
        startScanning();
        
      } else {
        throw new Error('Video element not found');
      }
      
    } catch (err) {
      console.error('Camera initialization failed:', err);
      setError('❌ Camera not available - using manual entry');
      setManualMode(true);
    }
  };

  const startScanning = () => {
    setError('🔍 Scanning for barcodes...');
    
    // Use QuaggaJS for barcode detection since BarcodeDetector is not available
    if (!detectorRef.current) {
      startQuaggaScanning();
    } else {
      startNativeScanning();
    }
  };

  const startQuaggaScanning = () => {
    if (!videoRef.current) return;
    
    console.log('🔍 Starting QuaggaJS scanning...');
    setError('🔍 QuaggaJS scanning active...');
    
    // Configure QuaggaJS for mobile barcode scanning
    Quagga.init({
      inputStream: {
        name: "Live",
        type: "LiveStream",
        target: videoRef.current,
        constraints: {
          width: 640,
          height: 480,
          facingMode: "environment"
        }
      },
      locator: {
        patchSize: "medium",
        halfSample: true
      },
      numOfWorkers: 2,
      frequency: 10,
      decoder: {
        readers: [
          "code_128_reader",
          "ean_reader",
          "ean_8_reader",
          "code_39_reader",
          "code_39_vin_reader",
          "codabar_reader",
          "upc_reader",
          "upc_e_reader"
        ]
      },
      locate: true
    }, (err) => {
      if (err) {
        console.error('❌ QuaggaJS init error:', err);
        setError('❌ Scanner initialization failed - use manual entry');
        return;
      }
      
      console.log('✅ QuaggaJS initialized');
      setError('🎯 Ready! Point camera at barcode');
      
      // Start scanning
      Quagga.start();
      
      // Listen for barcode detection
      Quagga.onDetected((data) => {
        const barcode = data.codeResult.code;
        console.log('🎯 Barcode detected by QuaggaJS:', barcode);
        
        // Stop scanning
        Quagga.stop();
        setError('⚡ Found: ' + barcode + ' - Looking up...');
        
        // Lookup product
        lookupProduct(barcode);
      });
    });
  };

  const startNativeScanning = () => {
    if (scanIntervalRef.current) {
      return;
    }
    
    scanIntervalRef.current = setInterval(async () => {
      try {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        
        if (!video || !canvas || video.videoWidth === 0) {
          return;
        }
        
        // Capture frame
        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);
        
        // Detect barcodes
        const barcodes = await detectorRef.current.detect(canvas);
        
        if (barcodes.length > 0) {
          const detectedBarcode = barcodes[0].rawValue;
          
          // Stop scanning
          clearInterval(scanIntervalRef.current);
          scanIntervalRef.current = null;
          
          // Lookup product
          await lookupProduct(detectedBarcode);
        }
        
      } catch (scanError) {
        // Continue scanning on errors
      }
    }, 300); // Scan every 300ms
  };

  const lookupProduct = async (barcodeValue) => {
    setLoading(true);
    setError('⚡ Looking up product...');
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/barcode/${barcodeValue}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const product = await response.json();
        setSuccess(`✅ Found: ${product.product_name}`);
        
        // Close and return product
        setTimeout(() => {
          onProductFound(product);
          onClose();
        }, 1500);
        
      } else {
        setError('❌ Product not found');
        setTimeout(() => {
          startScanning(); // Resume scanning
        }, 2000);
      }
      
    } catch (err) {
      setError('❌ Network error');
      setTimeout(() => {
        startScanning(); // Resume scanning
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
              <h2 className="text-lg font-bold">📱 Mobile Scanner</h2>
              <p className="text-xs text-gray-600">Optimized for mobile</p>
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
              
              {/* Video Display */}
              <div className="relative bg-black rounded-lg overflow-hidden" style={{ height: '300px' }}>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    backgroundColor: '#000'
                  }}
                />
                <canvas ref={canvasRef} className="hidden" />
                
                {/* Scanning overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-60 h-20 border-2 border-green-400 rounded-lg bg-green-400 bg-opacity-20">
                    {cameraActive && (
                      <div className="absolute -top-6 left-0 bg-green-500 text-white text-xs px-2 py-1 rounded">
                        {detectorRef.current ? '📱 Point at barcode' : '📱 Enhanced scanning active'}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Quick manual entry overlay for better UX */}
                {cameraActive && !detectorRef.current && (
                  <div className="absolute bottom-4 left-4 right-4">
                    <div className="bg-black bg-opacity-75 text-white p-2 rounded-lg text-center">
                      <p className="text-xs">Can't find barcode? Try manual entry! 👇</p>
                    </div>
                  </div>
                )}
                
                {/* Status indicator */}
                {cameraActive && (
                  <div className="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                    📷 Live
                  </div>
                )}
              </div>
              
              {/* Camera Controls */}
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    cleanup();
                    setTimeout(initializeCamera, 500);
                  }}
                  className="flex-1 bg-orange-500 text-white py-2 rounded-lg hover:bg-orange-600 text-sm"
                >
                  🔄 Restart
                </button>
                
                <button
                  onClick={() => setManualMode(true)}
                  className="flex-1 bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 text-sm"
                >
                  ⌨️ Manual
                </button>
              </div>
            </div>
          )}

          {/* Manual Entry */}
          {manualMode && (
            <div className="space-y-3">
              <div className="text-center">
                <h3 className="font-semibold text-gray-800">⌨️ Manual Entry</h3>
                <p className="text-sm text-gray-600">Type barcode number</p>
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
                    className="flex-1 bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 disabled:opacity-50"
                  >
                    {loading ? '⚡ Finding...' : '🔍 Find'}
                  </button>
                  
                  <button
                    type="button"
                    onClick={() => setBarcode('3222471081716')}
                    className="bg-purple-500 text-white px-4 py-3 rounded-lg hover:bg-purple-600"
                  >
                    Test
                  </button>
                </div>
              </form>
              
              <button
                onClick={() => {
                  setManualMode(false);
                  initializeCamera();
                }}
                className="w-full bg-gray-500 text-white py-2 rounded-lg hover:bg-gray-600 text-sm"
              >
                📷 Back to Camera
              </button>
            </div>
          )}

          {/* Status Messages */}
          {loading && (
            <div className="flex items-center justify-center space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
              <span className="text-blue-700">Loading...</span>
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
          
          {/* Debug Info */}
          <div className="bg-gray-50 p-2 rounded-lg text-xs text-gray-600">
            <p>Camera: {cameraActive ? '✅ Active' : '❌ Inactive'}</p>
            <p>Detector: {detectorRef.current ? '✅ Native API' : '🔧 QuaggaJS Fallback'}</p>
            <p>Stream: {streamRef.current ? '✅ Ready' : '❌ None'}</p>
          </div>
          
          {/* Auto-suggest manual entry if scanning issues */}
          {cameraActive && !detectorRef.current && (
            <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
              <div className="text-center">
                <p className="text-blue-800 text-sm font-medium">💡 Quick Tip</p>
                <p className="text-blue-600 text-xs mt-1">
                  Your device uses enhanced scanning. If barcodes aren't detected automatically, try manual entry for fastest results!
                </p>
                <button
                  onClick={() => setManualMode(true)}
                  className="mt-2 bg-blue-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-600"
                >
                  ⚡ Quick Manual Entry
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MobileBarcodeScanner;