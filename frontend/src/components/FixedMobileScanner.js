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
      
      // Stop ZXing reader
      if (codeReaderRef.current) {
        try {
          codeReaderRef.current.reset();
        } catch (e) {
          console.warn('ZXing reader reset error:', e);
        }
        codeReaderRef.current = null;
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
      
      // Initialize ZXing barcode reader
      if (!codeReaderRef.current) {
        codeReaderRef.current = new BrowserMultiFormatReader();
      }
      
      // Get available video devices
      const videoDevices = await navigator.mediaDevices.enumerateDevices();
      const cameras = videoDevices.filter(device => device.kind === 'videoinput');
      
      // Try to find back camera (environment)
      let selectedDeviceId = cameras.find(camera => 
        camera.label.toLowerCase().includes('back') || 
        camera.label.toLowerCase().includes('rear') ||
        camera.label.toLowerCase().includes('environment')
      )?.deviceId || cameras[0]?.deviceId;
      
      if (!selectedDeviceId) {
        throw new Error('No camera devices found');
      }

      // Start camera with ZXing
      await codeReaderRef.current.decodeFromVideoDevice(
        selectedDeviceId,
        videoRef.current,
        (result, error) => {
          if (result && mountedRef.current && cameraActive) {
            const barcode = result.getText();
            console.log('🎯 Barcode detected by ZXing:', barcode);
            
            // Stop scanning and lookup product
            setAutoScanEnabled(false);
            lookupProduct(barcode);
          }
          
          if (error && error.name !== 'NotFoundException') {
            console.warn('ZXing scan error:', error);
          }
        }
      );
      
      if (mountedRef.current) {
        setCameraActive(true);
        setAutoScanEnabled(true);
        setError('🎯 Camera ready! Point at barcode');
        setManualMode(false);
        console.log('✅ ZXing camera started successfully');
      }
      
    } catch (err) {
      console.error('Camera/ZXing error:', err);
      if (mountedRef.current) {
        let errorMsg = '❌ Camera not available';
        
        if (err.name === 'NotAllowedError') {
          errorMsg = '❌ Camera permission denied - click "Allow" when prompted';
        } else if (err.name === 'NotFoundError') {
          errorMsg = '❌ No camera found - manual entry available below';
        } else if (err.message?.includes('devices')) {
          errorMsg = '❌ No camera devices available - manual entry available below';
        }
        
        setError(errorMsg);
        // KEEP CAMERA MODE AS PRIMARY - Don't switch to manual mode
        setManualMode(false);
        setCameraActive(false);
      }
    }
  };

  const stopScanning = () => {
    try {
      if (codeReaderRef.current) {
        codeReaderRef.current.reset();
      }
      if (scanIntervalRef.current) {
        clearInterval(scanIntervalRef.current);
        scanIntervalRef.current = null;
      }
      setAutoScanEnabled(false);
      setCameraActive(false);
      setError('');
    } catch (e) {
      console.warn('Stop scanning error:', e);
    }
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
          
          {/* Camera Scanner Mode (PRIMARY) - Always visible */}
          {!manualMode && (
            <div className="space-y-4">
              <div className="text-center bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-800">📷 Camera Scanner (Primary)</h3>
                <p className="text-sm text-gray-600">Point camera at barcode for instant detection</p>
              </div>
              
              {!cameraActive ? (
                <div className="space-y-3">
                  {/* Camera placeholder with scanning frame */}
                  <div className="relative bg-black rounded-lg h-64 flex items-center justify-center">
                    <div className="text-center text-white">
                      <Camera size={48} className="mx-auto mb-4 text-gray-400" />
                      <p className="text-sm">
                        {error.includes('Camera') ? 'Camera unavailable' : 'Camera ready to start'}
                      </p>
                    </div>
                    
                    {/* Show scanning frame even when camera isn't active */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-64 h-32 border-2 border-green-400 rounded-lg bg-green-400 bg-opacity-20 relative">
                        {/* Corner indicators */}
                        <div className="absolute -top-1 -left-1 w-6 h-6 border-l-4 border-t-4 border-green-400 rounded-tl-lg"></div>
                        <div className="absolute -top-1 -right-1 w-6 h-6 border-r-4 border-t-4 border-green-400 rounded-tr-lg"></div>
                        <div className="absolute -bottom-1 -left-1 w-6 h-6 border-l-4 border-b-4 border-green-400 rounded-bl-lg"></div>
                        <div className="absolute -bottom-1 -right-1 w-6 h-6 border-r-4 border-b-4 border-green-400 rounded-br-lg"></div>
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={startCamera}
                    className="w-full bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center space-x-2 font-medium"
                  >
                    <Camera size={16} />
                    <span>🚀 Start Camera Scanning</span>
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {/* Video Display */}
                  <div className="relative bg-black rounded-lg overflow-hidden" style={{ height: '300px' }}>
                    <video
                      ref={videoRef}
                      className="w-full h-full object-cover"
                      style={{ transform: 'scaleX(-1)' }}
                    />
                    
                    {/* Enhanced scanning overlay */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="relative">
                        {/* Main scanning frame */}
                        <div className="w-64 h-32 border-2 border-green-400 rounded-lg bg-green-400 bg-opacity-20 relative">
                          {/* Corner indicators */}
                          <div className="absolute -top-1 -left-1 w-6 h-6 border-l-4 border-t-4 border-green-400 rounded-tl-lg"></div>
                          <div className="absolute -top-1 -right-1 w-6 h-6 border-r-4 border-t-4 border-green-400 rounded-tr-lg"></div>
                          <div className="absolute -bottom-1 -left-1 w-6 h-6 border-l-4 border-b-4 border-green-400 rounded-bl-lg"></div>
                          <div className="absolute -bottom-1 -right-1 w-6 h-6 border-r-4 border-b-4 border-green-400 rounded-br-lg"></div>
                          
                          {/* Scanning animation */}
                          {autoScanEnabled && (
                            <div className="absolute inset-0 overflow-hidden rounded-lg">
                              <div className="w-full h-0.5 bg-green-400 absolute animate-pulse" 
                                   style={{
                                     top: '50%'
                                   }}></div>
                            </div>
                          )}
                        </div>
                        
                        {/* Instructions */}
                        <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-75 text-white text-xs px-3 py-1 rounded-full whitespace-nowrap">
                          {autoScanEnabled ? '🎯 Scanning active' : '📱 Ready to scan'}
                        </div>
                      </div>
                    </div>
                    
                    {/* Status indicator */}
                    {autoScanEnabled && (
                      <div className="absolute top-3 left-3 bg-green-500 text-white text-xs px-3 py-1 rounded-full font-medium animate-pulse">
                        🔍 ZXing Active
                      </div>
                    )}
                  </div>
                  
                  {/* Camera Controls */}
                  <div className="flex space-x-2">
                    <button
                      onClick={stopScanning}
                      className="flex-1 bg-red-500 text-white py-3 rounded-lg hover:bg-red-600 transition-colors"
                    >
                      Stop Camera
                    </button>
                    
                    <button
                      onClick={() => {
                        cleanup();
                        setManualMode(true);
                      }}
                      className="bg-blue-500 text-white px-4 py-3 rounded-lg hover:bg-blue-600 transition-colors"
                      title="Switch to manual entry"
                    >
                      <Keyboard size={16} />
                    </button>
                  </div>
                </div>
              )}
              
              {/* Manual Entry Option within Camera Mode (Secondary) */}
              <div className="border-t pt-4">
                <div className="text-center mb-3">
                  <p className="text-sm text-gray-600">📱 Or enter barcode manually:</p>
                </div>
                
                <form onSubmit={handleManualSubmit} className="space-y-3">
                  <div className="relative">
                    <input
                      type="text"
                      value={barcode}
                      onChange={(e) => setBarcode(e.target.value)}
                      placeholder="Type barcode (e.g. 3222471081716)"
                      className="w-full px-3 py-3 border border-gray-300 rounded-lg text-center font-mono focus:ring-2 focus:ring-green-500"
                      disabled={loading}
                    />
                    {barcode && (
                      <button
                        type="button"
                        onClick={() => setBarcode('')}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                      >
                        <X size={16} />
                      </button>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="submit"
                      disabled={!barcode.trim() || loading}
                      className="bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-colors"
                    >
                      {loading ? '⚡ Finding...' : '🔍 Find'}
                    </button>
                    
                    <button
                      type="button"
                      onClick={() => setBarcode('3222471081716')}
                      className="bg-purple-500 text-white py-2 rounded-lg hover:bg-purple-600 transition-colors"
                      title="Test barcode"
                    >
                      📦 Test
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Full Manual Entry Mode (Only if explicitly requested) */}
          {manualMode && (
            <div className="space-y-4">
              <div className="text-center bg-gradient-to-r from-blue-50 to-green-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-800">⌨️ Manual Entry Only</h3>
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
            
            {/* Switch back to Camera Mode */}
            <div className="border-t pt-4">
              <button
                onClick={() => {
                  setManualMode(false);
                  setTimeout(() => startCamera(), 200);
                }}
                className="w-full bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center space-x-2"
              >
                <Camera size={16} />
                <span>📷 Back to Camera Scanner</span>
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
            <h4 className="font-medium text-gray-800 text-sm">💡 Scanner Tips</h4>
            <p className="text-xs text-gray-600 mt-1">
              Camera scanner is primary • Hold steady at barcode • Manual entry available as backup
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FixedMobileScanner;