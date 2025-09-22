import React, { useState, useRef, useEffect } from 'react';
import { Camera, AlertCircle } from 'lucide-react';

const MobileCameraTest = () => {
  const [stream, setStream] = useState(null);
  const [error, setError] = useState('');
  const [cameraInfo, setCameraInfo] = useState('');
  const videoRef = useRef(null);

  const startMobileCamera = async () => {
    try {
      setError('');
      setCameraInfo('🔄 Starting mobile camera...');
      
      // Mobile-optimized constraints
      const constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: 640, max: 1280 },
          height: { ideal: 480, max: 720 }
        }
      };

      console.log('📱 Requesting camera access...');
      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      
      console.log('✅ Camera stream obtained');
      setStream(mediaStream);
      
      if (videoRef.current) {
        const video = videoRef.current;
        
        // Essential mobile video setup
        video.srcObject = mediaStream;
        video.autoplay = true;
        video.playsInline = true;
        video.muted = true;
        
        video.onloadedmetadata = async () => {
          console.log('📱 Video metadata loaded');
          setCameraInfo(`📱 Camera active: ${video.videoWidth}x${video.videoHeight}`);
          
          try {
            await video.play();
            console.log('✅ Video playing');
            setCameraInfo(`✅ Camera working: ${video.videoWidth}x${video.videoHeight}`);
          } catch (playError) {
            console.error('❌ Play error:', playError);
            setError('❌ Camera display failed: ' + playError.message);
          }
        };
        
        video.onerror = (err) => {
          console.error('❌ Video error:', err);
          setError('❌ Video error: ' + (err.message || 'Unknown error'));
        };
      }
      
    } catch (err) {
      console.error('❌ Camera error:', err);
      setError('❌ Camera failed: ' + err.message);
      
      // Show detailed error info for debugging
      setCameraInfo(`
        Error: ${err.name} - ${err.message}
        UserAgent: ${navigator.userAgent}
        Protocol: ${window.location.protocol}
        Camera API: ${navigator.mediaDevices ? 'Available' : 'Not available'}
      `);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraInfo('');
    setError('');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md max-h-screen overflow-y-auto">
        <div className="p-4">
          <h2 className="text-lg font-bold mb-4">📱 Mobile Camera Test</h2>
          
          {/* Video Display */}
          <div className="relative bg-black rounded-lg overflow-hidden mb-4">
            <video
              ref={videoRef}
              className="w-full h-64 object-cover"
              style={{
                backgroundColor: '#000',
                objectFit: 'cover'
              }}
            />
            
            {!stream && (
              <div className="absolute inset-0 flex items-center justify-center text-white">
                <div className="text-center">
                  <Camera size={48} className="mx-auto mb-2 text-gray-400" />
                  <p>Camera not active</p>
                </div>
              </div>
            )}
          </div>
          
          {/* Controls */}
          <div className="space-y-3">
            {!stream ? (
              <button
                onClick={startMobileCamera}
                className="w-full bg-green-500 text-white py-3 rounded-lg hover:bg-green-600"
              >
                📱 Start Mobile Camera
              </button>
            ) : (
              <button
                onClick={stopCamera}
                className="w-full bg-red-500 text-white py-3 rounded-lg hover:bg-red-600"
              >
                ❌ Stop Camera
              </button>
            )}
            
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-gray-500 text-white py-2 rounded-lg hover:bg-gray-600"
            >
              🔄 Reload Page
            </button>
          </div>
          
          {/* Status Messages */}
          {cameraInfo && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-800 text-sm whitespace-pre-line">{cameraInfo}</p>
            </div>
          )}
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <AlertCircle size={16} className="text-red-500 mt-0.5" />
                <p className="text-red-700 text-sm whitespace-pre-line">{error}</p>
              </div>
            </div>
          )}
          
          {/* Debug Info */}
          <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
            <h3 className="font-medium text-gray-800 mb-2">🔍 Debug Info:</h3>
            <div className="text-xs text-gray-600 space-y-1">
              <p><strong>User Agent:</strong> {navigator.userAgent}</p>
              <p><strong>Protocol:</strong> {window.location.protocol}</p>
              <p><strong>Host:</strong> {window.location.host}</p>
              <p><strong>Camera API:</strong> {navigator.mediaDevices ? '✅ Available' : '❌ Not available'}</p>
              <p><strong>Screen:</strong> {window.screen.width}x{window.screen.height}</p>
              <p><strong>Viewport:</strong> {window.innerWidth}x{window.innerHeight}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileCameraTest;