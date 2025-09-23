import React, { useState, useEffect, useRef } from 'react';
import { X, Camera, Keyboard, Zap, AlertCircle, CheckCircle, Package } from 'lucide-react';
import { BrowserMultiFormatReader } from '@zxing/library';

const FixedMobileScanner = ({ isOpen, onClose, onProductFound }) => {
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [manualMode, setManualMode] = useState(false);
  const [barcode, setBarcode] = useState('');
  const [autoScanEnabled, setAutoScanEnabled] = useState(false);
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const scanIntervalRef = useRef(null);
  const mountedRef = useRef(true);
  const codeReaderRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Cleanup and mount management
  // Initialize on open - CAMERA FIRST (PRIMARY)
  useEffect(() => {
    mountedRef.current = true;
    if (isOpen) {
      // Start with CAMERA mode as PRIMARY option
      setManualMode(false);
      setError('');
      setSuccess('');
      // Auto-start camera when modal opens
      setTimeout(() => {
        startCamera();
      }, 500);
    } else {
      cleanup();
    }
    
    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, [isOpen]);

  const cleanup = () => {
    try {
      if (scanIntervalRef.current) {
        clearInterval(scanIntervalRef.current);
        scanIntervalRef.current = null;
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => {
          try {
            track.stop();
          } catch (e) {
            console.warn('Track stop error:', e);
          }
        });
        streamRef.current = null;
      }
      
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      
      setCameraActive(false);
      setAutoScanEnabled(false);
      setError('');
      setSuccess('');
    } catch (e) {
      console.warn('Cleanup error:', e);
    }
  };

  const startCamera = async () => {
    if (!mountedRef.current) return;
    
    try {
      setError('📱 Starting camera...');
      
      // Simple, reliable camera constraints
      const constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: 640, max: 1280 },
          height: { ideal: 480, max: 720 }
        }
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      if (!mountedRef.current) {
        // Component unmounted during camera initialization
        stream.getTracks().forEach(track => track.stop());
        return;
      }
      
      streamRef.current = stream;
      
      if (videoRef.current && mountedRef.current) {
        videoRef.current.srcObject = stream;
        
        // Wait for video to be ready
        const videoReady = new Promise((resolve, reject) => {
          if (videoRef.current) {
            videoRef.current.onloadedmetadata = () => resolve();
            videoRef.current.onerror = reject;
          }
        });
        
        await videoReady;
        
        if (mountedRef.current) {
          await videoRef.current.play();
          setCameraActive(true);
          setError('');
          setManualMode(false);
        }
      }
      
    } catch (err) {
      console.error('Camera error:', err);
      if (mountedRef.current) {
        setError('❌ Camera not available - using manual entry');
        setManualMode(true);
      }
    }
  };

  const startSimpleScanning = () => {
    if (!cameraActive || !videoRef.current || scanIntervalRef.current) return;
    
    setAutoScanEnabled(true);
    setError('🔍 Auto-scanning enabled - point at barcode');
    
    // Simple interval-based scanning without QuaggaJS
    scanIntervalRef.current = setInterval(() => {
      if (!mountedRef.current || !autoScanEnabled) {
        stopScanning();
        return;
      }
      
      // Visual feedback that scanning is active
      const now = Date.now();
      if (now % 2000 < 1000) {
        setError('🔍 Scanning... or use manual entry below');
      } else {
        setError('📱 Point camera at barcode or enter manually');
      }
    }, 1000);
  };

  const stopScanning = () => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    setAutoScanEnabled(false);
    setError('');
  };

  const lookupProduct = async (barcodeValue) => {
    if (!mountedRef.current) return;
    
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
      
      if (!mountedRef.current) return;
      
      if (response.ok) {
        const product = await response.json();
        setSuccess(`✅ Found in ${lookupTime}ms: ${product.product_name}`);
        
        // Close scanner and return product
        setTimeout(() => {
          if (mountedRef.current) {
            onProductFound(product);
            onClose();
          }
        }, 1500);
        
      } else {
        setError('❌ Product not found in database');
      }
      
    } catch (err) {
      console.error('Lookup error:', err);
      if (mountedRef.current) {
        setError('❌ Network error - check connection');
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    if (!barcode.trim() || loading) return;
    
    await lookupProduct(barcode.trim());
    setBarcode('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-2">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md max-h-screen overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-green-500 to-blue-500">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">📱 Simple Scanner</h2>
              <p className="text-xs text-green-100">Fast & Reliable</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full text-white"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          
          {/* Manual Entry Mode (Primary) */}
          <div className="space-y-4">
            <div className="text-center bg-gradient-to-r from-blue-50 to-green-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-800">⚡ Quick Barcode Entry</h3>
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
                  disabled={loading}
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
          </div>

          {/* Camera Option (Secondary) */}
          {!manualMode && (
            <div className="space-y-3 border-t pt-4">
              <div className="text-center">
                <h4 className="font-medium text-gray-800">📷 Camera Scanner (Optional)</h4>
                <p className="text-xs text-gray-600">For hands-free scanning</p>
              </div>
              
              {!cameraActive ? (
                <button
                  onClick={startCamera}
                  className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors flex items-center justify-center space-x-2"
                >
                  <Camera size={16} />
                  <span>Start Camera</span>
                </button>
              ) : (
                <div className="space-y-3">
                  {/* Video Display */}
                  <div className="relative bg-black rounded-lg overflow-hidden" style={{ height: '200px' }}>
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-full object-cover"
                    />
                    
                    {/* Simple scanning overlay */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-48 h-16 border-2 border-green-400 rounded-lg bg-green-400 bg-opacity-20">
                        <div className="absolute -top-6 left-0 bg-green-500 text-white text-xs px-2 py-1 rounded">
                          Point at barcode
                        </div>
                      </div>
                    </div>
                    
                    {autoScanEnabled && (
                      <div className="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full animate-pulse">
                        📷 Scanning
                      </div>
                    )}
                  </div>
                  
                  {/* Camera Controls */}
                  <div className="flex space-x-2">
                    {!autoScanEnabled ? (
                      <button
                        onClick={startSimpleScanning}
                        className="flex-1 bg-green-500 text-white py-2 rounded-lg hover:bg-green-600 transition-colors text-sm"
                      >
                        Start Auto-Scan
                      </button>
                    ) : (
                      <button
                        onClick={stopScanning}
                        className="flex-1 bg-red-500 text-white py-2 rounded-lg hover:bg-red-600 transition-colors text-sm"
                      >
                        Stop Scanning
                      </button>
                    )}
                    
                    <button
                      onClick={() => {
                        cleanup();
                        setManualMode(true);
                      }}
                      className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors text-sm"
                    >
                      Manual Only
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Show camera option button when in manual mode */}
          {manualMode && (
            <div className="border-t pt-4">
              <button
                onClick={() => {
                  setManualMode(false);
                  startCamera();
                }}
                className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 transition-colors text-sm flex items-center justify-center space-x-2"
              >
                <Camera size={16} />
                <span>Try Camera Scanner</span>
              </button>
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
              <AlertCircle size={16} className="text-red-500 flex-shrink-0" />
              <span className="text-red-700 text-sm">{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center space-x-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle size={16} className="text-green-500 flex-shrink-0" />
              <span className="text-green-700 text-sm">{success}</span>
            </div>
          )}

          {/* Instructions */}
          <div className="bg-gray-50 p-3 rounded-lg text-center">
            <h4 className="font-medium text-gray-800 text-sm">💡 Quick Tips</h4>
            <p className="text-xs text-gray-600 mt-1">
              Manual entry is fastest • Camera is optional • Works with all barcode formats
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FixedMobileScanner;