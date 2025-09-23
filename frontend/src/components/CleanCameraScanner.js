import React, { useState, useEffect, useRef } from 'react';
import { X, Camera, Keyboard, AlertCircle, CheckCircle, RotateCcw } from 'lucide-react';
import jsQR from 'jsqr';

const CleanCameraScanner = ({ isOpen, onClose, onProductFound }) => {
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [manualMode, setManualMode] = useState(false);
  const [barcode, setBarcode] = useState('');
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const scanIntervalRef = useRef(null);
  const canvasRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (isOpen) {
      setManualMode(false);
      setCameraActive(false);
      setError('');
      setSuccess('');
      setTimeout(startCamera, 300);
    } else {
      cleanup();
    }
    return cleanup;
  }, [isOpen]);

  const cleanup = () => {
    setScanning(false);
    
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
    setError('');
    setSuccess('');
  };

  const startCamera = async () => {
    try {
      setError('📱 Starting camera...');
      
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
        videoRef.current.srcObject = stream;
        videoRef.current.autoplay = true;
        videoRef.current.playsInline = true;
        videoRef.current.muted = true;
        
        videoRef.current.onloadedmetadata = async () => {
          try {
            await videoRef.current.play();
            setCameraActive(true);
            setError('');
            console.log('✅ Camera started');
            setTimeout(() => {
              startDetection();
            }, 1000);
          } catch (playErr) {
            console.error('Video play error:', playErr);
            setError('❌ Failed to start video');
          }
        };
        
        videoRef.current.onerror = (err) => {
          console.error('Video error:', err);
          setError('❌ Video stream error');
        };
      }
      
    } catch (err) {
      console.error('Camera error:', err);
      let errorMessage = '❌ Camera not available';
      if (err.name === 'NotAllowedError') {
        errorMessage = '📱 Camera permission denied. Please allow camera access.';
      } else if (err.name === 'NotFoundError') {
        errorMessage = '📱 No camera found on this device.';
      }
      setError(errorMessage);
      setCameraActive(false);
    }
  };

  const startDetection = () => {
    if (!videoRef.current || scanning) return;
    
    setScanning(true);
    setError('🎯 Scanning for barcodes...');
    
    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }
    
    scanIntervalRef.current = setInterval(() => {
      detectBarcode();
    }, 300);
  };

  const detectBarcode = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    if (!video || !canvas || video.readyState !== video.HAVE_ENOUGH_DATA) {
      return;
    }
    
    try {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const context = canvas.getContext('2d');
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
      
      const qrCode = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: 'dontInvert',
      });
      
      if (qrCode) {
        console.log('🎯 Barcode detected:', qrCode.data);
        stopDetection();
        setSuccess(`📱 Detected: ${qrCode.data}`);
        lookupProduct(qrCode.data);
        return;
      }
      
      // Visual feedback messages
      const messages = [
        '🔍 Scanning... Hold barcode steady',
        '📱 Position barcode in green frame',
        '💡 Ensure good lighting',
        '🎯 Try different angle'
      ];
      const randomMessage = messages[Math.floor(Math.random() * messages.length)];
      setError(randomMessage);
      
    } catch (err) {
      console.warn('Detection error:', err);
    }
  };

  const stopDetection = () => {
    setScanning(false);
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    setError('');
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
        setTimeout(() => {
          onProductFound(product);
          onClose();
        }, 1500);
      } else {
        setError('❌ Product not found');
      }
      
    } catch (err) {
      setError('❌ Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    if (!barcode.trim()) return;
    stopDetection();
    await lookupProduct(barcode.trim());
    setBarcode('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-green-500 to-blue-500">
          <div className="flex items-center space-x-2">
            <Camera size={20} className="text-white" />
            <div>
              <h2 className="text-lg font-bold text-white">📷 Camera Scanner</h2>
              <p className="text-xs text-green-100">Point and scan</p>
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
        <div className="p-4">
          
          {/* Camera Mode */}
          {!manualMode && (
            <div className="space-y-4">
              
              {/* Camera Display */}
              <div className="relative">
                <div className="bg-black rounded-lg overflow-hidden" style={{ height: '300px' }}>
                  <video
                    ref={videoRef}
                    className="w-full h-full object-cover"
                    autoPlay
                    playsInline
                    muted
                  />
                  
                  {/* Scanning Overlay */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="relative">
                      <div className="w-60 h-24 border-2 border-green-400 rounded-lg relative">
                        <div className="absolute -top-2 -left-2 w-6 h-6 border-l-4 border-t-4 border-green-400 rounded-tl-lg"></div>
                        <div className="absolute -top-2 -right-2 w-6 h-6 border-r-4 border-t-4 border-green-400 rounded-tr-lg"></div>
                        <div className="absolute -bottom-2 -left-2 w-6 h-6 border-l-4 border-b-4 border-green-400 rounded-bl-lg"></div>
                        <div className="absolute -bottom-2 -right-2 w-6 h-6 border-r-4 border-b-4 border-green-400 rounded-br-lg"></div>
                        
                        {scanning && (
                          <div className="absolute inset-x-0 top-1/2 h-0.5 bg-green-400 animate-pulse"></div>
                        )}
                      </div>
                      
                      <div className="absolute -bottom-10 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-75 text-white text-xs px-3 py-1 rounded-full">
                        {scanning ? 'Scanning active' : 'Ready to scan'}
                      </div>
                    </div>
                  </div>
                  
                  {cameraActive && (
                    <div className="absolute top-3 left-3 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                      📹 Live
                    </div>
                  )}
                  
                  {scanning && (
                    <div className="absolute top-3 right-3 bg-blue-500 text-white text-xs px-2 py-1 rounded-full animate-pulse">
                      🔍 Scanning
                    </div>
                  )}
                </div>
              </div>
              
              {/* Camera Controls */}
              <div className="space-y-3">
                {!cameraActive ? (
                  <button
                    onClick={startCamera}
                    className="w-full bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 transition-colors font-medium"
                  >
                    📷 Start Camera
                  </button>
                ) : (
                  <div className="space-y-2">
                    <div className="grid grid-cols-2 gap-3">
                      {!scanning ? (
                        <button
                          onClick={startDetection}
                          className="bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors font-medium"
                        >
                          🔍 Start Scan
                        </button>
                      ) : (
                        <button
                          onClick={stopDetection}
                          className="bg-red-500 text-white py-3 rounded-lg hover:bg-red-600 transition-colors font-medium"
                        >
                          ⏹️ Stop
                        </button>
                      )}
                      
                      <button
                        onClick={() => {
                          detectBarcode();
                        }}
                        className="bg-purple-500 text-white py-3 rounded-lg hover:bg-purple-600 transition-colors font-medium"
                      >
                        🎯 Force Detect
                      </button>
                    </div>
                    
                    <button
                      onClick={() => {
                        cleanup();
                        setTimeout(startCamera, 500);
                      }}
                      className="w-full bg-orange-500 text-white py-2 rounded-lg hover:bg-orange-600 transition-colors text-sm"
                    >
                      <RotateCcw size={14} className="inline mr-1" />
                      Restart Camera
                    </button>
                    
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => lookupProduct('3222471081716')}
                        className="bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors text-sm"
                      >
                        📦 Test Lookup
                      </button>
                      
                      <button
                        onClick={() => lookupProduct('3222474131326')}
                        className="bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
                      >
                        🥤 Test Energy
                      </button>
                    </div>
                  </div>
                )}
                
                <button
                  onClick={() => setManualMode(true)}
                  className="w-full bg-gray-500 text-white py-2 rounded-lg hover:bg-gray-600 transition-colors text-sm"
                >
                  <Keyboard size={14} className="inline mr-1" />
                  Manual Entry
                </button>
              </div>
            </div>
          )}

          {/* Manual Entry Mode */}
          {manualMode && (
            <div className="space-y-4">
              <div className="text-center bg-gray-50 p-3 rounded-lg">
                <h3 className="font-semibold text-gray-800">⌨️ Manual Entry</h3>
                <p className="text-sm text-gray-600">Type barcode number</p>
              </div>
              
              <form onSubmit={handleManualSubmit} className="space-y-3">
                <input
                  type="text"
                  value={barcode}
                  onChange={(e) => setBarcode(e.target.value)}
                  placeholder="Enter barcode (e.g. 3222471081716)"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg text-center font-mono focus:ring-2 focus:ring-green-500"
                  autoFocus
                />
                
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="submit"
                    disabled={!barcode.trim() || loading}
                    className="bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 disabled:opacity-50"
                  >
                    {loading ? '⚡ Finding...' : '🔍 Find'}
                  </button>
                  
                  <button
                    type="button"
                    onClick={() => setBarcode('3222471081716')}
                    className="bg-purple-500 text-white py-3 rounded-lg hover:bg-purple-600"
                  >
                    📦 Test
                  </button>
                </div>
              </form>
              
              <button
                onClick={() => {
                  setManualMode(false);
                  setTimeout(startCamera, 300);
                }}
                className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 text-sm"
              >
                📷 Back to Camera
              </button>
            </div>
          )}

          {/* Status Messages */}
          <div className="mt-4 space-y-2">
            {loading && (
              <div className="flex items-center justify-center space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                <span className="text-blue-700 text-sm">Searching...</span>
              </div>
            )}

            {error && (
              <div className="flex items-start space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <AlertCircle size={16} className="text-red-500 flex-shrink-0 mt-0.5" />
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

          {/* Tips */}
          <div className="mt-4 bg-gray-50 p-3 rounded-lg text-center">
            <p className="text-gray-600 text-xs">
              💡 Hold barcode steady • Good lighting • 6-8 inches distance
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CleanCameraScanner;