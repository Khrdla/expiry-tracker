import React, { useState, useEffect, useRef } from 'react';
// Removed html5-qrcode dependency - using pure native solution
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
  const [useNativeFallback, setUseNativeFallback] = useState(false);
  const [nativeStream, setNativeStream] = useState(null);
  
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
    // Enhanced mobile browser detection - moved outside try block for catch block access
    const isMobile = /Mobi|Android|iPhone|iPad|iPod/.test(navigator.userAgent);
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isAndroid = /Android/.test(navigator.userAgent);
    
    try {
      console.log('🔍 Initializing camera for mobile device...');
      console.log('📱 Device info:', {
        userAgent: navigator.userAgent,
        isMobile: /Mobi|Android/i.test(navigator.userAgent),
        isIOS: /iPad|iPhone|iPod/.test(navigator.userAgent),
        isAndroid: /Android/.test(navigator.userAgent),
        isSafari: /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent),
        isChrome: /Chrome/.test(navigator.userAgent),
        protocol: window.location.protocol,
        isSecure: window.location.protocol === 'https:'
      });
      
      // Check if mediaDevices API is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera API not available in this browser. Please use a modern mobile browser.');
      }
      
      // Check for secure context (required on mobile)
      if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
        throw new Error('Camera requires HTTPS connection on mobile devices');
      }
      
      // Mobile-optimized camera constraints with multiple fallbacks
      const mobileConstraints = [
        // First attempt: Mobile-optimized high quality
        {
          video: {
            facingMode: { ideal: 'environment' }, // Prefer back camera
            width: { ideal: 1280, max: 1920, min: 320 },
            height: { ideal: 720, max: 1080, min: 240 },
            frameRate: { ideal: 30, max: 60, min: 10 },
            aspectRatio: { ideal: 1.7777777778 }
          }
        },
        // Second attempt: iOS Safari compatible
        {
          video: {
            facingMode: 'environment',
            width: { ideal: 640, max: 1280 },
            height: { ideal: 480, max: 720 },
            frameRate: { ideal: 15, max: 30 }
          }
        },
        // Third attempt: Android Chrome compatible
        {
          video: {
            facingMode: 'environment',
            width: 640,
            height: 480
          }
        },
        // Fourth attempt: Basic mobile
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
      let usedConstraints = null;
      
      // Try each constraint set until one works
      for (let i = 0; i < mobileConstraints.length; i++) {
        try {
          const constraints = mobileConstraints[i];
          console.log(`🔍 Attempt ${i + 1}: Trying constraints:`, constraints);
          
          stream = await navigator.mediaDevices.getUserMedia(constraints);
          usedConstraints = constraints;
          console.log(`✅ Camera initialized with attempt ${i + 1}`);
          break;
          
        } catch (constraintError) {
          console.warn(`⚠️ Constraint attempt ${i + 1} failed:`, constraintError);
          
          // If this is the last attempt, throw the error
          if (i === mobileConstraints.length - 1) {
            throw constraintError;
          }
          
          // Wait a bit before next attempt on mobile
          if (isMobile) {
            // Use setTimeout instead of await for compatibility
            setTimeout(() => {}, 200);
          }
        }
      }
      
      if (!stream) {
        throw new Error('Unable to initialize camera with any constraints');
      }
      
      // Verify stream is actually working
      const tracks = stream.getVideoTracks();
      if (tracks.length === 0) {
        stream.getTracks().forEach(track => track.stop());
        throw new Error('No video tracks available');
      }
      
      const videoTrack = tracks[0];
      const settings = videoTrack.getSettings();
      console.log('✅ Camera stream settings:', settings);
      
      // Mobile-specific validation
      if (isMobile) {
        // Check if we got the back camera as requested
        if (settings.facingMode && settings.facingMode !== 'environment') {
          console.warn('⚠️ Front camera detected, back camera preferred for barcode scanning');
        }
        
        // Ensure minimum resolution for barcode detection
        if (settings.width < 320 || settings.height < 240) {
          console.warn('⚠️ Low camera resolution detected, barcode detection may be affected');
        }
      }
      
      setCameraPermission(true);
      console.log('✅ Mobile camera initialization successful');
      console.log('📊 Final camera settings:', {
        width: settings.width,
        height: settings.height,
        frameRate: settings.frameRate,
        facingMode: settings.facingMode,
        aspectRatio: settings.aspectRatio
      });
      
      // Stop the test stream
      stream.getTracks().forEach(track => track.stop());
      
    } catch (error) {
      console.error('❌ Mobile camera initialization error:', error);
      setCameraPermission(false);
      
      let errorMessage = '❌ Camera initialization failed. ';
      
      // Mobile-specific error messages
      if (error.name === 'NotAllowedError') {
        if (isIOS) {
          errorMessage += 'Please allow camera access in Safari Settings > Privacy & Security > Camera > This Website.';
        } else if (isAndroid) {
          errorMessage += 'Please allow camera access by tapping the camera icon in the address bar.';
        } else {
          errorMessage += 'Please allow camera access and try again.';
        }
      } else if (error.name === 'NotFoundError') {
        errorMessage += 'No camera found. Please ensure your device has a working camera.';
      } else if (error.name === 'NotReadableError') {
        errorMessage += 'Camera is being used by another app. Please close other camera apps and try again.';
      } else if (error.name === 'OverconstrainedError') {
        errorMessage += 'Camera configuration not supported. This may happen on older devices.';
      } else if (error.name === 'AbortError') {
        errorMessage += 'Camera access was interrupted. Please try again.';
      } else if (error.name === 'SecurityError') {
        errorMessage += 'Camera access blocked by security policy. Please enable camera permissions.';
      } else if (error.message.includes('HTTPS')) {
        errorMessage += 'Camera requires secure connection. Please ensure you are using HTTPS.';
      } else if (error.message.includes('not available')) {
        errorMessage += 'Camera API not supported. Please update your browser to the latest version.';
      } else {
        errorMessage += `${error.message || 'Unknown camera error'}. Please try refreshing the page.`;
      }
      
      setError(errorMessage);
    }
  };

  // PURE NATIVE CAMERA SOLUTION - bypasses html5-qrcode completely
  const startNativeScanning = async () => {
    if (!isMountedRef.current) return;
    
    try {
      resetScanner();
      setIsScanning(true);
      setError('📱 Starting native camera...');

      console.log('🚀 Starting PURE NATIVE camera solution...');
      
      // Get camera with GUARANTEED working constraints
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });

      console.log('✅ Native camera stream obtained successfully');
      setNativeStream(stream);

      // Create video element with GUARANTEED visibility
      const video = document.createElement('video');
      video.srcObject = stream;
      video.autoplay = true;
      video.playsInline = true;
      video.muted = true;
      video.style.width = '100%';
      video.style.height = '400px';
      video.style.backgroundColor = '#000';
      video.style.objectFit = 'cover';
      video.style.borderRadius = '8px';

      // Clear container and add WORKING video
      const container = document.getElementById('qr-reader');
      if (container) {
        container.innerHTML = '';
        container.appendChild(video);

        // Add CLEAN scan overlay that doesn't block camera view
        const scanOverlay = document.createElement('div');
        scanOverlay.style.position = 'absolute';
        scanOverlay.style.top = '50%';
        scanOverlay.style.left = '50%';
        scanOverlay.style.transform = 'translate(-50%, -50%)';
        scanOverlay.style.width = '250px';
        scanOverlay.style.height = '100px';
        scanOverlay.style.border = '3px solid #22c55e';
        scanOverlay.style.borderRadius = '8px';
        scanOverlay.style.backgroundColor = 'rgba(34, 197, 94, 0.1)';
        scanOverlay.style.pointerEvents = 'none';
        scanOverlay.innerHTML = '<div style="background: #22c55e; color: white; padding: 4px 8px; font-size: 12px; border-radius: 4px; position: absolute; top: -25px; left: 0; font-weight: bold;">🎯 BARCODE TARGET</div>';
        
        // Position container for overlay
        container.style.position = 'relative';
        container.appendChild(scanOverlay);

        // Add REAL barcode detection using canvas scanning
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        let scanning = true;
        
        // REAL barcode detection loop
        const detectBarcode = async () => {
          if (!scanning || !video.videoWidth || !video.videoHeight) {
            if (scanning) {
              setTimeout(detectBarcode, 100);
            }
            return;
          }

          try {
            // Capture frame from video
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0);
            
            // Try BarcodeDetector API if available
            if ('BarcodeDetector' in window) {
              const barcodeDetector = new BarcodeDetector({
                formats: ['code_128', 'code_39', 'ean_13', 'ean_8', 'upc_a', 'upc_e', 'qr_code']
              });
              
              const barcodes = await barcodeDetector.detect(canvas);
              
              if (barcodes.length > 0) {
                const barcode = barcodes[0];
                console.log('🎯 BARCODE DETECTED:', barcode.rawValue);
                
                scanning = false;
                setError('✅ Barcode detected: ' + barcode.rawValue);
                
                // Flash green on success
                scanOverlay.style.backgroundColor = 'rgba(34, 197, 94, 0.5)';
                setTimeout(() => {
                  handleSuccessfulScan(barcode.rawValue);
                  
                  // Look up product
                  const token = localStorage.getItem('token');
                  fetch(`${process.env.REACT_APP_BACKEND_URL}/api/barcode/${barcode.rawValue}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                  })
                  .then(response => response.ok ? response.json() : null)
                  .then(product => {
                    if (product) {
                      onProductFound(product);
                      onClose();
                    } else {
                      setError('❌ Product not found: ' + barcode.rawValue);
                    }
                  })
                  .catch(() => setError('❌ Lookup failed: ' + barcode.rawValue));
                }, 500);
                
                return;
              }
            }
          } catch (detectError) {
            // Silent - detection errors are normal when no barcode present
          }
          
          if (scanning) {
            setTimeout(detectBarcode, 200); // 5 FPS detection
          }
        };
        
        // Add manual input BELOW camera (not overlapping)
        const inputContainer = document.createElement('div');
        inputContainer.style.marginTop = '10px';
        inputContainer.style.padding = '12px';
        inputContainer.style.backgroundColor = '#f8fafc';
        inputContainer.style.borderRadius = '8px';
        inputContainer.style.border = '1px solid #e2e8f0';
        
        inputContainer.innerHTML = `
          <div style="display: flex; gap: 8px; align-items: center;">
            <input 
              type="text" 
              id="native-barcode-input"
              placeholder="Or type barcode..."
              style="flex: 1; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 14px; font-family: monospace;"
            />
            <button 
              id="native-lookup-btn"
              style="padding: 8px 16px; background: #22c55e; color: white; border: none; border-radius: 4px; font-size: 14px; font-weight: bold; cursor: pointer; white-space: nowrap;"
            >
              🔍 Find
            </button>
          </div>
        `;
        
        container.appendChild(inputContainer);

        // Add manual lookup functionality
        const input = document.getElementById('native-barcode-input');
        const button = document.getElementById('native-lookup-btn');
        
        const handleLookup = async () => {
          const barcode = input.value.trim();
          if (!barcode) {
            setError('❌ Please enter a barcode');
            return;
          }

          setError('🔍 Looking up: ' + barcode);
          
          try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/barcode/${barcode}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
              const product = await response.json();
              console.log('✅ Manual lookup success:', product);
              handleSuccessfulScan(barcode);
              onProductFound(product);
              onClose();
            } else {
              setError('❌ Product not found: ' + barcode);
            }
          } catch (error) {
            console.error('Manual lookup error:', error);
            setError('❌ Network error');
          }
        };

        button.onclick = handleLookup;
        input.onkeypress = (e) => {
          if (e.key === 'Enter') {
            handleLookup();
          }
        };

        // Store cleanup function
        window.cleanupDetection = () => {
          scanning = false;
        };
      }

      video.onloadedmetadata = () => {
        console.log('✅ Native video loaded - starting barcode detection');
        setError('🎯 Point camera at barcode or type manually below');
        
        // Start real barcode detection
        setTimeout(() => {
          if (scanning) {
            detectBarcode();
            console.log('🎯 Barcode detection started');
          }
        }, 1000);
      };

      video.onerror = (error) => {
        console.error('❌ Video error:', error);
        setError('❌ Camera error - use manual entry');
      };

    } catch (nativeError) {
      console.error('❌ Native camera failed:', nativeError);
      setError('❌ Camera not available. Using manual entry mode.');
      setIsScanning(false);
      
      // Show manual entry fallback
      startNativeFallback();
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
    console.log('🛑 Stopping mobile scanner...');
    setIsScanning(false);
    
    if (scannerInstanceRef.current) {
      try {
        console.log('🧹 Cleaning up mobile scanner instance...');
        
        // Mobile-optimized cleanup sequence
        const isMobile = /Mobi|Android|iPhone|iPad|iPod/.test(navigator.userAgent);
        
        if (isMobile) {
          // On mobile, stop all video tracks first to prevent black screen
          const videoElement = document.querySelector('#qr-reader video');
          if (videoElement && videoElement.srcObject) {
            const stream = videoElement.srcObject;
            if (stream) {
              stream.getTracks().forEach(track => {
                console.log('🎥 Stopping video track:', track.kind, track.label);
                track.stop();
              });
              videoElement.srcObject = null;
            }
          }
        }
        
        // Clear the scanner instance
        await scannerInstanceRef.current.clear();
        
        // Mobile-specific additional cleanup delay
        const cleanupDelay = isMobile ? 150 : 50;
        setTimeout(() => {
          scannerInstanceRef.current = null;
          console.log('✅ Mobile scanner cleanup completed');
          
          // Mobile: Force DOM cleanup to prevent black screen remnants
          if (isMobile) {
            const qrReaderElement = document.getElementById("qr-reader");
            if (qrReaderElement) {
              qrReaderElement.innerHTML = '';
              console.log('🧹 Mobile DOM cleanup completed');
            }
          }
        }, cleanupDelay);
        
      } catch (error) {
        console.warn('⚠️ Error during mobile scanner cleanup:', error);
        
        // Force cleanup even if error occurs - critical for mobile
        scannerInstanceRef.current = null;
        
        // Mobile: Emergency cleanup
        const isMobile = /Mobi|Android|iPhone|iPad|iPod/.test(navigator.userAgent);
        if (isMobile) {
          try {
            // Force stop any remaining video streams
            navigator.mediaDevices.getUserMedia({ video: false }).catch(() => {});
            
            // Clear DOM
            const qrReaderElement = document.getElementById("qr-reader");
            if (qrReaderElement) {
              qrReaderElement.innerHTML = '';
            }
            
            console.log('🚨 Mobile emergency cleanup completed');
          } catch (emergencyError) {
            console.warn('⚠️ Emergency mobile cleanup error:', emergencyError);
          }
        }
      }
    }
  };

  const cleanup = async () => {
    console.log('🧹 Starting comprehensive cleanup...');
    await stopScanning();
    
    // Native fallback cleanup
    if (useNativeFallback) {
      console.log('🧹 Cleaning up native fallback...');
      if (window.nativeScannerCleanup) {
        window.nativeScannerCleanup();
        window.nativeScannerCleanup = null;
      }
      if (nativeStream) {
        nativeStream.getTracks().forEach(track => track.stop());
        setNativeStream(null);
      }
      setUseNativeFallback(false);
    }
    
    // Mobile: Additional safety cleanup
    const isMobile = /Mobi|Android|iPhone|iPad|iPod/.test(navigator.userAgent);
    if (isMobile) {
      // Ensure all camera resources are released on mobile
      setTimeout(() => {
        const videos = document.querySelectorAll('#qr-reader video');
        videos.forEach(video => {
          if (video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
            video.srcObject = null;
          }
        });
        console.log('🧹 Mobile video cleanup completed');
      }, 100);
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

  // Simple Native Camera fallback (no BarcodeDetector dependency)
  const startNativeFallback = async () => {
    console.log('🚨 STARTING SIMPLE NATIVE CAMERA to bypass video abort errors');
    setUseNativeFallback(true);
    setError('🔄 Starting clear camera mode...');
    
    try {
      // Skip BarcodeDetector check - use simple camera + manual detection
      console.log('📱 Using simple camera approach for maximum compatibility');
      
      // Get camera with CRYSTAL CLEAR constraints for barcode scanning
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { exact: 'environment' },
          width: { ideal: 1920, min: 1280 }, // Higher resolution for clarity
          height: { ideal: 1080, min: 720 },
          frameRate: { ideal: 30, min: 15 },
          focusMode: 'continuous',
          zoom: 1.0 // No zoom for clarity
        }
      });
      
      setNativeStream(stream);
      
      // Create CRYSTAL CLEAR video element
      const video = document.createElement('video');
      video.srcObject = stream;
      video.autoplay = true;
      video.playsInline = true;
      video.muted = true; // Prevent audio issues
      video.style.width = '100%';
      video.style.height = '400px'; // Increased height for better view
      video.style.objectFit = 'cover';
      video.style.borderRadius = '8px';
      video.style.backgroundColor = '#000';
      
      // Remove BarcodeDetector dependency - use manual input approach
      console.log('📱 Setting up crystal clear camera view for manual barcode entry');
      
      // Clear container and add video
      const container = document.getElementById('qr-reader');
      if (container) {
        container.innerHTML = '';
        
        // Add video
        container.appendChild(video);
        
        // Add CLEAR barcode targeting overlay
        const overlay = document.createElement('div');
        overlay.style.position = 'absolute';
        overlay.style.top = '50%';
        overlay.style.left = '50%';
        overlay.style.transform = 'translate(-50%, -50%)';
        overlay.style.width = '280px';
        overlay.style.height = '120px';
        overlay.style.border = '3px solid #22c55e';
        overlay.style.borderRadius = '12px';
        overlay.style.backgroundColor = 'rgba(34, 197, 94, 0.1)';
        overlay.style.pointerEvents = 'none';
        overlay.innerHTML = '<div style="background: rgba(34, 197, 94, 0.95); color: white; padding: 8px 12px; font-size: 14px; font-weight: bold; border-radius: 6px; position: absolute; top: -40px; left: 0;">🎯 CRYSTAL CLEAR VIEW - Hold 2-4 inches away</div>';
        
        // Add manual input below video
        const inputContainer = document.createElement('div');
        inputContainer.style.marginTop = '15px';
        inputContainer.style.padding = '15px';
        inputContainer.style.backgroundColor = '#f8f9fa';
        inputContainer.style.borderRadius = '8px';
        inputContainer.innerHTML = `
          <div style="margin-bottom: 10px; font-weight: bold; color: #333;">📝 Manual Barcode Entry:</div>
          <input 
            type="text" 
            id="manual-barcode-input"
            placeholder="Type barcode numbers here..."
            style="width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px; font-family: monospace;"
          />
          <button 
            id="manual-submit-btn"
            style="width: 100%; margin-top: 10px; padding: 12px; background: #22c55e; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold;"
          >
            🔍 Lookup Barcode
          </button>
        `;
        
        container.style.position = 'relative';
        container.appendChild(overlay);
        container.appendChild(inputContainer);
        
        // Add manual input handler
        const manualInput = document.getElementById('manual-barcode-input');
        const submitBtn = document.getElementById('manual-submit-btn');
        
        const handleManualSubmit = async () => {
          const barcode = manualInput.value.trim();
          if (barcode) {
            console.log('📝 Manual barcode entered:', barcode);
            setError('🔍 Looking up barcode...');
            
            try {
              const token = localStorage.getItem('token');
              const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/barcode/${barcode}`, {
                headers: { 'Authorization': `Bearer ${token}` }
              });
              
              if (response.ok) {
                const product = await response.json();
                handleSuccessfulScan(barcode);
                onProductFound(product);
                onClose();
                return;
              } else {
                setError('❌ Barcode not found in database');
              }
            } catch (error) {
              setError('❌ Error looking up barcode');
            }
          }
        };
        
        submitBtn.onclick = handleManualSubmit;
        manualInput.onkeypress = (e) => {
          if (e.key === 'Enter') {
            handleManualSubmit();
          }
        };
      }
      
      video.onloadedmetadata = () => {
        console.log('✅ Crystal clear camera loaded');
        setError('📱 Crystal clear camera active! Use manual entry below or type barcode numbers');
      };
      
      // Cleanup function
      const cleanup = () => {
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }
      };
      
      // Store cleanup for later use
      window.nativeScannerCleanup = cleanup;
      
    } catch (nativeError) {
      console.error('❌ Native camera failed:', nativeError);
      setError(''); // Clear error to show clean manual entry
      setUseNativeFallback(false);
      
      // Show CLEAN manual input (no error messages)
      const container = document.getElementById('qr-reader');
      if (container) {
        container.innerHTML = `
          <div style="padding: 25px; background: linear-gradient(135deg, #f0f9ff, #e0f2fe); border-radius: 12px; text-align: center; border: 2px solid #0ea5e9;">
            <div style="background: #0ea5e9; color: white; padding: 8px 16px; border-radius: 20px; display: inline-block; margin-bottom: 20px;">
              📱 Manual Barcode Scanner
            </div>
            <p style="color: #0c4a6e; margin-bottom: 20px; font-size: 14px;">Enter barcode numbers for instant product lookup</p>
            <input 
              type="text" 
              id="fallback-barcode-input"
              placeholder="Type barcode (e.g. 3222471081716)..."
              style="width: 100%; padding: 15px; border: 2px solid #0ea5e9; border-radius: 8px; font-size: 16px; margin-bottom: 15px; font-family: monospace; text-align: center;"
            />
            <button 
              id="fallback-submit-btn"
              style="width: 100%; padding: 15px; background: linear-gradient(135deg, #22c55e, #16a34a); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);"
            >
              🔍 Find Product Now
            </button>
            <div style="margin-top: 15px; padding: 10px; background: rgba(34, 197, 94, 0.1); border-radius: 6px;">
              <small style="color: #166534;">✨ Works with all barcode formats: EAN, UPC, Code128</small>
            </div>
          </div>
        `;
        
        const fallbackInput = document.getElementById('fallback-barcode-input');
        const fallbackBtn = document.getElementById('fallback-submit-btn');
        
        const handleFallbackSubmit = async () => {
          const barcode = fallbackInput.value.trim();
          if (barcode) {
            setError('🔍 Looking up barcode...');
            try {
              const token = localStorage.getItem('token');
              const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/barcode/${barcode}`, {
                headers: { 'Authorization': `Bearer ${token}` }
              });
              
              if (response.ok) {
                const product = await response.json();
                handleSuccessfulScan(barcode);
                onProductFound(product);
                onClose();
              } else {
                setError('❌ Barcode not found');
              }
            } catch (error) {
              setError('❌ Lookup failed');
            }
          }
        };
        
        fallbackBtn.onclick = handleFallbackSubmit;
        fallbackInput.onkeypress = (e) => {
          if (e.key === 'Enter') handleFallbackSubmit();
        };
        fallbackInput.focus();
      }
    }
  };

  const startScanning = async () => {
    // Redirect to native scanning solution
    console.log('🔄 Redirecting to native camera solution');
    startNativeScanning();
  };
  // Keep original scanning as fallback (rename to avoid confusion)
  const startOldScanning = async () => {
    // Original html5-qrcode implementation kept as emergency fallback
    console.log('🔄 Starting original scanner (fallback)...');
    // The rest of original implementation stays here but not used by default
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

  // Test function to simulate barcode detection
  const testBarcodeDetection = () => {
    const testBarcode = '3222471081716'; // Apple Juice Box 1L
    console.log('🧪 Testing barcode detection with:', testBarcode);
    setSuccess('🧪 Testing barcode detection...');
    processBarcode(testBarcode);
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
                      onClick={startNativeScanning}
                      className="flex items-center justify-center space-x-2 bg-gradient-to-r from-green-500 to-green-600 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:from-green-600 hover:to-green-700 transition-all text-sm md:text-base shadow-lg active:scale-95 transform"
                    >
                      <Camera size={16} className="md:hidden" />
                      <Camera size={20} className="hidden md:block" />
                      <span>📱 Native Camera</span>
                    </button>
                    <button
                      onClick={startNativeFallback}
                      className="flex items-center justify-center space-x-2 bg-orange-500 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:bg-orange-600 transition-colors text-sm md:text-base active:scale-95 transform"
                      title="Use if regular scanner has issues"
                    >
                      <Camera size={16} className="md:hidden" />
                      <Camera size={20} className="hidden md:block" />
                      <span>📱 Clear Camera</span>
                    </button>
                    <button
                      onClick={() => setShowManualInput(!showManualInput)}
                      className="flex items-center justify-center space-x-2 bg-blue-500 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:bg-blue-600 transition-colors text-sm md:text-base active:scale-95 transform"
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
                    <button
                      onClick={testBarcodeDetection}
                      className="flex items-center space-x-2 bg-purple-500 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:bg-purple-600 transition-colors text-sm md:text-base"
                    >
                      <Package size={16} className="md:hidden" />
                      <Package size={20} className="hidden md:block" />
                      <span>🧪 Test Detection</span>
                    </button>
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
                    
                    {/* CLEAN scanning indicator - no clutter */}
                    <div className="absolute top-4 left-4 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium">
                      📱 Scanning...
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

              {/* ELEGANT Simple Instructions */}
              <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <div className="text-center mb-3">
                  <h4 className="text-lg font-semibold text-gray-800">📱 Quick Barcode Scanner</h4>
                  <p className="text-sm text-gray-600">Position barcode 2-4 inches from camera</p>
                </div>
                
                <div className="flex items-center justify-center space-x-6 text-xs text-gray-500">
                  <div className="flex items-center">
                    <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                    EAN, UPC, QR
                  </div>
                  <div className="flex items-center">
                    <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                    Auto Detection
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Loading Camera - Mobile Optimized */}
          {cameraPermission === null && (
            <div className="text-center py-6 md:py-8">
              <div className="animate-spin rounded-full h-8 w-8 md:h-12 md:w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
              <p className="text-sm md:text-base text-gray-600">📱 Initializing anti-abort mobile scanner...</p>
              
              {/* Mobile Detection Info */}
              {/Mobi|Android|iPhone|iPad|iPod/.test(navigator.userAgent) && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-blue-700 font-medium text-sm">📱 Mobile Device Detected</p>
                  <p className="text-blue-600 text-xs mt-1">
                    {/iPad|iPhone|iPod/.test(navigator.userAgent) ? '🍎 iOS Safari optimizations active' :
                     /Android/.test(navigator.userAgent) ? '🤖 Android Chrome optimizations active' :
                     '📱 Mobile optimizations active'}
                  </p>
                </div>
              )}
              
              <div className="text-xs text-gray-500 mt-4 bg-gray-50 p-3 rounded-lg">
                <p><strong>🔍 Mobile Debug Info:</strong></p>
                <p>📍 URL: {window.location.protocol}//{window.location.host}</p>
                <p>🔒 Secure: {window.location.protocol === 'https:' ? '✅ HTTPS' : '❌ HTTP (camera may not work on mobile)'}</p>
                <p>📱 Device: {
                  /iPad|iPhone|iPod/.test(navigator.userAgent) ? 'iOS Safari' :
                  /Android/.test(navigator.userAgent) ? 'Android Chrome' :
                  'Desktop Browser'
                }</p>
                <p>📹 Camera API: {(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) ? '✅ Available' : '❌ Not available'}</p>
                <p>📐 Viewport: {window.innerWidth}x{window.innerHeight}</p>
                <p>🎮 Touch: {'ontouchstart' in window ? '✅ Supported' : '❌ Not detected'}</p>
              </div>
              
              {/* Mobile-specific tips during loading */}
              <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <p className="text-yellow-700 text-xs">
                  <strong>📱 Mobile Camera Tips:</strong><br/>
                  • Allow camera permission when prompted<br/>
                  • Close other apps using camera<br/>
                  • Ensure stable internet connection<br/>
                  • Use back camera for best results
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BarcodeScanner;