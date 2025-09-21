import React, { useState, useEffect, useRef } from 'react';
import { Html5QrcodeScanner, Html5QrcodeScanType, Html5QrcodeSupportedFormats } from 'html5-qrcode';
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
            await new Promise(resolve => setTimeout(resolve, 200));
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

  const startScanning = async () => {
    if (!isMountedRef.current) return;
    
    try {
      resetScanner();
      setIsScanning(true);

      console.log('🚀 Starting mobile-optimized scanner...');
      
      // Enhanced mobile device detection
      const isMobile = /Mobi|Android|iPhone|iPad|iPod/.test(navigator.userAgent);
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
      const isAndroid = /Android/.test(navigator.userAgent);
      const isLowEnd = /Android.*[2-6]\./i.test(navigator.userAgent) || window.screen.width < 400;
      
      // Enhanced error recovery for video abort issues
      let retryAttempts = 0;
      const maxRetries = 3;
      
      console.log('📱 Mobile detection:', { isMobile, isIOS, isAndroid, isLowEnd });

      // Mobile-optimized Html5QrcodeScanner configuration with close-range detection
      const config = {
        // Optimized FPS for better detection at close range
        fps: isLowEnd ? 5 : (isMobile ? 8 : 10),
        
        // Enhanced scan area for close-range barcode detection (2-8 inches)
        qrbox: function(viewfinderWidth, viewfinderHeight) {
          console.log('📐 Viewfinder dimensions:', { viewfinderWidth, viewfinderHeight });
          
          // Larger scan area for close-range detection (2-8 inches optimal)
          const isMobileViewport = viewfinderWidth < 500 || viewfinderHeight < 400;
          const scanAreaPercentage = isMobileViewport ? 0.9 : 0.8; // Increased for better close detection
          
          const minEdgeSize = Math.min(viewfinderWidth, viewfinderHeight);
          const scanSize = Math.floor(minEdgeSize * scanAreaPercentage);
          
          // Optimized for close-range scanning (2-8 inches)
          const width = Math.min(Math.max(scanSize, 250), isMobileViewport ? 350 : 450); // Increased minimum
          const height = Math.min(Math.max(scanSize * 0.7, 175), isMobileViewport ? 245 : 315); // Better ratio for barcodes
          
          console.log('📏 Close-range scan area:', { width, height, scanAreaPercentage, optimal: '2-8 inches' });
          
          return { width, height };
        },
        
        // Mobile-friendly aspect ratio
        aspectRatio: isMobile ? 1.33 : 1.777778, // 4:3 for mobile, 16:9 for desktop
        
        // Disable flip for better performance on mobile
        disableFlip: isMobile,
        
        // Enhanced mobile experimental features
        experimentalFeatures: {
          useBarCodeDetectorIfSupported: true
        },
        
        // Comprehensive barcode format support
        formatsToSupport: [
          Html5QrcodeSupportedFormats.QR_CODE,
          Html5QrcodeSupportedFormats.UPC_A,
          Html5QrcodeSupportedFormats.UPC_E,
          Html5QrcodeSupportedFormats.EAN_8,
          Html5QrcodeSupportedFormats.EAN_13,
          Html5QrcodeSupportedFormats.CODE_128,
          Html5QrcodeSupportedFormats.CODE_39,
          Html5QrcodeSupportedFormats.CODE_93,
          Html5QrcodeSupportedFormats.CODABAR
        ],
        
        supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA],
        
        // Mobile-specific UI controls
        showTorchButtonIfSupported: true,
        showZoomSliderIfSupported: !isLowEnd, // Disable zoom on low-end devices
        defaultZoomValueIfSupported: isMobile ? 1.2 : 2,
        
        // Mobile-optimized video constraints
        videoConstraints: {
          facingMode: { ideal: "environment" }, // Prefer back camera
          
          // Mobile-friendly resolution constraints
          width: isMobile ? 
            { ideal: 1280, max: 1920, min: 320 } : 
            { ideal: 1920, min: 640 },
          height: isMobile ? 
            { ideal: 720, max: 1080, min: 240 } : 
            { ideal: 1080, min: 480 },
          
          // Frame rate optimized for mobile
          frameRate: { 
            ideal: isLowEnd ? 15 : (isMobile ? 20 : 30), 
            max: isMobile ? 30 : 60,
            min: 10 
          },
          
          // Advanced mobile camera settings
          ...(isMobile && {
            aspectRatio: { ideal: 1.33 }, // 4:3 preferred on mobile
            resizeMode: 'crop-and-scale'
          }),
          
          // iOS Safari specific optimizations
          ...(isIOS && {
            focusMode: 'continuous',
            exposureMode: 'continuous',
            whiteBalanceMode: 'continuous'
          })
        }
      };
      
      console.log('🔧 Mobile-optimized scanner config:', config);

      // Ensure cleanup of any existing scanner instance
      if (scannerInstanceRef.current) {
        await cleanup();
        // Add extra delay for mobile cleanup
        if (isMobile) {
          await new Promise(resolve => setTimeout(resolve, 300));
        }
      }

      // Dynamic import with mobile-specific error handling
      let Html5QrcodeScanner;
      try {
        const module = await import('html5-qrcode');
        Html5QrcodeScanner = module.Html5QrcodeScanner;
        console.log('✅ Html5QrcodeScanner imported for mobile');
      } catch (importError) {
        console.error('❌ Failed to import html5-qrcode library:', importError);
        throw new Error('Failed to load barcode scanning library. Please refresh the page.');
      }
      
      // Enhanced browser compatibility check
      console.log('🔍 Mobile browser compatibility:', {
        userAgent: navigator.userAgent,
        hasGetUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
        hasBarcodeDetector: 'BarcodeDetector' in window,
        protocol: window.location.protocol,
        isSecure: window.location.protocol === 'https:',
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
        devicePixelRatio: window.devicePixelRatio
      });

      // Create scanner instance with enhanced error handling
      try {
        scannerInstanceRef.current = new Html5QrcodeScanner(
          "qr-reader",
          config,
          true // verbose logging for mobile debugging
        );
        console.log('✅ Mobile Html5QrcodeScanner instance created');
      } catch (instanceError) {
        console.error('❌ Failed to create scanner instance:', instanceError);
        throw new Error('Failed to initialize barcode scanner. Please try refreshing the page.');
      }

      // Enhanced DOM element verification with mobile-specific checks
      const qrReaderElement = document.getElementById("qr-reader");
      if (!qrReaderElement) {
        throw new Error('Scanner container not found in DOM');
      }
      
      // Mobile-specific DOM validation
      const elementRect = qrReaderElement.getBoundingClientRect();
      console.log('📐 Scanner DOM element info:', {
        element: qrReaderElement,
        rect: elementRect,
        visible: elementRect.width > 0 && elementRect.height > 0,
        inViewport: elementRect.top >= 0 && elementRect.left >= 0
      });
      
      if (elementRect.width === 0 || elementRect.height === 0) {
        console.warn('⚠️ Scanner container has zero dimensions, may cause mobile rendering issues');
      }

      // Mobile-optimized initialization delay
      const initDelay = isIOS ? 250 : (isAndroid ? 200 : 100);
      console.log(`⏱️ Using ${initDelay}ms initialization delay for mobile compatibility`);

      setTimeout(() => {
        if (scannerInstanceRef.current && isMountedRef.current) {
          try {
            scannerInstanceRef.current.render(
              (decodedText) => {
                console.log('🎯 MOBILE SUCCESS: Barcode detected!', decodedText);
                console.log('📊 Mobile scan details:', {
                  barcode: decodedText,
                  timestamp: new Date().toISOString(),
                  length: decodedText.length,
                  device: { isMobile, isIOS, isAndroid }
                });
                
                if (isMountedRef.current) {
                  handleSuccessfulScan(decodedText);
                }
              },
              (errorMessage) => {
                // Enhanced mobile error handling with video abort recovery
                const ignoredMobileMessages = [
                  'No MultiFormat Readers',
                  'NotFoundException', 
                  'No QR code found',
                  'QR code parse error', 
                  'Unable to detect a valid barcode',
                  'No barcode or QR code detected',
                  'No code found',
                  'No camera stream',
                  'Camera not ready'
                ];
                
                const criticalVideoErrors = [
                  'video surface onabort',
                  'RenderedCameraImpl',
                  'Video stream error',
                  'Camera stream interrupted',
                  'MediaStream error',
                  'Video element error'
                ];
                
                const isIgnoredMessage = ignoredMobileMessages.some(msg => 
                  errorMessage.includes(msg)
                );
                
                const isVideoAbortError = criticalVideoErrors.some(err => 
                  errorMessage.includes(err)
                );
                
                if (isVideoAbortError && retryAttempts < maxRetries) {
                  retryAttempts++;
                  console.warn(`🔄 AGGRESSIVE VIDEO ABORT RECOVERY ${retryAttempts}/${maxRetries}:`, errorMessage);
                  
                  // Immediate aggressive recovery without delay
                  (async () => {
                    try {
                      console.log('🚨 Starting aggressive camera recovery...');
                      
                      // 1. Immediate stop of all scanner instances
                      if (scannerInstanceRef.current) {
                        try {
                          await scannerInstanceRef.current.clear();
                        } catch (clearError) {
                          console.warn('Clear error (continuing):', clearError);
                        }
                        scannerInstanceRef.current = null;
                      }
                      
                      // 2. Force stop ALL video tracks on page
                      navigator.mediaDevices.getUserMedia({ video: false }).catch(() => {});
                      
                      // 3. Aggressive video element cleanup
                      const allVideos = document.querySelectorAll('video');
                      allVideos.forEach(video => {
                        try {
                          if (video.srcObject) {
                            video.srcObject.getTracks().forEach(track => {
                              console.log('🛑 Force stopping track:', track.kind, track.readyState);
                              track.stop();
                            });
                            video.srcObject = null;
                          }
                          video.pause();
                          video.load(); // Reset video element
                          if (video.parentNode) {
                            video.remove();
                          }
                        } catch (videoError) {
                          console.warn('Video cleanup error (continuing):', videoError);
                        }
                      });
                      
                      // 4. Clear ALL scanner containers
                      const containers = document.querySelectorAll('#qr-reader, [id*="qr-"], [class*="qr-"]');
                      containers.forEach(container => {
                        container.innerHTML = '';
                      });
                      
                      // 5. Force garbage collection hint
                      if (window.gc) {
                        window.gc();
                      }
                      
                      // 6. Very short delay then immediate restart
                      await new Promise(resolve => setTimeout(resolve, 500));
                      
                      console.log('🔄 Restarting with basic camera constraints...');
                      
                      // 7. Restart with most basic configuration
                      if (isMountedRef.current) {
                        setError('🔄 Camera recovering... Please wait');
                        await new Promise(resolve => setTimeout(resolve, 500));
                        
                        // Reset retry counter for this attempt
                        const originalRetryCount = retryAttempts;
                        
                        // Start fresh scanner instance
                        startScanning();
                        
                        // Clear recovery message after delay
                        setTimeout(() => {
                          if (isMountedRef.current) {
                            setError('');
                          }
                        }, 3000);
                      }
                      
                    } catch (recoveryError) {
                      console.error('❌ Aggressive recovery failed:', recoveryError);
                      if (retryAttempts >= maxRetries) {
                        setError('❌ Camera system error: Recovery failed. Please close and reopen the scanner.');
                        setIsScanning(false);
                      } else {
                        // Try one more time with even more basic approach
                        setTimeout(() => {
                          if (isMountedRef.current) {
                            setError('🔄 Final recovery attempt...');
                            startScanning();
                          }
                        }, 1000);
                      }
                    }
                  })();
                  
                  return; // Exit error handler immediately
                }
                
                if (!isIgnoredMessage && !isVideoAbortError) {
                  console.warn('⚠️ Mobile scanner error (not ignored):', errorMessage);
                  
                  // Handle mobile-specific critical errors
                  if (errorMessage.includes('Camera access') || 
                      errorMessage.includes('Permission') ||
                      errorMessage.includes('NotAllowed')) {
                    setError('❌ Camera access required. Please allow camera permissions.');
                    setCameraPermission(false);
                  } else if (retryAttempts >= maxRetries) {
                    setError('❌ Camera initialization failed after multiple attempts. Please refresh the page.');
                    setIsScanning(false);
                  }
                } else if (!isVideoAbortError) {
                  // Reduced frequency logging for mobile to save performance
                  if (Math.random() < 0.002) {
                    console.log('🔍 Mobile scanning active...', new Date().toLocaleTimeString());
                  }
                }
              }
            );
            
            console.log('✅ Mobile scanner render initiated successfully');
          } catch (renderError) {
            console.error('❌ Mobile scanner render failed:', renderError);
            setError('❌ Failed to start camera. Please try closing other apps using the camera and refresh the page.');
            setIsScanning(false);
          }
        }
      }, initDelay);

    } catch (error) {
      console.error('❌ Mobile scanner startup error:', error);
      console.error('🔍 Mobile error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack?.substring(0, 300) // Truncate for mobile logging
      });
      
      setIsScanning(false);
      
      // Mobile-specific error handling
      if (error.message.includes('Cannot access camera') || 
          error.message.includes('camera')) {
        setError('❌ Cannot access camera. Please allow camera permission in your browser settings and try again.');
        setCameraPermission(false);
      } else if (error.message.includes('Permission denied') || 
                 error.message.includes('NotAllowed')) {
        setError('❌ Camera permission denied. Please check your browser settings and allow camera access.');
        setCameraPermission(false);
      } else if (error.message.includes('library') || 
                 error.message.includes('import')) {
        setError('❌ Scanner library failed to load. Please check your internet connection and refresh the page.');
      } else {
        handleScanError(error);
      }
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
    console.log('🧹 Starting mobile-aware cleanup...');
    await stopScanning();
    
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
                      onClick={startScanning}
                      className="flex items-center justify-center space-x-2 bg-gradient-to-r from-green-500 to-green-600 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg hover:from-green-600 hover:to-green-700 transition-all text-sm md:text-base shadow-lg active:scale-95 transform"
                    >
                      <Camera size={16} className="md:hidden" />
                      <Camera size={20} className="hidden md:block" />
                      <span>📱 Start Mobile Scan</span>
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
                    
                    {/* Enhanced Scanning Overlay */}
                    <div className="absolute inset-0 pointer-events-none">
                      <div className="relative w-full h-full">
                        {/* Format indicators */}
                        <div className="absolute top-2 left-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs">
                          📱 All Formats: EAN, UPC, Code128, QR
                        </div>
                        
                        {/* Enhanced Instructions */}
                        <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-80 text-white px-3 md:px-4 py-2 rounded-lg text-center max-w-xs">
                          <p className="text-xs md:text-sm font-medium text-green-400">🎯 Barcode Detection Active</p>
                          <p className="text-xs text-gray-300 mt-1">Hold phone 6-12 inches from barcode</p>
                          <p className="text-xs text-gray-300">Keep barcode horizontal & well-lit</p>
                        </div>
                        
                        {/* Scan area guide */}
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="border-2 border-green-400 border-dashed rounded-lg bg-transparent" 
                               style={{
                                 width: '280px',
                                 height: '120px',
                                 opacity: 0.6
                               }}>
                            <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-green-400 text-xs font-medium">
                              📊 Barcode Scan Area
                            </div>
                          </div>
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

              {/* Enhanced Mobile Instructions */}
              <div className="text-center text-xs md:text-sm text-gray-600 space-y-2 bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border">
                <p>📱 <strong>Mobile Barcode Scanner Tips:</strong></p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-left">
                  <p>📱 Tap "Start Mobile Scan" for camera</p>
                  <p>💡 Ensure good lighting</p>
                  <p>🎯 Hold steady, 6-12 inches away</p>
                  <p>🔄 Auto-retry on scan failures</p>
                  <p>📊 Supports: EAN, UPC, Code128, QR</p>
                  <p>⚡ Optimized for mobile devices</p>
                  <p>🍎 iOS Safari compatible</p>
                  <p>🤖 Android Chrome optimized</p>
                </div>
                {/Mobi|Android|iPhone|iPad|iPod/.test(navigator.userAgent) && (
                  <div className="mt-3 p-2 bg-green-50 rounded border-green-200 border">
                    <p className="text-green-700 font-medium">📱 Mobile Device Detected</p>
                    <p className="text-green-600 text-xs">Optimized camera settings activated for your device</p>
                  </div>
                )}
                {retryCount > 0 && (
                  <p className="text-orange-600 font-medium">• Having trouble? Try the "Manual Entry" option or restart your browser</p>
                )}
              </div>
            </div>
          )}

          {/* Loading Camera - Mobile Optimized */}
          {cameraPermission === null && (
            <div className="text-center py-6 md:py-8">
              <div className="animate-spin rounded-full h-8 w-8 md:h-12 md:w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
              <p className="text-sm md:text-base text-gray-600">📱 Initializing mobile scanner...</p>
              
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