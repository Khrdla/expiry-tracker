import React, { useState, useEffect, useRef } from 'react';
import { Camera, X, AlertTriangle, Type, CheckCircle, RefreshCw, Volume2 } from 'lucide-react';
import { BrowserMultiFormatReader, NotFoundException, ChecksumException, FormatException } from '@zxing/library';

const SimpleMobileBarcodeScanner = ({ onScan, onClose }) => {
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState('');
  const [manualInput, setManualInput] = useState('');
  const [showManualInput, setShowManualInput] = useState(false);
  const [cameraError, setCameraError] = useState(false);
  const [scanSuccess, setScanSuccess] = useState(false);
  const [lastScanTime, setLastScanTime] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const [scanStatus, setScanStatus] = useState('');
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const codeReaderRef = useRef(null);
  const animationFrameRef = useRef(null);

  useEffect(() => {
    if (!showManualInput) {
      initializeScanner();
    }
    return () => {
      cleanup();
    };
  }, [showManualInput]);

  const initializeScanner = async () => {
    try {
      setIsScanning(true);
      setError('');
      setCameraError(false);
      setScanStatus('🔍 Initializing camera...');

      // Initialize ZXing barcode reader with multiple format support
      codeReaderRef.current = new BrowserMultiFormatReader();
      
      // Get available video devices
      const videoDevices = await codeReaderRef.current.listVideoInputDevices();
      
      if (videoDevices.length === 0) {
        throw new Error('No camera devices found');
      }

      // Try to use back camera on mobile devices
      let selectedDeviceId = videoDevices[0].deviceId;
      for (const device of videoDevices) {
        if (device.label.toLowerCase().includes('back') || 
            device.label.toLowerCase().includes('rear') ||
            device.label.toLowerCase().includes('environment')) {
          selectedDeviceId = device.deviceId;
          break;
        }
      }

      setScanStatus('📷 Starting camera...');
      
      // Start decoding from video device
      await codeReaderRef.current.decodeFromVideoDevice(
        selectedDeviceId,
        videoRef.current,
        (result, error) => {
          if (result) {
            handleBarcodeDetected(result.getText());
          } else if (error) {
            // Only log non-routine scanning errors
            if (!(error instanceof NotFoundException)) {
              console.log('Scan error:', error);
            }
            
            // Update scan status for user feedback
            const now = Date.now();
            if (now - lastScanTime > 2000) { // Update status every 2 seconds
              setScanStatus('🎯 Position barcode in center frame');
              setLastScanTime(now);
            }
          }
        }
      );

      setScanStatus('✅ Scanner active - position barcode in frame');
      
    } catch (error) {
      console.error('Scanner initialization error:', error);
      setCameraError(true);
      
      let errorMessage = 'Camera not available. ';
      if (error.name === 'NotAllowedError') {
        errorMessage = 'Camera permission denied. Please allow camera access and try again.';
      } else if (error.name === 'NotFoundError') {
        errorMessage = 'No camera found on this device.';
      } else if (error.name === 'NotSupportedError') {
        errorMessage = 'Camera not supported in this browser.';
      }
      
      setError(errorMessage);
      setScanStatus('❌ Camera unavailable');
      setShowManualInput(true);
    }
  };

  const handleBarcodeDetected = (barcodeText) => {
    if (barcodeText && barcodeText.trim()) {
      // Prevent duplicate scans within 1 second
      const now = Date.now();
      if (now - lastScanTime < 1000) {
        return;
      }
      setLastScanTime(now);

      console.log('Barcode detected:', barcodeText);
      
      // Play success feedback
      playSuccessBeep();
      showSuccessFlash();
      
      // Call parent callback with detected barcode
      onScan(barcodeText.trim());
    }
  };

  const playSuccessBeep = () => {
    try {
      // Create success beep sound
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      // Higher pitch for success
      oscillator.frequency.setValueAtTime(1200, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.1);
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    } catch (error) {
      console.log('Audio not available:', error);
    }
  };

  const showSuccessFlash = () => {
    setScanSuccess(true);
    setTimeout(() => setScanSuccess(false), 500);
  };

  const cleanup = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (codeReaderRef.current) {
      codeReaderRef.current.reset();
      codeReaderRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsScanning(false);
  };

  const retryScanning = () => {
    setRetryCount(prev => prev + 1);
    setError('');
    setCameraError(false);
    setShowManualInput(false);
    initializeScanner();
  };

  const handleManualSubmit = () => {
    if (manualInput.trim()) {
      onScan(manualInput.trim());
      onClose();
    }
  };

  const handleDeviceScanner = () => {
    // Trigger device's native barcode scanner if available
    if ('BarcodeDetector' in window) {
      // Use native BarcodeDetector API if supported
      const barcodeDetector = new window.BarcodeDetector();
      // Implementation would go here
    } else {
      // Fallback: Prompt user to use device's camera app
      alert('Please use your device\'s camera app to scan the barcode, then enter it manually below.');
      setShowManualInput(true);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-md w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-blue-600 text-white p-4 flex justify-between items-center">
          <h3 className="text-lg font-semibold">📷 Scan Barcode</h3>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200"
          >
            <X size={24} />
          </button>
        </div>

        {/* Camera or Manual Input */}
        <div className="p-4">
          {!showManualInput ? (
            <div>
              {/* Camera Preview with Enhanced Overlay */}
              <div className={`relative bg-black rounded-lg overflow-hidden mb-4 transition-all duration-300 ${
                scanSuccess ? 'ring-4 ring-green-500' : ''
              }`} style={{aspectRatio: '16/9'}}>
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover"
                  playsInline
                  muted
                  autoPlay
                />
                
                {/* Success Flash Overlay */}
                {scanSuccess && (
                  <div className="absolute inset-0 bg-green-500 opacity-50 animate-pulse"></div>
                )}
                
                {/* Scanning Frame */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative">
                    {/* Main scanning frame */}
                    <div className={`border-2 w-64 h-32 bg-transparent transition-colors duration-200 ${
                      scanSuccess ? 'border-green-400' : 'border-blue-400'
                    }`}>
                      {/* Corner markers */}
                      <div className="absolute -top-1 -left-1 w-6 h-6 border-l-4 border-t-4 border-white"></div>
                      <div className="absolute -top-1 -right-1 w-6 h-6 border-r-4 border-t-4 border-white"></div>
                      <div className="absolute -bottom-1 -left-1 w-6 h-6 border-l-4 border-b-4 border-white"></div>
                      <div className="absolute -bottom-1 -right-1 w-6 h-6 border-r-4 border-b-4 border-white"></div>
                    </div>
                    
                    {/* Scanning line animation */}
                    {isScanning && !cameraError && (
                      <div className="absolute inset-0 overflow-hidden">
                        <div className="w-full h-0.5 bg-red-500 animate-pulse"></div>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Status Indicator */}
                {scanStatus && (
                  <div className="absolute top-4 left-4 right-4">
                    <div className={`px-3 py-2 rounded text-center text-sm font-medium ${
                      scanStatus.includes('✅') ? 'bg-green-500 text-white' :
                      scanStatus.includes('❌') ? 'bg-red-500 text-white' :
                      'bg-black bg-opacity-70 text-white'
                    }`}>
                      {scanStatus}
                    </div>
                  </div>
                )}
                
                {/* Supported formats indicator */}
                <div className="absolute bottom-4 left-4 right-4">
                  <div className="bg-black bg-opacity-70 text-white px-3 py-2 rounded text-center text-xs">
                    📊 Supports: CODE128, EAN13/8, UPC, QR codes
                  </div>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded mb-4 flex items-start gap-2">
                  <AlertTriangle size={16} className="mt-0.5" />
                  <div>
                    <div className="font-medium">Camera Error</div>
                    <div className="text-sm">{error}</div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-3">
                {cameraError && (
                  <button
                    onClick={retryScanning}
                    className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 flex items-center justify-center gap-2"
                  >
                    <RefreshCw size={16} />
                    Retry Camera (Attempt {retryCount + 1})
                  </button>
                )}
                
                <button
                  onClick={handleDeviceScanner}
                  className="w-full px-4 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700"
                >
                  📱 Use Device Scanner App
                </button>
                
                <button
                  onClick={() => setShowManualInput(true)}
                  className="w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 flex items-center justify-center gap-2"
                >
                  <Type size={16} />
                  Enter Barcode Manually
                </button>
              </div>
            </div>
          ) : (
            <div>
              {/* Manual Input */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter Barcode Number
                </label>
                <input
                  type="text"
                  value={manualInput}
                  onChange={(e) => setManualInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleManualSubmit();
                    }
                  }}
                  placeholder="Type or paste barcode here"
                  className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-lg"
                  autoFocus
                />
              </div>

              <div className="space-y-3">
                <button
                  onClick={handleManualSubmit}
                  disabled={!manualInput.trim()}
                  className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <CheckCircle size={16} />
                  Use This Barcode
                </button>
                
                {!cameraError && (
                  <button
                    onClick={() => setShowManualInput(false)}
                    className="w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 flex items-center justify-center gap-2"
                  >
                    <Camera size={16} />
                    Back to Camera
                  </button>
                )}
              </div>

              {/* Instructions */}
              <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-blue-700 text-sm">
                  💡 <strong>Tip:</strong> You can also use your device's camera app to scan the barcode, then copy and paste the number here.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SimpleMobileBarcodeScanner;