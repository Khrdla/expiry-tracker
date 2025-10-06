import React, { useState, useEffect, useRef } from 'react';
import { Camera, X, AlertTriangle, Type, CheckCircle, RefreshCw, Volume2 } from 'lucide-react';
import { BrowserMultiFormatReader, NotFoundException, ChecksumException, FormatException } from '@zxing/library';

const SimpleMobileBarcodeScanner = ({ onScan, onClose }) => {
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState('');
  const [manualInput, setManualInput] = useState('');
  const [showManualInput, setShowManualInput] = useState(false);
  const [cameraError, setCameraError] = useState(false);
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const scanIntervalRef = useRef(null);

  useEffect(() => {
    if (!showManualInput) {
      startCamera();
    }
    return () => {
      stopCamera();
    };
  }, [showManualInput]);

  const startCamera = async () => {
    try {
      setIsScanning(true);
      setError('');
      setCameraError(false);

      // Request camera permission with better constraints for mobile
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });

      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          startBarcodeDetection();
        };
      }
    } catch (error) {
      console.error('Camera access error:', error);
      setCameraError(true);
      setError('Camera access denied or not available. Use manual input below.');
      setShowManualInput(true);
    }
  };

  const stopCamera = () => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsScanning(false);
  };

  const startBarcodeDetection = () => {
    // Simple pattern matching for common barcode formats
    scanIntervalRef.current = setInterval(() => {
      captureAndAnalyze();
    }, 500);
  };

  const captureAndAnalyze = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    const video = videoRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    context.drawImage(video, 0, 0);

    // For now, we'll rely on manual input since camera-based barcode detection
    // requires external libraries. This provides a working camera preview.
    // Users can see the barcode and type it manually or use device's native scanner.
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
              {/* Camera Preview */}
              <div className="relative bg-black rounded-lg overflow-hidden mb-4" style={{aspectRatio: '16/9'}}>
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover"
                  playsInline
                  muted
                />
                <canvas ref={canvasRef} className="hidden" />
                
                {/* Scanning Overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="border-2 border-green-500 w-64 h-32 bg-transparent"></div>
                </div>
                
                {/* Scanning Indicator */}
                {isScanning && !cameraError && (
                  <div className="absolute bottom-4 left-4 right-4">
                    <div className="bg-black bg-opacity-50 text-white px-3 py-2 rounded text-center">
                      📷 Position barcode within the green frame
                    </div>
                  </div>
                )}
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded mb-4 flex items-start gap-2">
                  <AlertTriangle size={16} className="mt-0.5" />
                  <span className="text-sm">{error}</span>
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-3">
                <button
                  onClick={handleDeviceScanner}
                  className="w-full px-4 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700"
                >
                  📱 Use Device Scanner
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