import React, { useState, useEffect, useRef, useContext, createContext } from "react";
import "./App.css";
import axios from "axios";
import { Html5QrcodeScanner } from "html5-qrcode";
import { BrowserMultiFormatReader, DecodeHintType } from '@zxing/library';
import { BrowserCodeReader } from '@zxing/browser';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

// Error Boundary Component for robust error handling
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-red-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full">
            <div className="flex items-center mb-4">
              <svg className="w-8 h-8 text-red-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <h2 className="text-xl font-bold text-gray-900">Something went wrong</h2>
            </div>
            <p className="text-gray-600 mb-4">
              The application encountered an unexpected error. Please refresh the page or contact support.
            </p>
            <button 
              onClick={() => window.location.reload()}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ChartJS.register(ArcElement, Tooltip, Legend);

// Authentication Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  const login = async (username, password) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        
        // Get user info
        const userResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${data.access_token}`,
          },
        });
        
        if (userResponse.ok) {
          const userData = await userResponse.json();
          setUser(userData);
        }
        
        return { success: true };
      } else {
        const error = await response.json();
        // Handle different error types
        if (response.status === 403) {
          return { success: false, error: error.detail, statusCode: 403 };
        }
        return { success: false, error: error.detail || 'Login failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (response.ok) {
        const data = await response.json();
        return { success: true, user: data };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Registration failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const getCurrentUser = async () => {
    if (!token) return null;

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        return userData;
      } else {
        // Token is invalid, logout
        logout();
        return null;
      }
    } catch (error) {
      console.error('Error getting current user:', error);
      logout();
      return null;
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        await getCurrentUser();
      }
      setLoading(false);
    };

    initAuth();
  }, [token]);

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const LoginForm = ({ onToggleForm }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(formData.username, formData.password);
    
    if (!result.success) {
      if (result.statusCode === 403) {
        setError("Account Pending Approval: Your account is waiting for administrator approval. Please contact your system administrator.");
      } else {
        setError(result.error);
      }
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8 relative">
      {/* Background logo - subtle watermark */}
      <div className="absolute inset-0 flex items-center justify-center opacity-5">
        <img 
          src="/icons/geant_official_logo.png" 
          alt="" 
          className="w-96 h-96 object-contain"
        />
      </div>
      
      <div className="max-w-md w-full space-y-8 relative z-10">
        <div className="text-center">
          {/* Main logo header */}
          <div className="flex justify-center mb-6">
            <img 
              src="/icons/geant_official_logo.png" 
              alt="Geant Hypermarket" 
              className="w-20 h-20 object-contain"
            />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Inventory Tracker
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            <span className="font-semibold text-blue-600">Geant Hypermarket</span> Official System
          </p>
          <p className="text-center text-xs text-gray-500">
            Welcome back! Please sign in to continue.
          </p>
        </div>
        <form className="mt-8 space-y-6 bg-white p-8 rounded-lg shadow-lg" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded flex items-center">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          )}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              required
              value={formData.username}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition duration-200"
              placeholder="Enter your username"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={formData.password}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 transition duration-200"
              placeholder="Enter your password"
            />
          </div>
          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition duration-200"
            >
              {loading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Signing in...
                </div>
              ) : (
                'Sign in'
              )}
            </button>
          </div>
          <div className="text-center">
            <button
              type="button"
              onClick={onToggleForm}
              className="text-blue-600 hover:text-blue-500 text-sm font-medium transition duration-200"
            >
              Don't have an account? Sign up
            </button>
          </div>
        </form>
        
        {/* Footer branding */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Powered by <span className="font-semibold">Geant Hypermarket</span>
          </p>
        </div>
      </div>
    </div>
  );
};

// Register Component
const RegisterForm = ({ onToggleForm }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    email: '',
    full_name: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    // Validate password length
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      setLoading(false);
      return;
    }

    const { confirmPassword, ...registrationData } = formData;
    const result = await register(registrationData);
    
    if (result.success) {
      setSuccess('Registration successful! Your account is pending approval. An administrator will review your request and approve access. Please contact your administrator if needed.');
      setFormData({
        username: '',
        password: '',
        confirmPassword: '',
        email: '',
        full_name: ''
      });
      setTimeout(() => onToggleForm(), 4000); // Longer timeout for longer message
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-100 py-12 px-4 sm:px-6 lg:px-8 relative">
      {/* Background logo - subtle watermark */}
      <div className="absolute inset-0 flex items-center justify-center opacity-5">
        <img 
          src="/icons/geant_official_logo.png" 
          alt="" 
          className="w-96 h-96 object-contain"
        />
      </div>
      
      <div className="max-w-md w-full space-y-8 relative z-10">
        <div className="text-center">
          {/* Main logo header */}
          <div className="flex justify-center mb-6">
            <img 
              src="/icons/geant_official_logo.png" 
              alt="Geant Hypermarket" 
              className="w-20 h-20 object-contain"
            />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            <span className="font-semibold text-green-600">Join Geant Hypermarket</span> Inventory System
          </p>
          <p className="text-center text-xs text-gray-500">
            Get started with our professional inventory tracker.
          </p>
        </div>
        <form className="mt-8 space-y-6 bg-white p-8 rounded-lg shadow-lg" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
              {success}
            </div>
          )}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Username *
            </label>
            <input
              id="username"
              name="username"
              type="text"
              required
              value={formData.username}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Choose a username"
            />
          </div>
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
              Full Name
            </label>
            <input
              id="full_name"
              name="full_name"
              type="text"
              value={formData.full_name}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your full name"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your email (optional)"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password *
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={formData.password}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Choose a password (min 6 characters)"
            />
          </div>
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
              Confirm Password *
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              required
              value={formData.confirmPassword}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Confirm your password"
            />
          </div>
          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 transition duration-200"
            >
              {loading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating account...
                </div>
              ) : (
                'Create account'
              )}
            </button>
          </div>
          <div className="text-center">
            <button
              type="button"
              onClick={onToggleForm}
              className="text-blue-600 hover:text-blue-500 text-sm font-medium transition duration-200"
            >
              Already have an account? Sign in
            </button>
          </div>
        </form>
        
        {/* Footer branding */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Powered by <span className="font-semibold">Geant Hypermarket</span>
          </p>
        </div>
      </div>
    </div>
  );
};

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Helper function to get authentication headers
const getAuthHeaders = (token) => ({
  Authorization: `Bearer ${token}`,
  'Content-Type': 'application/json',
});

function App() {
  const { token, logout, user } = useAuth(); // Add useAuth hook
  const [activeTab, setActiveTab] = useState('dashboard');
  const [products, setProducts] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [kpi, setKpi] = useState({});
  const [enhancedKpi, setEnhancedKpi] = useState({});  // NEW: Enhanced KPI data
  const [topSuppliers, setTopSuppliers] = useState([]);
  const [donutChartData, setDonutChartData] = useState(null);
  const [categories, setCategories] = useState({});
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View mode for items
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'cards'
  
  // Return form state
  const [returnItems, setReturnItems] = useState([]);
  const [returnForm, setReturnForm] = useState({
    supplierCode: '',
    supplierName: '',
    itemNumber: '',
    barcode: '',
    itemName: '',
    quantity: '',
    unitPrice: '',
    currency: 'YER',
    reasonForReturn: 'Expired',  // NEW: Reason for return
    returnValue: 0,
    expiryDate: '',  // NEW: Expiry date
    attachedImage: null  // NEW: Image attachment
  });
  const [editingReturnIndex, setEditingReturnIndex] = useState(-1);
  
  // Item search for return form
  const [itemSearchQuery, setItemSearchQuery] = useState('');
  const [itemSearchResults, setItemSearchResults] = useState([]);
  const [showItemSearchResults, setShowItemSearchResults] = useState(false);
  
  // Admin state
  const [pendingUsers, setPendingUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  
  // Dashboard state
  const [showAlerts, setShowAlerts] = useState(false);
  const [selectedSearchItem, setSelectedSearchItem] = useState(null);
  
  // Form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [formData, setFormData] = useState({
    product_name: '',
    item_number: '',  // NEW
    department: '',
    section: '',
    family: '',
    sub_family: '',
    supplier_code: '',  // NEW
    supplier: '',
    expiry_date: '',
    quantity: '',
    barcode: '',
    selling_price: '',
    purchase_price: '',
    purchase_currency: 'YER',  // NEW: Purchase currency field
    arabic_description: '',  // NEW
    description: '',
    location: '',
    brand: ''
  });
  
  // Filters
  const [filters, setFilters] = useState({
    supplier: '',
    department: '',
    section: '',
    family: '',
    search: ''
  });

  // Search state
  const [globalSearch, setGlobalSearch] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchScanning, setSearchScanning] = useState(false);

  // Import options
  const [importMode, setImportMode] = useState('add_only');
  const [showAdvancedImport, setShowAdvancedImport] = useState(false);
  
  // NEW: Out of Stock state
  const [outOfStockProducts, setOutOfStockProducts] = useState([]);
  const [outOfStockFilters, setOutOfStockFilters] = useState({ section: '', supplier: '' });
  
  // NEW: Enhanced Supplier Dashboard state
  const [supplierDashboardData, setSupplierDashboardData] = useState(null);
  const [supplierDashboardSection, setSupplierDashboardSection] = useState('');

  // Barcode scanner state
  const [scannerActive, setScannerActive] = useState(false);
  const [scannedProduct, setScannedProduct] = useState(null);
  const [manualBarcode, setManualBarcode] = useState('');
  
  // Enhanced ZXing scanner refs
  const [zxingCodeReader, setZxingCodeReader] = useState(null);
  const [isZxingScanning, setIsZxingScanning] = useState(false);
  const videoRef = useRef(null);
  const scannerRef = useRef(null);
  const searchScannerRef = useRef(null);
  const html5QrcodeScanner = useRef(null);
  const searchBarcodeScanner = useRef(null);

  // New states for improved search and product details
  const [isSearching, setIsSearching] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showProductDetails, setShowProductDetails] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  
  // PWA install state
  const [installPrompt, setInstallPrompt] = useState(null);
  const [isInstallable, setIsInstallable] = useState(false);
  
  // Supplier Details Modal state
  const [selectedSupplierData, setSelectedSupplierData] = useState(null);
  const [showSupplierDetails, setShowSupplierDetails] = useState(false);
  const [supplierDetailsLoading, setSupplierDetailsLoading] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(40);

  // Enhanced currency formatter supporting multiple currencies
  const formatCurrency = (amount, currency = 'YER') => {
    if (!amount && amount !== 0) return `0.00 ${currency}`;
    const formattedAmount = parseFloat(amount).toFixed(2);
    return `${formattedAmount} ${currency}`;
  };

  // Calculate stock value (Quantity × Purchase Price)
  const calculateStockValue = (quantity, purchasePrice, currency = 'YER') => {
    if (!quantity || !purchasePrice) return `0.00 ${currency}`;
    const stockValue = parseFloat(quantity) * parseFloat(purchasePrice);
    return formatCurrency(stockValue, currency);
  };

  // Get currency from product data
  const getProductCurrency = (product) => {
    return product.purchase_currency || product.currency || 'YER';
  };

  // Search functionality with debouncing and direct product opening
  const performSearch = async (searchTerm) => {
    if (!searchTerm.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      // First try exact barcode match
      const barcodeResponse = await fetch(`${BACKEND_URL}/api/products/barcode/${encodeURIComponent(searchTerm.trim())}`, {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });

      if (barcodeResponse.ok) {
        const product = await barcodeResponse.json();
        // Direct product match found - open details immediately
        setSelectedProduct(product);
        setShowProductDetails(true);
        setGlobalSearch('');
        setSearchResults([]);
        setIsSearching(false);
        return;
      }

      // If no direct barcode match, search for products
      const response = await fetch(`${BACKEND_URL}/api/search?q=${encodeURIComponent(searchTerm.trim())}&limit=50`, {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });

      if (response.ok) {
        const results = await response.json();
        
        // If only one result, open it directly
        if (results.length === 1) {
          setSelectedProduct(results[0]);
          setShowProductDetails(true);
          setGlobalSearch('');
          setSearchResults([]);
        } else {
          setSearchResults(results);
        }
      } else {
        console.error('Search failed:', response.statusText);
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Debounced search effect
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (globalSearch) {
        performSearch(globalSearch);
      } else {
        setSearchResults([]);
      }
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [globalSearch]);

  // Handle barcode scan result
  const handleBarcodeResult = async (barcode) => {
    setIsScanning(false);
    setGlobalSearch(barcode);
    
    // Search for product with this barcode
    try {
      const response = await fetch(`${BACKEND_URL}/api/products/barcode/${barcode}`, {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });

      if (response.ok) {
        const product = await response.json();
        setSelectedProduct(product);
        setShowProductDetails(true);
      } else {
        // If barcode not found, perform regular search
        performSearch(barcode);
      }
    } catch (error) {
      console.error('Barcode lookup error:', error);
      performSearch(barcode);
    }
  };

  // Open product details
  const openProductDetails = (product) => {
    setSelectedProduct(product);
    setShowProductDetails(true);
  };

  // Close product details
  const closeProductDetails = () => {
    setSelectedProduct(null);
    setShowProductDetails(false);
  };

  // PWA install function
  const handleInstallApp = async () => {
    if (installPrompt) {
      installPrompt.prompt();
      const result = await installPrompt.userChoice;
      if (result.outcome === 'accepted') {
        setSuccess('📱 App installation started! Check your home screen.');
        setInstallPrompt(null);
        setIsInstallable(false);
      }
    }
  };

  // Supplier Details Functions
  const openSupplierDetails = async (supplierName) => {
    setSupplierDetailsLoading(true);
    setShowSupplierDetails(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/suppliers/details/${encodeURIComponent(supplierName)}`, {
        headers: token ? {
          'Authorization': `Bearer ${token}`
        } : {}
      });

      if (response.ok) {
        const supplierData = await response.json();
        setSelectedSupplierData(supplierData);
      } else {
        console.error('Failed to fetch supplier details');
        setError('Failed to load supplier details');
      }
    } catch (error) {
      console.error('Error fetching supplier details:', error);
      setError('Error loading supplier details');
    } finally {
      setSupplierDetailsLoading(false);
    }
  };

  const closeSupplierDetails = () => {
    setSelectedSupplierData(null);
    setShowSupplierDetails(false);
  };

  // Export Supplier PDF
  const exportSupplierPDF = async (supplierName) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/suppliers/export/pdf/${encodeURIComponent(supplierName)}`, {
        method: 'POST',
        headers: token ? {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        } : { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `supplier_${supplierName.replace(/[^a-z0-9]/gi, '_')}_report.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        setSuccess('📄 Supplier PDF report downloaded successfully!');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        throw new Error('Export failed');
      }
    } catch (error) {
      console.error('Error exporting supplier PDF:', error);
      setError('Failed to export supplier PDF');
      setTimeout(() => setError(''), 3000);
    }
  };

  // Export Supplier Excel
  const exportSupplierExcel = async (supplierName) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/suppliers/export/excel/${encodeURIComponent(supplierName)}`, {
        method: 'POST',
        headers: token ? {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        } : { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `supplier_${supplierName.replace(/[^a-z0-9]/gi, '_')}_data.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        setSuccess('📊 Supplier Excel report downloaded successfully!');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        throw new Error('Export failed');
      }
    } catch (error) {
      console.error('Error exporting supplier Excel:', error);
      setError('Failed to export supplier Excel');
      setTimeout(() => setError(''), 3000);
    }
  };

  useEffect(() => {
    if (user) {
      fetchKPI();
      fetchDonutChartData();
      fetchProducts();
      fetchAlerts();
      refreshAllFilters(); // Use the new real-time filter refresh
      generateAlerts();
    }
  }, []);
  // PWA functionality - Handle app shortcuts and launch parameters
  useEffect(() => {
    // Handle URL parameters for PWA shortcuts
    const urlParams = new URLSearchParams(window.location.search);
    const action = urlParams.get('action');
    const tab = urlParams.get('tab');
    
    if (user) {
      if (action === 'scan') {
        setActiveTab('scanner');
      } else if (action === 'add') {
        setActiveTab('products');
        setShowAddForm(true);
      } else if (tab === 'dashboard') {
        setActiveTab('dashboard');
      }
    }
    
    // Install prompt handling
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setInstallPrompt(e);
      setIsInstallable(true);
    };
    
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    
    // Handle app install success
    window.addEventListener('appinstalled', () => {
      console.log('Geant Inventory App installed successfully!');
      setSuccess('📱 App installed successfully! You can now use it from your home screen.');
      setTimeout(() => setSuccess(''), 5000);
    });
    
    // Register for push notifications if supported
    if ('Notification' in window && 'serviceWorker' in navigator) {
      if (Notification.permission === 'default') {
        // We'll ask for permission when user performs their first important action
      }
    }
    
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, [user]);

  useEffect(() => {
    fetchProducts();
    setCurrentPage(1); // Reset to first page when filters change
  }, [filters]);

  // Fetch out-of-stock products when the tab is activated or filters change
  useEffect(() => {
    if (user && activeTab === 'out-of-stock') {
      fetchOutOfStockProducts();
    }
  }, [user, activeTab, outOfStockFilters]);

  // Fetch supplier dashboard when the tab is activated or section filter changes
  useEffect(() => {
    if (user && activeTab === 'suppliers') {
      fetchSupplierDashboard();
    }
  }, [user, activeTab, supplierDashboardSection]);

  useEffect(() => {
    // Cleanup scanner on unmount
    return () => {
      // Clean up HTML5 scanner
      if (html5QrcodeScanner.current) {
        try {
          const scannerElement = document.getElementById('barcode-reader');
          if (scannerElement) {
            html5QrcodeScanner.current.clear().catch(() => {
              // Ignore cleanup errors on unmount
            });
          }
        } catch (error) {
          // Ignore cleanup errors on unmount
        }
        html5QrcodeScanner.current = null;
      }
      
      // Clean up search scanner
      if (searchBarcodeScanner.current) {
        try {
          searchBarcodeScanner.current.clear().catch(() => {
            // Ignore cleanup errors on unmount
          });
        } catch (error) {
          // Ignore cleanup errors on unmount
        }
        searchBarcodeScanner.current = null;
      }
      
      // Clean up ZXing scanner
      if (zxingCodeReader) {
        try {
          zxingCodeReader.reset();
        } catch (error) {
          // Ignore cleanup errors on unmount
        }
      }
      
      // Clean up any video streams
      try {
        const video = document.getElementById('video-scanner');
        if (video && video.srcObject) {
          const stream = video.srcObject;
          if (stream && typeof stream.getTracks === 'function') {
            stream.getTracks().forEach(track => {
              try {
                track.stop();
              } catch (error) {
                // Ignore track cleanup errors
              }
            });
          }
        }
      } catch (error) {
        // Ignore video cleanup errors on unmount
      }
    };
  }, [zxingCodeReader]); // Add zxingCodeReader dependency

  // Item search for return form
  const searchItemsForReturn = async (query) => {
    if (!query.trim()) {
      setItemSearchResults([]);
      setShowItemSearchResults(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/search?q=${encodeURIComponent(query)}&limit=10`, {
        headers: getAuthHeaders(token)
      });
      setItemSearchResults(response.data);
      setShowItemSearchResults(true);
    } catch (error) {
      console.error('Error searching items:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  // Handle item selection from search results
  const handleItemSelect = (item) => {
    const updatedForm = {
      ...returnForm,
      supplierCode: item.supplier_code || '',  // NEW: Auto-populate supplier code
      supplierName: item.supplier,
      itemNumber: item.item_number || '',      // NEW: Auto-populate item number
      barcode: item.barcode || '',             // NEW: Auto-populate barcode
      itemName: item.product_name,
      unitPrice: item.purchase_price || item.selling_price || '',  // Use purchase price first, then selling price
      currency: item.purchase_currency || 'YER'  // NEW: Auto-populate currency from item's purchase currency
    };
    
    // Calculate return value if quantity is already entered
    if (updatedForm.quantity && updatedForm.unitPrice) {
      updatedForm.returnValue = parseFloat(updatedForm.quantity) * parseFloat(updatedForm.unitPrice);
    }
    
    setReturnForm(updatedForm);
    setItemSearchQuery(item.product_name);
    setShowItemSearchResults(false);
  };

  // Debounced item search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchItemsForReturn(itemSearchQuery);
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [itemSearchQuery]);

  // Enhanced global search functionality
  const handleGlobalSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      setShowSearchResults(false);
      setSelectedSearchItem(null);
      return;
    }

    try {
      const response = await axios.get(`${API}/search/details?q=${encodeURIComponent(query)}`, {
        headers: getAuthHeaders(token)
      });
      setSearchResults(response.data.results);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  // Handle search item selection
  const handleSearchItemSelect = (item) => {
    setSelectedSearchItem(item);
    setShowSearchResults(false);
    setGlobalSearch('');
  };

  // Navigate to items with filter
  const navigateToItemsWithFilter = async (filterType) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/products/by-status?status=${filterType}`, {
        headers: getAuthHeaders(token)
      });
      setProducts(response.data);
      setActiveTab('products');
    } catch (error) {
      console.error('Filter failed:', error);
      setError('Filter failed. Please try again.');
      if (error.response?.status === 401) {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  // Return Form Functions
  const handleReturnFormChange = (e) => {
    const { name, value } = e.target;
    const updatedForm = { ...returnForm, [name]: value };
    
    // Auto-calculate return value when quantity or unit price changes
    if (name === 'quantity' || name === 'unitPrice') {
      const qty = name === 'quantity' ? parseFloat(value) || 0 : parseFloat(returnForm.quantity) || 0;
      const price = name === 'unitPrice' ? parseFloat(value) || 0 : parseFloat(returnForm.unitPrice) || 0;
      updatedForm.returnValue = qty * price;
    }
    
    setReturnForm(updatedForm);
  };

  const addReturnItem = () => {
    if (!returnForm.supplierCode || !returnForm.supplierName || !returnForm.itemName || !returnForm.quantity || !returnForm.unitPrice) {
      setError('Please fill all required fields');
      setTimeout(() => setError(''), 3000);
      return;
    }

    const newItem = {
      ...returnForm,
      supplierCode: returnForm.supplierCode,
      supplierName: returnForm.supplierName,
      itemNumber: returnForm.itemNumber,
      barcode: returnForm.barcode,
      itemName: returnForm.itemName,
      id: Date.now(), // Simple ID for tracking
      quantity: parseFloat(returnForm.quantity),
      unitPrice: parseFloat(returnForm.unitPrice),
      currency: returnForm.currency,
      returnValue: parseFloat(returnForm.quantity) * parseFloat(returnForm.unitPrice),
      returnValueFormatted: `${(parseFloat(returnForm.quantity) * parseFloat(returnForm.unitPrice)).toFixed(2)} ${returnForm.currency}`
    };

    if (editingReturnIndex >= 0) {
      // Update existing item
      const updatedItems = [...returnItems];
      updatedItems[editingReturnIndex] = newItem;
      setReturnItems(updatedItems);
      setEditingReturnIndex(-1);
    } else {
      // Add new item
      setReturnItems([...returnItems, newItem]);
    }

    // Reset form
    setReturnForm({
      supplierCode: '',
      supplierName: '',
      itemNumber: '',
      barcode: '',
      itemName: '',
      quantity: '',
      unitPrice: '',
      currency: 'YER',
      reasonForReturn: 'Expired',
      returnValue: 0,
      expiryDate: '',
      attachedImage: null
    });
    
    // Clear item search state
    setItemSearchQuery('');
    setItemSearchResults([]);
    setShowItemSearchResults(false);
    
    setSuccess('Return item added successfully!');
    setTimeout(() => setSuccess(''), 3000);
  };

  const editReturnItem = (index) => {
    const item = returnItems[index];
    setReturnForm({
      supplierCode: item.supplierCode,
      supplierName: item.supplierName,
      itemNumber: item.itemNumber || '',
      barcode: item.barcode || '',
      itemName: item.itemName,
      quantity: item.quantity.toString(),
      unitPrice: item.unitPrice.toString(),
      currency: item.currency || 'YER',
      reasonForReturn: item.reasonForReturn || 'Expired',
      returnValue: item.returnValue,
      expiryDate: item.expiryDate || '',
      attachedImage: item.attachedImage || null
    });
    setItemSearchQuery(item.itemName);
    setEditingReturnIndex(index);
  };

  const deleteReturnItem = (index) => {
    if (window.confirm('Are you sure you want to delete this return item?')) {
      const updatedItems = returnItems.filter((_, i) => i !== index);
      setReturnItems(updatedItems);
      setSuccess('Return item deleted successfully!');
      setTimeout(() => setSuccess(''), 3000);
    }
  };

  const exportReturnFormPDF = async () => {
    if (returnItems.length === 0) {
      setError('No return items to export');
      setTimeout(() => setError(''), 3000);
      return;
    }

    try {
      const response = await axios.post(`${API}/reports/supplier-return-pdf`, {
        returnItems: returnItems
      }, {
        responseType: 'blob',
        headers: getAuthHeaders(token)
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const now = new Date();
      const dateStr = now.toISOString().split('T')[0];
      link.setAttribute('download', `supplier_return_form_${dateStr}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Supplier Return Form PDF exported successfully!');
      setTimeout(() => setSuccess(''), 5000);  // Show success message for 5 seconds
    } catch (error) {
      setError('Error exporting return form PDF');
      console.error('Error exporting PDF:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  // NEW: Enhanced Excel export function
  const exportReturnFormExcel = async () => {
    if (returnItems.length === 0) {
      setError('No return items to export');
      setTimeout(() => setError(''), 3000);
      return;
    }

    try {
      const response = await axios.post(`${API}/reports/supplier-return-excel`, {
        returnItems: returnItems
      }, {
        responseType: 'blob',
        headers: getAuthHeaders(token)
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const now = new Date();
      const dateStr = now.toISOString().split('T')[0];
      link.setAttribute('download', `supplier_return_form_${dateStr}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Supplier Return Form Excel exported successfully!');
      setTimeout(() => setSuccess(''), 5000);  // Show success message for 5 seconds
    } catch (error) {
      setError('Error exporting return form Excel');
      console.error('Error exporting Excel:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const clearReturnForm = () => {
    if (window.confirm('Are you sure you want to clear all return items?')) {
      setReturnItems([]);
      setReturnForm({
        supplierCode: '',
        supplierName: '',
        itemNumber: '',
        barcode: '',
        itemName: '',
        quantity: '',
        unitPrice: '',
        currency: 'YER',
        reasonForReturn: 'Expired',
        returnValue: 0,
        expiryDate: '',
        attachedImage: null
      });
      setEditingReturnIndex(-1);
      // Clear item search state
      setItemSearchQuery('');
      setItemSearchResults([]);
      setShowItemSearchResults(false);
      setSuccess('Return form cleared successfully!');
      setTimeout(() => setSuccess(''), 3000);
    }
  };

  // Admin Functions
  const fetchPendingUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users/pending`, {
        headers: getAuthHeaders(token)
      });
      setPendingUsers(response.data);
    } catch (error) {
      console.error('Error fetching pending users:', error);
      if (error.response?.status === 403) {
        setError('Admin access required');
        setTimeout(() => setError(''), 3000);
      } else if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const fetchAllUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`, {
        headers: getAuthHeaders(token)
      });
      setAllUsers(response.data);
    } catch (error) {
      console.error('Error fetching all users:', error);
      if (error.response?.status === 403) {
        setError('Admin access required');
        setTimeout(() => setError(''), 3000);
      } else if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const approveUser = async (userId, approvalStatus) => {
    try {
      await axios.post(`${API}/admin/users/approve`, {
        user_id: userId,
        approval_status: approvalStatus
      }, {
        headers: getAuthHeaders(token)
      });
      
      setSuccess(`User ${approvalStatus} successfully!`);
      setTimeout(() => setSuccess(''), 3000);
      
      // Refresh user lists
      fetchPendingUsers();
      fetchAllUsers();
    } catch (error) {
      setError(`Error ${approvalStatus === 'approved' ? 'approving' : 'rejecting'} user`);
      console.error('Error approving user:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const makeUserAdmin = async (userId) => {
    if (window.confirm('Are you sure you want to grant admin privileges to this user?')) {
      try {
        await axios.post(`${API}/admin/users/${userId}/make-admin`, {}, {
          headers: getAuthHeaders(token)
        });
        
        setSuccess('User granted admin privileges successfully!');
        setTimeout(() => setSuccess(''), 3000);
        
        fetchAllUsers();
      } catch (error) {
        setError('Error granting admin privileges');
        console.error('Error making user admin:', error);
        if (error.response?.status === 401) {
          logout();
        }
      }
    }
  };

  // Debounced search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      handleGlobalSearch(globalSearch);
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [globalSearch]);

  // Call enhanced KPI instead of basic KPI
  const fetchKPI = async () => {
    try {
      const response = await axios.get(`${API}/kpi/enhanced`, {  // Changed to enhanced endpoint
        headers: getAuthHeaders(token)
      });
      setEnhancedKpi(response.data);  // Store in enhancedKpi state
      
      // Also set basic KPI for backward compatibility
      setKpi({
        total_products: response.data.total_products,
        low_stock_items: response.data.low_stock_items,  // This is now separate from out_of_stock
        expiring_soon: response.data.expiring_soon,
        expired_products: response.data.expired_products
      });
    } catch (error) {
      console.error('Error fetching enhanced KPI:', error);
      setError('Error fetching KPI data');
    }
  };

  // Fetch enhanced KPI data
  const fetchEnhancedKpi = async () => {
    try {
      const response = await axios.get(`${API}/kpi/enhanced`, {
        headers: getAuthHeaders(token)
      });
      setEnhancedKpi(response.data);
    } catch (error) {
      console.error('Error fetching enhanced KPI:', error);
    }
  };

  // Fetch out-of-stock products
  const fetchOutOfStockProducts = async () => {
    try {
      const params = new URLSearchParams();
      if (outOfStockFilters.section) params.append('section', outOfStockFilters.section);
      if (outOfStockFilters.supplier) params.append('supplier', outOfStockFilters.supplier);
      
      const response = await axios.get(`${API}/products/out-of-stock?${params}`, {
        headers: getAuthHeaders(token)
      });
      
      setOutOfStockProducts(response.data.out_of_stock_products || []);
    } catch (error) {
      console.error('Error fetching out-of-stock products:', error);
      setError('Error fetching out-of-stock products');
    }
  };

  // Fetch supplier dashboard data
  const fetchSupplierDashboard = async () => {
    try {
      const params = new URLSearchParams();
      if (supplierDashboardSection) params.append('section', supplierDashboardSection);
      
      const response = await axios.get(`${API}/suppliers/dashboard?${params}`, {
        headers: getAuthHeaders(token)
      });
      
      setSupplierDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching supplier dashboard:', error);
      setError('Error fetching supplier dashboard');
    }
  };

  // Export out-of-stock products
  const exportOutOfStock = async () => {
    try {
      const params = new URLSearchParams();
      if (outOfStockFilters.section) params.append('section', outOfStockFilters.section);
      if (outOfStockFilters.supplier) params.append('supplier', outOfStockFilters.supplier);
      
      const response = await axios.get(`${API}/export/out-of-stock-excel?${params}`, {
        responseType: 'blob',
        headers: getAuthHeaders(token)
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `out_of_stock_products_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Out-of-stock products exported successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError('Error exporting out-of-stock products');
      console.error('Error:', error);
    }
  };

  const fetchTopSuppliers = async () => {
    try {
      const response = await axios.get(`${API}/kpi/top-suppliers`, {
        headers: getAuthHeaders(token)
      });
      setTopSuppliers(response.data.top_suppliers || []);
    } catch (error) {
      console.error('Error fetching top suppliers:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const fetchDonutChartData = async () => {
    try {
      const response = await axios.get(`${API}/kpi/donut-chart`, {
        headers: getAuthHeaders(token)
      });
      setDonutChartData(response.data);
    } catch (error) {
      console.error('Error fetching donut chart data:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const response = await axios.get(`${API}/products?${params}`, {
        headers: getAuthHeaders(token)
      });
      setProducts(response.data);
    } catch (error) {
      setError('Error fetching items');
      console.error('Error fetching products:', error);
      if (error.response?.status === 401) {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API}/alerts?is_read=false`, {
        headers: getAuthHeaders(token)
      });
      setAlerts(response.data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories`, {
        headers: getAuthHeaders(token)
      });
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const fetchSuppliers = async () => {
    try {
      const response = await axios.get(`${API}/suppliers`, {
        headers: getAuthHeaders(token)
      });
      setSuppliers(response.data.suppliers || []);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  // Enhanced real-time filter refresh function
  const refreshAllFilters = async () => {
    try {
      const response = await axios.get(`${API}/filters/refresh`, {
        headers: getAuthHeaders(token)
      });
      
      const filterData = response.data;
      
      // Update all filter states with real-time data
      setCategories({
        departments: filterData.departments || [],
        sections: filterData.sections || [],
        families: filterData.families || [],
        sub_families: filterData.sub_families || []
      });
      
      setSuppliers(filterData.suppliers || []);
      
      console.log(`🔄 Filters refreshed at ${filterData.last_updated}:`, {
        departments: filterData.departments?.length || 0,
        sections: filterData.sections?.length || 0,
        suppliers: filterData.suppliers?.length || 0
      });
      
    } catch (error) {
      console.error('Error refreshing filters:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const generateAlerts = async () => {
    try {
      await axios.post(`${API}/alerts/generate`, {}, {
        headers: getAuthHeaders(token)
      });
    } catch (error) {
      console.error('Error generating alerts:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  // PDF Reports
  const downloadSupplierKPIPDF = async () => {
    try {
      const response = await axios.get(`${API}/reports/supplier-kpi-pdf`, {
        responseType: 'blob',
        headers: getAuthHeaders(token)
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'supplier_kpi_summary.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Supplier KPI PDF downloaded successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError('Error downloading Supplier KPI PDF');
      console.error('Error downloading PDF:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const downloadExpiringItemsPDF = async () => {
    try {
      const response = await axios.get(`${API}/reports/expiring-items-pdf`, {
        responseType: 'blob',
        headers: getAuthHeaders(token)
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'expiring_items_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Expiring Items PDF downloaded successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError('Error downloading Expiring Items PDF');
      console.error('Error downloading PDF:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const downloadMonthlyExpiredPDF = async () => {
    try {
      const response = await axios.get(`${API}/reports/monthly-expired-pdf`, {
        responseType: 'blob',
        headers: getAuthHeaders(token)
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename with current month
      const now = new Date();
      const monthNames = ["january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"];
      const monthName = monthNames[now.getMonth()];
      
      link.setAttribute('download', `monthly_expired_items_${monthName}_${now.getFullYear()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Monthly Expired Items PDF downloaded successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError('Error downloading Monthly Expired Items PDF');
      console.error('Error downloading PDF:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Enhanced file type validation - support images and PDFs
      const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'];
      if (!validTypes.includes(file.type)) {
        setError('Please select a valid file (JPG, PNG, GIF, WebP, or PDF)');
        setTimeout(() => setError(''), 5000); // Auto-clear error
        return;
      }
      
      // Enhanced file size validation (max 10MB for processing)
      if (file.size > 10 * 1024 * 1024) {
        setError(`File size (${(file.size / 1024 / 1024).toFixed(2)}MB) must be less than 10MB`);
        setTimeout(() => setError(''), 5000); // Auto-clear error
        return;
      }
      
      setSelectedImage(file);
      
      // Show processing information for images
      if (file.type.startsWith('image/')) {
        setSuccess(`📸 Image selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)
        
✨ Processing will include:
• Automatic orientation correction
• Smart centering and framing  
• Background enhancement
• Professional quality optimization
• Standardized 800×800 format`);
        setTimeout(() => setSuccess(''), 8000);
      } else {
        setSuccess(`📄 File selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);
        setTimeout(() => setSuccess(''), 3000);
      }
      
      // Create preview for images (PDF will show file name)
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          setImagePreview(e.target.result);
          setError(''); // Clear any previous errors
        };
        reader.onerror = () => {
          setError('Failed to read image file. Please try again.');
          setTimeout(() => setError(''), 5000);
        };
        reader.readAsDataURL(file);
      } else if (file.type === 'application/pdf') {
        // For PDF files, show a PDF icon preview
        setImagePreview('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiByeD0iMTAiIGZpbGw9IiNGRjQwNDAiLz4KPHRleHQgeD0iNTAiIHk9IjU1IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+UERGPC90ZXh0Pgo8L3N2Zz4K');
        setError(''); // Clear any previous errors
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(''); // Clear any previous errors
      
      if (editingProduct) {
        // For updates, use JSON API (image upload separate)
        const productData = {
          ...formData,
          expiry_date: new Date(formData.expiry_date).toISOString(),
          quantity: parseInt(formData.quantity),
          selling_price: formData.selling_price ? parseFloat(formData.selling_price) : null,
          purchase_price: formData.purchase_price ? parseFloat(formData.purchase_price) : null
        };

        const response = await axios.put(`${API}/products/${editingProduct.id}`, productData, {
          headers: getAuthHeaders(token)
        });
        
        console.log('Product update response:', response.data);
        
        // Upload image separately if selected
        if (selectedImage) {
          try {
            const imageFormData = new FormData();
            imageFormData.append('file', selectedImage);
            imageFormData.append('product_id', editingProduct.id);
            
            const imageResponse = await axios.post(`${API}/upload-image`, imageFormData, {
              headers: {
                ...getAuthHeaders(token),
                'Content-Type': 'multipart/form-data'
              }
            });
            
            console.log('Image upload response:', imageResponse.data);
            
            // Update the product with the new image URL
            if (imageResponse.data.image_url) {
              await axios.put(`${API}/products/${editingProduct.id}`, {
                image_url: imageResponse.data.image_url
              }, {
                headers: getAuthHeaders(token)
              });
            }
            
          } catch (imageError) {
            console.error('Image upload failed:', imageError);
            if (imageError.response?.status === 403) {
              setError('Image upload failed: Access denied. Only administrators can upload images.');
            } else if (imageError.response?.status === 401) {
              logout();
            } else {
              setError(`Image upload failed: ${imageError.response?.data?.detail || imageError.message}`);
            }
            // Don't return here - still want to show success for product update
          }
        }
        
        setSuccess('Item updated successfully!');
        
        // Ensure form closes after successful update
        setTimeout(() => {
          resetForm(); // This will close the form
        }, 100); // Small delay to ensure success message is visible
      } else {
        // For new products, use FormData for file upload
        const submitData = new FormData();
        Object.entries(formData).forEach(([key, value]) => {
          if (value !== '' && value !== null) {
            if (key === 'expiry_date') {
              submitData.append(key, new Date(value).toISOString());
            } else if (key === 'quantity') {
              submitData.append(key, parseInt(value) || 0);
            } else if (key === 'selling_price' || key === 'purchase_price') {
              const numValue = parseFloat(value);
              if (!isNaN(numValue)) {
                submitData.append(key, numValue);
              }
            } else {
              submitData.append(key, value);
            }
          }
        });
        
        if (selectedImage) {
          submitData.append('image', selectedImage);
        }
        
        const response = await axios.post(`${API}/products/with-image`, submitData, {
          headers: {
            ...getAuthHeaders(token),
            'Content-Type': 'multipart/form-data',
          },
        });
        
        console.log('Product creation response:', response.data);
        setSuccess('Item added successfully!');
        
        // Ensure form closes after successful creation
        setTimeout(() => {
          resetForm(); // This will close the form
        }, 100); // Small delay to ensure success message is visible
      }
      
      // Always refresh data after successful operation
      resetForm();
      await Promise.all([
        fetchProducts(),
        fetchKPI(),
        fetchTopSuppliers(),
        fetchDonutChartData(),
        fetchAlerts(),
        refreshAllFilters() // Refresh filters in real-time after adding/editing items
      ]);
      
      setTimeout(() => setSuccess(''), 3000);
      
    } catch (error) {
      console.error('Error saving product:', error);
      
      if (error.response?.status === 401) {
        logout();
      } else if (error.response?.status === 403) {
        setError('Access denied. Only administrators can modify inventory.');
      } else if (error.response?.status === 404) {
        setError('Product not found. It may have been deleted by another user. Please refresh and try again.');
        // Refresh the product list
        fetchProducts();
      } else if (error.response?.data?.detail) {
        setError(`Error: ${error.response.data.detail}`);
      } else if (error.response?.data?.message) {
        setError(`Error: ${error.response.data.message}`);
      } else if (error.response?.status === 500) {
        setError('Server error. Please check all required fields and try again.');
      } else {
        setError(`Error saving item: ${error.message || 'Please check all required fields.'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (productId) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      try {
        await axios.delete(`${API}/products/${productId}`, {
          headers: getAuthHeaders(token)
        });
        setSuccess('Item deleted successfully!');
        fetchProducts();
        fetchKPI();
        fetchTopSuppliers();
        fetchDonutChartData();
        setTimeout(() => setSuccess(''), 3000);
      } catch (error) {
        setError('Error deleting item');
        console.error('Error deleting product:', error);
        if (error.response?.status === 401) {
          logout();
        }
      }
    }
  };

  const handleEdit = (product) => {
    console.log('Editing product:', product); // Debug log
    
    // Ensure product exists and has valid ID
    if (!product || !product.id) {
      setError('Invalid product selected for editing');
      return;
    }
    
    setEditingProduct(product);
    setFormData({
      product_name: product.product_name || '',
      item_number: product.item_number || '',
      department: product.department || '',
      section: product.section || '',
      family: product.family || '',
      sub_family: product.sub_family || '',
      supplier_code: product.supplier_code || '',
      supplier: product.supplier || '',
      expiry_date: product.expiry_date ? new Date(product.expiry_date).toISOString().split('T')[0] : '',
      quantity: product.quantity?.toString() || '',
      barcode: product.barcode || '',
      selling_price: product.selling_price?.toString() || '',
      purchase_price: product.purchase_price?.toString() || '',
      arabic_description: product.arabic_description || '',
      description: product.description || '',
      location: product.location || '',
      brand: product.brand || ''
    });
    
    // Handle existing product image
    if (product.image_url) {
      setImagePreview(`${BACKEND_URL}${product.image_url}`);
    } else {
      setImagePreview(null);
    }
    setSelectedImage(null);
    setShowAddForm(true);
  };

  const resetForm = () => {
    setFormData({
      product_name: '',
      item_number: '',
      department: '',
      section: '',
      family: '',
      sub_family: '',
      supplier_code: '',
      supplier: '',
      expiry_date: '',
      quantity: '',
      barcode: '',
      selling_price: '',
      purchase_price: '',
      arabic_description: '',
      description: '',
      location: '',
      brand: ''
    });
    setEditingProduct(null);
    setSelectedImage(null);
    setImagePreview(null);
    setShowAddForm(false);
  };

  const handleImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      const response = await axios.post(`${API}/import/excel?update_mode=${importMode}`, formData, {
        headers: {
          ...getAuthHeaders(token),
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setSuccess(`Import successful! ${response.data.items_imported} items imported, ${response.data.items_updated || 0} items updated.`);
      if (response.data.errors && response.data.errors.length > 0) {
        setError(`Some errors occurred: ${response.data.errors.join(', ')}`);
      }
      
      fetchProducts();
      fetchKPI();
      fetchTopSuppliers();
      fetchDonutChartData();
      refreshAllFilters(); // Refresh filters after Excel import
      setShowImportModal(false);
      setShowAdvancedImport(false);
      setTimeout(() => {
        setSuccess('');
        setError('');
      }, 5000);
    } catch (error) {
      setError(error.response?.data?.detail || 'Error importing file');
      console.error('Error importing file:', error);
      if (error.response?.status === 401) {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await axios.get(`${API}/export/excel`, {
        responseType: 'blob',
        headers: getAuthHeaders(token)
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'items_export.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Export completed successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError('Error exporting items');
      console.error('Error exporting products:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await axios.get(`${API}/export/template`, {
        responseType: 'blob',
        headers: getAuthHeaders(token)
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'items_import_template.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Template downloaded successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError('Error downloading template');
      console.error('Error downloading template:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  // Search barcode scanner
  const startSearchBarcodeScanner = () => {
    setIsScanning(true);
    
    setTimeout(() => {
      if (searchScannerRef.current) {
        searchBarcodeScanner.current = new Html5QrcodeScanner(
          "search-barcode-reader", 
          { 
            fps: 10,
            qrbox: { width: 250, height: 250 },
            aspectRatio: 1.0,
            showTorchButtonIfSupported: true
          }, 
          false
        );
        
        searchBarcodeScanner.current.render(
          (decodedText, decodedResult) => {
            console.log(`Search barcode scanned: ${decodedText}`);
            handleBarcodeResult(decodedText);
            stopSearchBarcodeScanner();
          },
          (error) => {
            // Suppress frequent scanning errors
            if (!error.includes('No QR code found')) {
              console.warn(`Search barcode scanning error: ${error}`);
            }
          }
        );
      }
    }, 100);
  };

  const stopSearchBarcodeScanner = () => {
    if (searchBarcodeScanner.current) {
      searchBarcodeScanner.current.clear().catch(console.error);
      searchBarcodeScanner.current = null;
    }
    setIsScanning(false);
  };

  // Enhanced mobile barcode scanner with iOS support and better error handling
  const startEnhancedBarcodeScanner = async () => {
    try {
      setIsZxingScanning(true);
      setError(''); // Clear any previous errors
      setSuccess(''); // Clear any previous success messages
      
      // Check for browser support
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setError('Camera access not supported. Please use manual barcode input or try a different browser.');
        setIsZxingScanning(false);
        return;
      }
      
      // Detect device and browser type
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
      const isAndroid = /Android/.test(navigator.userAgent);
      const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
      
      // Set device-specific constraints
      const constraints = {
        video: {
          facingMode: 'environment', // Use back camera
          width: { 
            ideal: isIOS ? 640 : isAndroid ? 800 : 1280,
            min: 320,
            max: isIOS ? 1024 : 1920
          },
          height: { 
            ideal: isIOS ? 480 : isAndroid ? 600 : 720,
            min: 240,
            max: isIOS ? 768 : 1080
          }
        }
      };
      
      // Request camera permission explicitly
      try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        // Stop the test stream immediately - we just needed permission
        stream.getTracks().forEach(track => track.stop());
        
        // Show loading indicator
        setSuccess('Camera permission granted. Starting scanner...');
        
      } catch (permissionError) {
        console.error('Camera permission error:', permissionError);
        
        if (permissionError.name === 'NotAllowedError') {
          if (isIOS) {
            setError('iOS: Camera blocked. Go to Safari Settings → Website Settings → Camera → Allow, then refresh this page.');
          } else if (isAndroid) {
            setError('Android: Camera permission denied. Please allow camera access in your browser settings and refresh.');
          } else {
            setError('Camera permission denied. Please allow camera access in your browser settings and refresh.');
          }
        } else if (permissionError.name === 'NotFoundError') {
          setError('No camera found on this device. Please use manual barcode input.');
        } else {
          setError(`Camera setup failed: ${permissionError.message}. Please use manual barcode input.`);
        }
        
        setIsZxingScanning(false);
        return;
      }
      
      try {
        const codeReader = new BrowserMultiFormatReader();
        setZxingCodeReader(codeReader);
        
        // Check if video element exists before attempting to use it
        const videoElement = document.getElementById('video-scanner');
        if (!videoElement) {
          console.error('Video scanner element not found in DOM');
          setError('Scanner video element not available. Please try the fallback scanner.');
          setIsZxingScanning(false);
          return;
        }
        
        // Device-specific timeout
        const timeoutDuration = isIOS ? 15000 : isAndroid ? 20000 : 25000;
        const scanTimeout = setTimeout(() => {
          console.log('Scanner timeout - stopping scan');
          stopEnhancedBarcodeScanner();
          setError(`Scanner timeout after ${timeoutDuration/1000} seconds. Please try manual barcode input or the fallback scanner.`);
        }, timeoutDuration);
        
        // Show scanning status
        setSuccess('Camera ready. Point at barcode to scan...');
        
        let scanAttempts = 0;
        const maxAttempts = 3;
        let scanResult = null;
        
        // Enhanced scanning with retry mechanism
        while (scanAttempts < maxAttempts && !scanResult) {
          try {
            scanAttempts++;
            setSuccess(`Scanning attempt ${scanAttempts}/${maxAttempts}. Point at barcode...`);
            
            const result = await codeReader.decodeOnceFromVideoDevice(undefined, 'video-scanner');
            
            if (result && result.text) {
              scanResult = result;
              break;
            }
            
            // Wait between attempts
            if (scanAttempts < maxAttempts) {
              await new Promise(resolve => setTimeout(resolve, 1000));
            }
            
          } catch (attemptError) {
            console.log(`Scan attempt ${scanAttempts} failed:`, attemptError);
            if (scanAttempts === maxAttempts) {
              throw attemptError;
            }
          }
        }
        
        clearTimeout(scanTimeout);
        
        if (scanResult && scanResult.text) {
          console.log('Enhanced barcode scanned:', scanResult.text);
          lookupBarcode(scanResult.text);
          setSuccess(`✅ Barcode scanned successfully: ${scanResult.text}`);
          setTimeout(() => setSuccess(''), 5000);
        } else {
          setError(`No barcode detected after ${maxAttempts} attempts. Please try manual input or the fallback scanner.`);
          setTimeout(() => setError(''), 7000); // Auto-clear error
        }
        
        stopEnhancedBarcodeScanner();
        
      } catch (scanError) {
        console.error('ZXing scan error:', scanError);
        
        if (scanError.name === 'NotAllowedError') {
          setError('Camera access was denied during scanning. Click "Retry Scanner" below or refresh and allow camera access.');
        } else if (scanError.name === 'NotFoundError') {
          setError('Camera not found during scanning. Please check your camera connection and click "Retry Scanner".');
        } else if (scanError.name === 'AbortError') {
          setError('Scanning was interrupted. Click "Retry Scanner" to try again.');
        } else if (scanError.name === 'OverconstrainedError') {
          setError('Camera constraints not supported. Trying fallback scanner...');
          // Automatically try fallback scanner
          setTimeout(() => {
            startBarcodeScanner();
          }, 1000);
        } else {
          setError(`Scanner error: ${scanError.message}. Please try manual barcode input.`);
        }
        
        stopEnhancedBarcodeScanner();
      }
      
    } catch (error) {
      console.error('Enhanced scanner setup error:', error);
      setError(`Scanner initialization failed: ${error.message}. Please use manual barcode input.`);
      setIsZxingScanning(false);
    }
  };

  const stopEnhancedBarcodeScanner = () => {
    if (zxingCodeReader) {
      try {
        zxingCodeReader.reset();
      } catch (error) {
        console.warn('Error resetting ZXing scanner (non-critical):', error);
      } finally {
        setZxingCodeReader(null);
      }
    }
    setIsZxingScanning(false);
    
    // Stop video streams safely
    try {
      const video = document.getElementById('video-scanner');
      if (video && video.srcObject) {
        const stream = video.srcObject;
        if (stream && typeof stream.getTracks === 'function') {
          const tracks = stream.getTracks();
          tracks.forEach(track => {
            try {
              track.stop();
            } catch (trackError) {
              console.warn('Error stopping track (non-critical):', trackError);
            }
          });
          video.srcObject = null;
        }
      }
    } catch (videoError) {
      console.warn('Error cleaning up video stream (non-critical):', videoError);
    }
  };

  const startBarcodeScanner = () => {
    // Stop any existing scanner first
    stopBarcodeScanner();
    
    setScannerActive(true);
    setError(''); // Clear any errors
    
    setTimeout(() => {
      const scannerContainer = document.getElementById('barcode-reader');
      if (scannerContainer) {  // Removed scannerRef.current dependency that was causing race condition
        try {
          // Clear any existing content
          scannerContainer.innerHTML = '';
          
          html5QrcodeScanner.current = new Html5QrcodeScanner(
            "barcode-reader", 
            { 
              fps: 10,
              qrbox: { width: 250, height: 250 },
              aspectRatio: 1.0,
              showTorchButtonIfSupported: true,
              showZoomSliderIfSupported: true,
              defaultZoomValueIfSupported: 2,
            },
            false
          );
          
          html5QrcodeScanner.current.render(
            (decodedText) => {
              console.log('Fallback barcode scanned:', decodedText);
              lookupBarcode(decodedText);
              stopBarcodeScanner();
              setSuccess('Barcode scanned successfully!');
              setTimeout(() => setSuccess(''), 3000);
            },
            (error) => {
              // Don't log every scanning attempt error
              if (!error.includes('No MultiFormat Readers')) {
                console.debug('Scanner error:', error);
              }
            }
          );
          
        } catch (error) {
          console.error('Failed to start fallback scanner:', error);
          setError('Failed to initialize barcode scanner. Please check camera permissions.');
          setScannerActive(false);
        }
      }
    }, 300);  // Increased timeout for proper DOM rendering
  };

  const stopBarcodeScanner = () => {
    if (html5QrcodeScanner.current) {
      try {
        // Check if the scanner element still exists in DOM
        const scannerElement = document.getElementById('barcode-reader');
        if (scannerElement) {
          // Clear scanner content safely
          html5QrcodeScanner.current.clear().then(() => {
            console.log('Scanner cleared successfully');
          }).catch((error) => {
            console.warn('Scanner clear error (non-critical):', error);
            // If clear fails, try to manually clean the container
            try {
              scannerElement.innerHTML = '';
            } catch (cleanupError) {
              console.warn('Manual cleanup error (non-critical):', cleanupError);
            }
          });
        }
      } catch (error) {
        console.warn('Error clearing scanner (non-critical):', error);
      } finally {
        html5QrcodeScanner.current = null;
      }
    }
    setScannerActive(false);
    setScannedProduct(null);
  };

  const lookupBarcode = async (barcode) => {
    try {
      const response = await axios.get(`${API}/products/barcode/${barcode}`, {
        headers: getAuthHeaders(token)
      });
      setScannedProduct(response.data);
    } catch (error) {
      if (error.response?.status === 401) {
        logout();
      } else {
        setError('Item not found for this barcode');
        setTimeout(() => setError(''), 3000);
      }
    }
  };

  const handleManualBarcodeSubmit = (e) => {
    e.preventDefault();
    if (manualBarcode.trim()) {
      lookupBarcode(manualBarcode.trim());
      setManualBarcode('');
    }
  };

  // Mobile-optimized product card component
  const MobileProductCard = ({ product, showStockValue = false }) => {
    const isExpired = product.expiry_date && new Date(product.expiry_date) < new Date();
    const isExpiringSoon = product.expiry_date && 
      new Date(product.expiry_date) <= new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) &&
      new Date(product.expiry_date) >= new Date();
    
    const stockValue = product.purchase_price ? (product.quantity * product.purchase_price) : null;
    
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-4 mx-2 my-3 max-w-sm mx-auto">
        {/* Product Image */}
        <div className="flex justify-center mb-4">
          {product.image_url ? (
            <img 
              src={`${BACKEND_URL}${product.image_url}`}
              alt={product.product_name}
              className="w-24 h-24 object-cover rounded-lg border-2 border-gray-200"
            />
          ) : (
            <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg flex items-center justify-center border-2 border-blue-300">
              <svg className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a8.949 8.949 0 008.354-5.646z" />
              </svg>
            </div>
          )}
        </div>
        
        {/* Product Title */}
        <h3 className="text-lg font-bold text-gray-900 text-center mb-3 leading-tight">
          {product.product_name}
        </h3>
        
        {/* Product Details */}
        <div className="space-y-2 text-sm">
          {/* Barcode */}
          {product.barcode && (
            <div className="flex justify-between items-center py-1">
              <span className="text-gray-600 font-medium">Barcode:</span>
              <span className="font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">
                {product.barcode}
              </span>
            </div>
          )}
          
          {/* Stock Available */}
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 font-medium">Stock Available:</span>
            <span className={`font-bold px-2 py-1 rounded ${
              product.quantity < 10 ? 'text-red-700 bg-red-100' : 
              product.quantity < 50 ? 'text-yellow-700 bg-yellow-100' : 
              'text-green-700 bg-green-100'
            }`}>
              {product.quantity}
            </span>
          </div>
          
          {/* Supplier */}
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 font-medium">Supplier:</span>
            <span className="text-gray-900 text-right flex-1 ml-2">
              {product.supplier}
            </span>
          </div>
          
          {/* Expiry Date */}
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 font-medium">Expiry Date:</span>
            <span className={`px-2 py-1 rounded text-sm font-medium ${
              isExpired ? 'text-red-700 bg-red-100' :
              isExpiringSoon ? 'text-yellow-700 bg-yellow-100' :
              'text-green-700 bg-green-100'
            }`}>
              {formatDate(product.expiry_date)}
            </span>
          </div>
          
          {/* Selling Price */}
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 font-medium">Selling Price:</span>
            <span className="text-xl font-bold text-green-600">
              {formatCurrency(product.selling_price)}
            </span>
          </div>
          
          {/* Purchase Price & Stock Value (if available) */}
          {product.purchase_price && (
            <>
              <div className="flex justify-between items-center py-1">
                <span className="text-gray-600 font-medium">Purchase Price:</span>
                <span className="text-lg font-semibold text-blue-600">
                  {formatCurrency(product.purchase_price)}
                </span>
              </div>
              
              {showStockValue && stockValue && (
                <div className="flex justify-between items-center py-1 bg-blue-50 px-2 rounded">
                  <span className="text-blue-700 font-medium">Stock Value:</span>
                  <span className="text-xl font-bold text-blue-700">
                    {formatCurrency(stockValue)}
                  </span>
                </div>
              )}
            </>
          )}
        </div>
        
        {/* Status Badge */}
        <div className="mt-4 text-center">
          <span className={`px-4 py-2 rounded-full text-sm font-medium ${
            isExpired ? 'bg-red-100 text-red-800' :
            isExpiringSoon ? 'bg-yellow-100 text-yellow-800' :
            'bg-green-100 text-green-800'
          }`}>
            {isExpired ? '❌ Expired' : isExpiringSoon ? '⚠️ Expiring Soon' : '✅ Fresh'}
          </span>
        </div>
      </div>
    );
  };

  // Enhanced Product Card Component with Out of Stock Indicators
  const EnhancedProductCard = ({ product, showStockValue = false }) => {
    const isExpired = product.expiry_date && new Date(product.expiry_date) < new Date();
    const isExpiringSoon = product.expiry_date && 
      new Date(product.expiry_date) <= new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) &&
      new Date(product.expiry_date) >= new Date();
    
    const isOutOfStock = product.quantity === 0;
    const isLowStock = product.quantity > 0 && product.quantity <= 5;
    
    // Calculate stock value with currency
    const stockValue = product.purchase_price && product.purchase_currency ? 
      (product.quantity * product.purchase_price) : null;
    
    return (
      <div className={`bg-white rounded-xl shadow-lg border-2 p-4 mx-2 my-3 max-w-sm mx-auto relative ${
        isOutOfStock ? 'border-red-300 bg-red-50' : 'border-gray-200'
      }`}>
        
        {/* Out of Stock Indicator */}
        {isOutOfStock && (
          <div className="absolute top-2 right-2 bg-red-600 text-white px-2 py-1 rounded-full text-xs font-bold z-10">
            🚨 OUT OF STOCK
          </div>
        )}

        {/* Product Image */}
        <div className="flex justify-center mb-4 mt-6">
          {product.image_url ? (
            <img 
              src={`${BACKEND_URL}${product.image_url}`}
              alt={product.product_name}
              className="w-24 h-24 object-contain rounded-lg border-2 border-gray-200"
              style={{ 
                aspectRatio: '1:1', 
                objectFit: 'contain',
                imageRendering: 'crisp-edges'
              }}
              loading="lazy"
            />
          ) : (
            <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg flex items-center justify-center border-2 border-blue-300">
              <svg className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a8.949 8.949 0 008.354-5.646z" />
              </svg>
            </div>
          )}
        </div>
        
        {/* Product Title */}
        <h3 className="text-lg font-bold text-gray-900 text-center mb-3 leading-tight">
          {product.product_name}
        </h3>
        
        {/* Product Details */}
        <div className="space-y-2 text-sm">
          {/* Barcode */}
          {product.barcode && (
            <div className="flex justify-between items-center py-1">
              <span className="text-gray-600 font-medium">Barcode:</span>
              <span className="font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">
                {product.barcode}
              </span>
            </div>
          )}
          
          {/* Stock Available */}
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 font-medium">Stock Available:</span>
            <span className={`font-bold px-2 py-1 rounded ${
              isOutOfStock ? 'text-red-700 bg-red-100' :
              isLowStock ? 'text-yellow-700 bg-yellow-100' : 
              'text-green-700 bg-green-100'
            }`}>
              {product.quantity}
              {isOutOfStock && <span className="ml-1 text-xs">🚨</span>}
            </span>
          </div>
          
          {/* Supplier */}
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 font-medium">Supplier:</span>
            <span className="text-gray-900 text-right flex-1 ml-2">
              {product.supplier}
            </span>
          </div>
          
          {/* Expiry Date */}
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 font-medium">Expiry Date:</span>
            <span className={`px-2 py-1 rounded text-sm font-medium ${
              isExpired ? 'text-red-700 bg-red-100' :
              isExpiringSoon ? 'text-yellow-700 bg-yellow-100' :
              'text-green-700 bg-green-100'
            }`}>
              {formatDate(product.expiry_date)}
            </span>
          </div>
          
          {/* Selling Price */}
          <div className="flex justify-between items-center py-1">
            <span className="text-gray-600 font-medium">Selling Price:</span>
            <span className="text-xl font-bold text-green-600">
              {formatCurrency(product.selling_price)}
            </span>
          </div>
          
          {/* Purchase Price & Currency */}
          {product.purchase_price && (
            <div className="flex justify-between items-center py-1">
              <span className="text-gray-600 font-medium">Purchase Price:</span>
              <span className="text-lg font-semibold text-blue-600">
                {product.purchase_price?.toFixed(2) || '0.00'} {product.purchase_currency || 'YER'}
              </span>
            </div>
          )}
          
          {/* Stock Value with Currency */}
          {showStockValue && stockValue && (
            <div className="flex justify-between items-center py-1 bg-blue-50 px-2 rounded">
              <span className="text-blue-700 font-medium">Stock Value:</span>
              <span className="text-lg font-bold text-blue-700">
                {stockValue.toFixed(2)} {product.purchase_currency || 'YER'}
              </span>
            </div>
          )}
          
          {/* Edit/Delete Buttons for Admin */}
          {user?.is_admin && (
            <div className="flex justify-between pt-3 mt-3 border-t border-gray-200">
              <button
                onClick={() => handleEdit(product)}
                className="bg-blue-500 text-white px-3 py-1 rounded-md text-xs hover:bg-blue-600 transition-colors"
              >
                ✏️ Edit
              </button>
              <button
                onClick={() => handleDelete(product.id)}
                className="bg-red-500 text-white px-3 py-1 rounded-md text-xs hover:bg-red-600 transition-colors"
              >
                🗑️ Delete
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const isExpired = (dateString) => {
    return new Date(dateString) < new Date();
  };

  const isExpiringSoon = (dateString) => {
    const expiryDate = new Date(dateString);
    const thirtyDaysFromNow = new Date();
    thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
    return expiryDate <= thirtyDaysFromNow && expiryDate >= new Date();
  };

  // Donut chart configuration
  const donutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
            return `${label}: ${value} items (${percentage}%)`;
          }
        }
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Global Search */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <img 
                  src="/geant_main_page_logo.png" 
                  alt="GEANT HYPERMARKET" 
                  className="h-8 sm:h-10 w-auto object-contain"
                  style={{ maxWidth: '150px' }}
                />
              </div>
              <div className="ml-3 hidden sm:block">
                <span className="text-lg font-semibold text-gray-900">Inventory Management System</span>
              </div>
            </div>
            
            {/* Navigation Tabs */}
            <div className="flex space-x-1 ml-6">
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'dashboard'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  📊 Dashboard
                </button>
                <button
                  onClick={() => setActiveTab('products')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'products'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  📦 Items
                </button>
                <button
                  onClick={() => setActiveTab('scanner')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'scanner'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  📱 Barcode Scanner
                </button>
                <button
                  onClick={() => setActiveTab('out-of-stock')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors relative ${
                    activeTab === 'out-of-stock'
                      ? 'bg-red-100 text-red-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  🚨 Out of Stock
                  {enhancedKpi.out_of_stock > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                      {enhancedKpi.out_of_stock}
                    </span>
                  )}
                </button>
                <button
                  onClick={() => setActiveTab('suppliers')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'suppliers'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  🏢 Suppliers
                </button>
                <button
                  onClick={() => setActiveTab('returns')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'returns'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  📋 Supplier Returns
                </button>
                {/* Admin tab - only visible for admin users */}
                {user?.is_admin && (
                  <button
                    onClick={() => {
                      setActiveTab('admin');
                      fetchPendingUsers();
                      fetchAllUsers();
                    }}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === 'admin'
                        ? 'bg-red-100 text-red-700'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    ⚙️ User Management
                  </button>
                )}
            </div>
            
            {/* Enhanced Search Bar - iOS Optimized */}
            <div className="flex items-center space-x-2 sm:space-x-4">
              <div className="relative flex-1 max-w-xs sm:max-w-sm">
                <input
                  type="search"
                  value={globalSearch}
                  onChange={(e) => setGlobalSearch(e.target.value)}
                  placeholder="Search items or scan barcode..."
                  className="w-full p-3 pl-10 pr-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white shadow-sm"
                  style={{
                    WebkitAppearance: 'none', // Remove iOS default styling
                    fontSize: '16px', // Prevent iOS zoom on focus
                    WebkitTapHighlightColor: 'transparent'
                  }}
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck="false"
                />
                <svg className="absolute left-3 top-3 w-4 h-4 text-gray-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                
                {/* Loading indicator */}
                {isSearching && (
                  <div className="absolute right-3 top-3">
                    <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  </div>
                )}
                
                {/* Clear button for iOS */}
                {globalSearch && (
                  <button
                    onClick={() => {
                      setGlobalSearch('');
                      setSearchResults([]);
                    }}
                    className="absolute right-3 top-3 p-0.5 rounded-full hover:bg-gray-200 transition-colors"
                    style={{ WebkitTapHighlightColor: 'transparent' }}
                  >
                    <svg className="w-3 h-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
                )}
              </div>
              
              <button
                onClick={() => isScanning ? stopSearchBarcodeScanner() : startSearchBarcodeScanner()}
                className={`p-3 rounded-xl transition-all duration-200 active:scale-95 shadow-sm ${
                  isScanning 
                    ? 'bg-red-600 text-white hover:bg-red-700 shadow-red-200' 
                    : 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-200'
                }`}
                title="Scan barcode"
                style={{ 
                  WebkitTapHighlightColor: 'transparent',
                  touchAction: 'manipulation'
                }}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
                
                {/* Enhanced Search Results Dropdown */}
                {globalSearch && searchResults.length > 0 && (
                  <div className="absolute top-full mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto">
                    <div className="p-2 border-b border-gray-100 bg-gray-50">
                      <p className="text-xs text-gray-600 font-medium">Click any result to view details</p>
                    </div>
                    {searchResults.slice(0, 8).map((item) => (
                      <div 
                        key={item.id} 
                        className="p-3 hover:bg-blue-50 border-b border-gray-100 cursor-pointer transition-all duration-150"
                        onClick={() => {
                          openProductDetails(item);
                          setGlobalSearch('');
                          setSearchResults([]);
                        }}
                      >
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            {item.image_url ? (
                              <img 
                                src={`${BACKEND_URL}${item.image_url}`} 
                                alt={item.product_name}
                                className="w-12 h-12 rounded-lg object-cover border"
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.nextSibling.style.display = 'flex';
                                }}
                              />
                            ) : null}
                            <div className={`${item.image_url ? 'hidden' : 'flex'} w-12 h-12 bg-gray-200 rounded-lg items-center justify-center border`}>
                              <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2z" />
                              </svg>
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-gray-900 truncate text-sm">{item.product_name}</div>
                            <div className="text-xs text-gray-600 mt-1">
                              <span className="font-medium">Code:</span> {item.item_number || item.barcode || 'N/A'}
                              {item.supplier && (
                                <>
                                  <span className="mx-1">•</span>
                                  <span className="font-medium">Supplier:</span> {item.supplier}
                                </>
                              )}
                            </div>
                            <div className="mt-1">
                              <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                                item.quantity <= 0 ? 'bg-red-100 text-red-700' :
                                item.quantity < 10 ? 'bg-yellow-100 text-yellow-700' :
                                'bg-green-100 text-green-700'
                              }`}>
                                {item.quantity <= 0 ? 'Out of Stock' : `${item.quantity} in stock`}
                              </span>
                            </div>
                          </div>
                          <div className="flex-shrink-0">
                            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </div>
                      </div>
                    ))}
                    {searchResults.length > 8 && (
                      <div className="p-3 text-center text-sm text-gray-500 bg-gray-50 border-t">
                        Showing 8 of {searchResults.length} results • Narrow your search for more specific results
                      </div>
                    )}
                  </div>
                )}
                
                {/* Search Barcode Scanner */}
                {isScanning && (
                  <div className="absolute top-full mt-1 left-0 right-0 bg-white border border-gray-300 rounded-md shadow-lg z-50 p-4">
                    <div className="text-center">
                      <div className="text-sm text-gray-600 mb-2">Point camera at barcode</div>
                      <div id="search-barcode-reader" ref={searchScannerRef} className="max-w-xs mx-auto"></div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* PWA Install Button */}
              {isInstallable && (
                <button
                  onClick={async () => {
                    if (installPrompt) {
                      installPrompt.prompt();
                      const result = await installPrompt.userChoice;
                      if (result.outcome === 'accepted') {
                        setSuccess('📱 App installation started! Check your home screen.');
                      }
                      setInstallPrompt(null);
                      setIsInstallable(false);
                    }
                  }}
                  className="hidden sm:flex items-center space-x-2 bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                  title="Install Geant App"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <span>Install App</span>
                </button>
              )}

              {/* Alert Badge */}
              {alerts.length > 0 && !showAlerts && (
                <div className="relative">
                  <button 
                    onClick={() => setShowAlerts(true)}
                    className="p-2 text-red-600 hover:text-red-800"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5-5-5h5zm-5-4h5v2h-5v-2zm0-6h5v4h-5V7z" />
                    </svg>
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {alerts.length > 99 ? '99+' : alerts.length}
                    </span>
                  </button>
                </div>
              )}

              {/* User Menu */}
              <div className="flex items-center space-x-3">
                <div className="text-sm text-gray-700">
                  Welcome, <span className="font-medium">{user?.username || 'User'}</span>
                </div>
                <button
                  onClick={logout}
                  className="bg-gray-600 text-white px-3 py-1 rounded-md hover:bg-gray-700 text-sm"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
      </header>

      {/* Success/Error Messages */}
      {success && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            {success}
          </div>
        </div>
      )}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        </div>
      )}

      {/* Product Details Modal - iOS Optimized */}
      {showProductDetails && selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end sm:items-center justify-center z-50">
          <div 
            className="bg-white rounded-t-xl sm:rounded-lg max-w-2xl w-full max-h-[90vh] sm:max-h-screen overflow-y-auto"
            style={{
              WebkitOverflowScrolling: 'touch', // iOS smooth scrolling
              transform: 'translateZ(0)', // Hardware acceleration
            }}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Product Details</h2>
              <button
                onClick={closeProductDetails}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6">
              {/* Product Image */}
              <div className="mb-6">
                <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden">
                  {selectedProduct.image_url ? (
                    <img 
                      src={`${BACKEND_URL}${selectedProduct.image_url}`} 
                      alt={selectedProduct.product_name}
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <div className="text-center text-gray-400">
                      <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2z" />
                      </svg>
                      <p className="text-sm">No Image Available</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Product Information */}
              <div className="space-y-4">
                {/* Product Name */}
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{selectedProduct.product_name}</h3>
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    selectedProduct.quantity <= 0 ? 'bg-red-100 text-red-800' :
                    selectedProduct.quantity < 10 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {selectedProduct.quantity <= 0 ? '❌ Out of Stock' :
                     selectedProduct.quantity < 10 ? '⚠️ Low Stock' : '✅ In Stock'}
                  </div>
                </div>

                {/* Product Details Grid */}
                <div className="space-y-4">
                  {/* Primary Information Card */}
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-gray-900 mb-3">Product Information</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-3">
                        <div>
                          <span className="text-sm font-medium text-gray-500">Item Code</span>
                          <p className="text-base font-medium text-gray-900">{selectedProduct.item_number || selectedProduct.barcode || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">Barcode</span>
                          <p className="text-base font-mono text-gray-900 bg-gray-50 px-2 py-1 rounded">{selectedProduct.barcode || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">Quantity in Stock</span>
                          <p className={`text-xl font-bold ${
                            selectedProduct.quantity <= 0 ? 'text-red-600' :
                            selectedProduct.quantity < 10 ? 'text-yellow-600' : 'text-green-600'
                          }`}>
                            {selectedProduct.quantity || 0}
                          </p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">Purchase Price</span>
                          <p className="text-base font-semibold text-blue-600">
                            {formatCurrency(selectedProduct.purchase_price, getProductCurrency(selectedProduct))}
                          </p>
                        </div>
                      </div>
                      
                      <div className="space-y-3">
                        <div>
                          <span className="text-sm font-medium text-gray-500">Stock Value</span>
                          <p className="text-xl font-bold text-green-600">
                            {calculateStockValue(selectedProduct.quantity, selectedProduct.purchase_price, getProductCurrency(selectedProduct))}
                          </p>
                          <p className="text-xs text-gray-500">Quantity × Purchase Price</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">Supplier</span>
                          <p className="text-base text-gray-900">{selectedProduct.supplier || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">Department</span>
                          <p className="text-base text-gray-900">{selectedProduct.department || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">Section</span>
                          <p className="text-base text-gray-900">{selectedProduct.section || 'N/A'}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Additional Information Card */}
                  {selectedProduct.expiry_date && (
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <h4 className="text-lg font-semibold text-gray-900 mb-3">Additional Information</h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm font-medium text-gray-500">Expiry Date</span>
                          <p className={`text-base font-medium ${
                            isExpired(selectedProduct.expiry_date) ? 'text-red-600' :
                            isExpiringSoon(selectedProduct.expiry_date) ? 'text-yellow-600' : 'text-green-600'
                          }`}>
                            {formatDate(selectedProduct.expiry_date)}
                          </p>
                        </div>
                        {selectedProduct.location && (
                          <div>
                            <span className="text-sm font-medium text-gray-500">Location</span>
                            <p className="text-base text-gray-900">{selectedProduct.location}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 flex space-x-3">
                <button
                  onClick={closeProductDetails}
                  className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Close
                </button>
                {user?.is_admin && (
                  <button
                    onClick={() => {
                      handleEdit(selectedProduct);
                      closeProductDetails();
                    }}
                    className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Edit Product
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Supplier Details Modal */}
      {showSupplierDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end sm:items-center justify-center z-50">
          <div 
            className="bg-white rounded-t-xl sm:rounded-lg max-w-4xl w-full max-h-[90vh] sm:max-h-screen overflow-y-auto"
            style={{
              WebkitOverflowScrolling: 'touch',
              transform: 'translateZ(0)',
            }}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Supplier Details</h2>
              <button
                onClick={closeSupplierDetails}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                style={{ touchAction: 'manipulation' }}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6">
              {supplierDetailsLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading supplier details...</p>
                </div>
              ) : selectedSupplierData ? (
                <div className="space-y-6">
                  {/* Supplier Header */}
                  <div className="text-center border-b border-gray-200 pb-6">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-2M7 21h2m3-18v18m3-18v18" />
                      </svg>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{selectedSupplierData.supplier_name}</h3>
                    <div className="text-sm text-gray-600 mb-3">
                      Supplier Code: <span className="font-mono font-medium">{selectedSupplierData.supplier_code || 'N/A'}</span>
                    </div>
                    <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                      📊 Supplier Overview
                    </div>
                  </div>

                  {/* Key Metrics Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Total Items */}
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                      <div className="flex items-center">
                        <div className="p-2 bg-blue-100 rounded-lg">
                          <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                          </svg>
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-blue-800">Total Items Supplied</p>
                          <p className="text-2xl font-bold text-blue-900">{selectedSupplierData.total_items || 0}</p>
                        </div>
                      </div>
                    </div>

                    {/* Out of Stock */}
                    <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                      <div className="flex items-center">
                        <div className="p-2 bg-red-100 rounded-lg">
                          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                          </svg>
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-red-800">Items Out of Stock</p>
                          <p className="text-2xl font-bold text-red-900">{selectedSupplierData.out_of_stock_count || 0}</p>
                        </div>
                      </div>
                    </div>

                    {/* Total Stock Value */}
                    <div className="bg-green-50 p-4 rounded-lg border border-green-200 sm:col-span-2 lg:col-span-1">
                      <div className="flex items-center">
                        <div className="p-2 bg-green-100 rounded-lg">
                          <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                          </svg>
                        </div>
                        <div className="ml-4 flex-1 min-w-0">
                          <p className="text-sm font-medium text-green-800">Total Stock Value</p>
                          <p className="text-lg sm:text-xl font-bold text-green-900">
                            {selectedSupplierData.total_stock_value_formatted}
                          </p>
                          <p className="text-xs text-green-700 mt-1">
                            {selectedSupplierData.currency === 'MULTI' ? 'Multi-currency total' : 'Quantity × Purchase Price'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Additional Information */}
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">Additional Information</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Lead Time</p>
                        <p className="text-lg font-semibold text-gray-900 mt-1">2 Days</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Return Policy</p>
                        <p className="text-lg font-semibold text-gray-900 mt-1">Accept Return or Replacement</p>
                      </div>
                    </div>
                  </div>

                  {/* Export Buttons */}
                  <div className="bg-white border-t border-gray-200 pt-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">📄 Export Reports</h4>
                    <div className="flex flex-col sm:flex-row gap-3">
                      <button
                        onClick={() => exportSupplierPDF(selectedSupplierData.supplier_name)}
                        className="flex-1 bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center space-x-2 active:scale-[0.98]"
                        style={{ touchAction: 'manipulation' }}
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span>Export to PDF</span>
                      </button>
                      <button
                        onClick={() => exportSupplierExcel(selectedSupplierData.supplier_name)}
                        className="flex-1 bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center space-x-2 active:scale-[0.98]"
                        style={{ touchAction: 'manipulation' }}
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span>Export to Excel</span>
                      </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2 text-center">
                      Reports include company logo, date, and are formatted for management use
                    </p>
                  </div>

                  {/* Close Button */}
                  <div className="flex justify-center pt-4">
                    <button
                      onClick={closeSupplierDetails}
                      className="bg-gray-100 text-gray-700 py-2 px-6 rounded-lg hover:bg-gray-200 transition-colors"
                      style={{ touchAction: 'manipulation' }}
                    >
                      Close
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-600">No supplier data available</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Selected Search Item Display */}
      {selectedSearchItem && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-medium text-blue-900">Search Result</h3>
              <button
                onClick={() => setSelectedSearchItem(null)}
                className="text-blue-600 hover:text-blue-800"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex items-start space-x-6">
              {selectedSearchItem.image_url && (
                <img 
                  src={`${BACKEND_URL}${selectedSearchItem.image_url}`} 
                  alt={selectedSearchItem.product_name}
                  className="w-24 h-24 rounded-lg object-cover"
                />
              )}
              <div className="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div><strong>Item Name:</strong> {selectedSearchItem.product_name}</div>
                <div><strong>Department:</strong> {selectedSearchItem.department}</div>
                <div><strong>Section:</strong> {selectedSearchItem.section}</div>
                <div><strong>Family:</strong> {selectedSearchItem.family}</div>
                <div><strong>Sub Family:</strong> {selectedSearchItem.sub_family}</div>
                <div><strong>Supplier:</strong> {selectedSearchItem.supplier}</div>
                <div><strong>Quantity:</strong> 
                  <span className={selectedSearchItem.quantity < 10 ? 'text-red-600 font-semibold ml-2' : 'ml-2'}>
                    {selectedSearchItem.quantity}
                  </span>
                </div>
                <div><strong>Selling Price:</strong> {formatCurrency(selectedSearchItem.selling_price)}</div>
                <div><strong>Expiry Date:</strong> 
                  <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                    selectedSearchItem.status === 'expired' ? 'bg-red-100 text-red-800' :
                    selectedSearchItem.status === 'expiring_soon' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {formatDate(selectedSearchItem.expiry_date)}
                  </span>
                </div>
                {selectedSearchItem.barcode && (
                  <div><strong>Barcode:</strong> {selectedSearchItem.barcode}</div>
                )}
                {selectedSearchItem.location && (
                  <div><strong>Location:</strong> {selectedSearchItem.location}</div>
                )}
                {selectedSearchItem.brand && (
                  <div><strong>Brand:</strong> {selectedSearchItem.brand}</div>
                )}
                {selectedSearchItem.description && (
                  <div className="md:col-span-2 lg:col-span-3">
                    <strong>Description:</strong> {selectedSearchItem.description}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Welcome Section with Geant Logo */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <img 
                    src="/icons/geant_official_logo.png" 
                    alt="Geant Hypermarket" 
                    className="w-16 h-16 object-contain"
                  />
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">Welcome to Your Dashboard</h2>
                    <p className="text-gray-600 mt-1">
                      <span className="font-semibold text-blue-600">Geant Hypermarket</span> Official Inventory Management System
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      Monitor your inventory, track expiry dates, and manage suppliers efficiently
                    </p>
                  </div>
                </div>
                {/* Beautiful Main Page Logo on the right */}
                <div className="hidden md:block">
                  <img 
                    src="/icons/geant_main_page_logo.png" 
                    alt="Geant" 
                    className="w-20 h-20 object-contain opacity-80 hover:opacity-100 transition-opacity"
                  />
                </div>
              </div>
            </div>
            
            {/* Clickable KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div 
                className="bg-white overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-lg transition-shadow kpi-card"
                onClick={() => navigateToItemsWithFilter('all')}
              >
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                        </svg>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Total Items</dt>
                        <dd className="text-lg font-medium text-gray-900">{kpi.total_products || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div 
                className="bg-white overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-lg transition-shadow kpi-card"
                onClick={() => navigateToItemsWithFilter('expiring_soon')}
              >
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Expiring Soon</dt>
                        <dd className="text-lg font-medium text-gray-900">{kpi.expiring_soon || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div 
                className="bg-white overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-lg transition-shadow kpi-card"
                onClick={() => navigateToItemsWithFilter('expired')}
              >
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-red-500 rounded-md flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Expired Items</dt>
                        <dd className="text-lg font-medium text-gray-900">{kpi.expired_products || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div 
                className="bg-white overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-lg transition-shadow kpi-card"
                onClick={() => navigateToItemsWithFilter('low_stock')}
              >
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-orange-500 rounded-md flex items-center justify-center">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                        </svg>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">Low Stock</dt>
                        <dd className="text-lg font-medium text-gray-900">{kpi.low_stock_items || 0}</dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Charts and Analytics Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Stock Level Donut Chart */}
              {donutChartData && (
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Stock Level Distribution</h3>
                  <div className="h-64">
                    <Doughnut 
                      data={{
                        labels: donutChartData.labels,
                        datasets: [{
                          data: donutChartData.data,
                          backgroundColor: donutChartData.colors,
                          borderWidth: 2,
                          borderColor: '#ffffff'
                        }]
                      }}
                      options={donutOptions}
                    />
                  </div>
                </div>
              )}

              {/* Top 5 Suppliers Visual KPI */}
              {topSuppliers.length > 0 && (
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Top 5 Suppliers by Stock Level</h3>
                  <div className="space-y-4">
                    {topSuppliers.map((supplier, index) => (
                      <div key={supplier.supplier} className="flex items-center">
                        <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                          {index + 1}
                        </div>
                        <div className="ml-4 flex-1">
                          <div className="flex justify-between items-center mb-1">
                            <div className="text-sm font-medium text-gray-900 truncate" title={supplier.supplier}>
                              {supplier.supplier.length > 25 ? `${supplier.supplier.substring(0, 25)}...` : supplier.supplier}
                            </div>
                            <div className="text-sm text-gray-500 flex-shrink-0 ml-2">
                              {supplier.total_quantity.toLocaleString()} items • {formatCurrency(supplier.total_value)}
                            </div>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full"
                              style={{ 
                                width: `${Math.min((supplier.total_quantity / topSuppliers[0].total_quantity) * 100, 100)}%` 
                              }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Reports Section */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">PDF Reports</h3>
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={downloadSupplierKPIPDF}
                  className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>Supplier KPI Summary PDF</span>
                </button>
                <button
                  onClick={downloadExpiringItemsPDF}
                  className="bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <span>Expiring Items PDF Report</span>
                </button>
                <button
                  onClick={downloadMonthlyExpiredPDF}
                  className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <span>Monthly Expired Items Report</span>
                </button>
              </div>
            </div>

            {/* Alerts Section - Toggleable */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">Alerts</h3>
                  <button
                    onClick={() => setShowAlerts(!showAlerts)}
                    className={`px-3 py-1 rounded-md text-sm ${
                      showAlerts 
                        ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {showAlerts ? 'Hide Alerts' : `Show Alerts (${alerts.length > 99 ? '99+' : alerts.length})`}
                  </button>
                </div>
                
                {showAlerts && alerts.length > 0 && (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {alerts.slice(0, 10).map((alert) => (
                      <div
                        key={alert.id}
                        className={`p-3 rounded-md ${
                          alert.alert_type === 'expired'
                            ? 'bg-red-50 border border-red-200'
                            : alert.alert_type === 'expiring_soon'
                            ? 'bg-yellow-50 border border-yellow-200'
                            : 'bg-orange-50 border border-orange-200'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <p className="text-sm text-gray-800">{alert.message}</p>
                          <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                            {formatDate(alert.created_at)}
                          </span>
                        </div>
                      </div>
                    ))}
                    {alerts.length > 10 && (
                      <div className="text-center pt-2">
                        <span className="text-sm text-gray-500">...and {alerts.length - 10} more alerts</span>
                      </div>
                    )}
                  </div>
                )}
                
                {showAlerts && alerts.length === 0 && (
                  <p className="text-sm text-gray-500">No active alerts</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Items Tab */}
        {activeTab === 'products' && (
          <div className="space-y-6">
            {/* Actions Bar */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
              {/* Enhanced Mobile-Friendly Admin Controls */}
              {user?.is_admin ? (
                <div className="w-full sm:w-auto">
                  <div className="grid grid-cols-2 sm:flex gap-2 sm:gap-3">
                    <button
                      onClick={() => setShowAddForm(true)}
                      className="bg-blue-600 text-white px-3 py-2 rounded-md hover:bg-blue-700 flex items-center justify-center space-x-1 sm:space-x-2 text-sm"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      <span className="hidden sm:inline">Add Item</span>
                      <span className="sm:hidden">Add</span>
                    </button>
                    <button
                      onClick={() => setShowImportModal(true)}
                      className="bg-green-600 text-white px-3 py-2 rounded-md hover:bg-green-700 flex items-center justify-center space-x-1 sm:space-x-2 text-sm"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6l-.9-.9" />
                      </svg>
                      <span>Import</span>
                    </button>
                    <button
                      onClick={handleExport}
                      className="bg-purple-600 text-white px-3 py-2 rounded-md hover:bg-purple-700 flex items-center justify-center space-x-1 sm:space-x-2 text-sm"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>Export</span>
                    </button>
                    <button
                      onClick={handleDownloadTemplate}
                      className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 flex items-center space-x-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707v11a2 2 0 01-2 2z" />
                      </svg>
                      <span>Template</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 w-full sm:w-auto">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-yellow-800 text-sm font-medium">
                      🔒 Admin-Only Access - Contact Administrator ({user?.username === 'imadqejji' ? 'You are admin' : 'imadqejji'}) for Inventory Changes
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* View Mode & Filters Section */}
            <div className="space-y-4">
              {/* View Mode Toggle */}
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-sm text-gray-700">View:</span>
                <button
                  onClick={() => setViewMode('table')}
                  className={`p-2 rounded-md ${
                    viewMode === 'table' 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                  title="Table View"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0V4a1 1 0 011-1h16a1 1 0 011 1v16a1 1 0 01-1 1H4a1 1 0 01-1-1z" />
                  </svg>
                </button>
                <button
                  onClick={() => setViewMode('cards')}
                  className={`p-2 rounded-md ${
                    viewMode === 'cards' 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                  title="Card View"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14-7H5a2 2 0 00-2 2v12a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2z" />
                  </svg>
                </button>
            </div>

            {/* Enhanced Mobile-Friendly Filters */}
            <div className="bg-white p-3 sm:p-4 rounded-lg shadow">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
                <div className="sm:col-span-2 lg:col-span-1">
                  <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">Search</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={filters.search}
                      onChange={(e) => setFilters({...filters, search: e.target.value})}
                      className="w-full p-2 pl-8 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Search items..."
                    />
                    <svg className="w-4 h-4 text-gray-400 absolute left-2.5 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                </div>
                <div>
                  <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">Supplier</label>
                  <select
                    value={filters.supplier}
                    onChange={(e) => setFilters({...filters, supplier: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Suppliers</option>
                    {suppliers.map((supplier) => (
                      <option key={supplier} value={supplier}>{supplier}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">Department</label>
                  <select
                    value={filters.department}
                    onChange={(e) => setFilters({...filters, department: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Departments</option>
                    {(categories.departments || []).map((dept) => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">Section</label>
                  <select
                    value={filters.section}
                    onChange={(e) => setFilters({...filters, section: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Sections</option>
                    {(categories.sections || []).map((section) => (
                      <option key={section} value={section}>{section}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1">Family</label>
                  <select
                    value={filters.family}
                    onChange={(e) => setFilters({...filters, family: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Families</option>
                    {(categories.families || []).map((family) => (
                      <option key={family} value={family}>{family}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Items Display */}
            {viewMode === 'cards' ? (
              /* Card View */
              <div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                {loading ? (
                  <div className="col-span-full text-center py-8">Loading...</div>
                ) : products.length === 0 ? (
                  <div className="col-span-full text-center py-8 text-gray-500">No items found</div>
                ) : (
                  products.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage).map((product) => (
                    <div 
                      key={product.id} 
                      className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md active:scale-[0.98] transition-all duration-200 cursor-pointer"
                      onClick={() => openProductDetails(product)}
                      style={{
                        minHeight: '280px', // Consistent card height for alignment
                        WebkitTapHighlightColor: 'rgba(59, 130, 246, 0.1)', // iOS touch highlight
                        touchAction: 'manipulation', // Prevent iOS double-tap zoom
                      }}
                    >
                      {/* Product Image - Fixed aspect ratio for consistency */}
                      <div className="h-40 bg-gray-50 flex items-center justify-center relative overflow-hidden">
                        {product.image_url ? (
                          <img 
                            src={`${BACKEND_URL}${product.image_url}`} 
                            alt={product.product_name}
                            className="w-full h-full object-cover"
                            style={{ imageRendering: 'auto' }} // iOS image optimization
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                        ) : null}
                        <div className={`${product.image_url ? 'hidden' : 'flex'} text-gray-400 text-center flex-col items-center justify-center w-full h-full`}>
                          <svg className="w-10 h-10 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2z" />
                          </svg>
                          <p className="text-xs font-medium text-gray-500">No Image</p>
                        </div>
                        
                        {/* Stock Status Indicator - Enhanced visibility */}
                        <div className="absolute top-3 right-3">
                          <div className={`w-5 h-5 rounded-full border-2 border-white shadow ${
                            product.quantity <= 0 ? 'bg-red-500' : 'bg-green-500'
                          }`} title={product.quantity <= 0 ? 'Out of Stock' : 'Available'}>
                          </div>
                        </div>
                      </div>
                      
                      {/* Product Information - Optimized padding for mobile */}
                      <div className="p-3 sm:p-4 flex-1 min-h-0">
                        {/* Product Name - Better line clamping */}
                        <h3 className="font-semibold text-gray-900 mb-2 text-sm sm:text-base leading-tight" 
                            style={{
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden'
                            }}>
                          {product.product_name}
                        </h3>
                        
                        {/* Item Code / Barcode - More compact */}
                        <div className="text-xs sm:text-sm text-gray-600 mb-2">
                          <span className="font-medium text-gray-800">Code:</span> {product.item_number || product.barcode || 'N/A'}
                        </div>
                        
                        {/* Stock Status - Better mobile layout */}
                        <div className="flex items-center justify-between mt-auto">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            product.quantity <= 0 
                              ? 'bg-red-100 text-red-800 border border-red-200' 
                              : 'bg-green-100 text-green-800 border border-green-200'
                          }`}>
                            {product.quantity <= 0 ? 'Out of Stock' : 
                             product.quantity === 1 ? '1 Available' : 
                             `${product.quantity} Available`}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
              
              {/* Pagination Controls for Card View */}
              {products.length > itemsPerPage && (
                <div className="mt-6 flex flex-col sm:flex-row items-center justify-between bg-white px-4 py-3 border-t border-gray-200 rounded-lg">
                  <div className="flex items-center text-sm text-gray-700 mb-2 sm:mb-0">
                    <span>
                      Showing {Math.min((currentPage - 1) * itemsPerPage + 1, products.length)} to{' '}
                      {Math.min(currentPage * itemsPerPage, products.length)} of {products.length} items
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <div className="flex space-x-1">
                      {Array.from({ length: Math.ceil(products.length / itemsPerPage) }, (_, i) => i + 1)
                        .filter(page => {
                          const totalPages = Math.ceil(products.length / itemsPerPage);
                          if (totalPages <= 7) return true;
                          if (page === 1 || page === totalPages) return true;
                          if (page >= currentPage - 1 && page <= currentPage + 1) return true;
                          return false;
                        })
                        .map((page, index, array) => (
                          <React.Fragment key={page}>
                            {index > 0 && array[index - 1] !== page - 1 && (
                              <span className="px-2 py-1 text-sm text-gray-500">...</span>
                            )}
                            <button
                              onClick={() => setCurrentPage(page)}
                              className={`px-3 py-1 text-sm rounded ${
                                currentPage === page
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                              }`}
                            >
                              {page}
                            </button>
                          </React.Fragment>
                        ))}
                    </div>
                    <button
                      onClick={() => setCurrentPage(Math.min(Math.ceil(products.length / itemsPerPage), currentPage + 1))}
                      disabled={currentPage >= Math.ceil(products.length / itemsPerPage)}
                      className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
              </div>
            ) : (
              /* Table View */
              <div className="bg-white shadow rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Section</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Family</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Supplier</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expiry Date</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price (YER)</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {loading ? (
                        <tr>
                          <td colSpan="9" className="px-6 py-4 text-center">Loading...</td>
                        </tr>
                      ) : products.length === 0 ? (
                        <tr>
                          <td colSpan="9" className="px-6 py-4 text-center text-gray-500">No items found</td>
                        </tr>
                      ) : (
                        products.map((product) => (
                          <tr key={product.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center space-x-3">
                                {product.image_url && (
                                  <img 
                                    src={`${BACKEND_URL}${product.image_url}`} 
                                    alt={product.product_name}
                                    className="w-12 h-12 rounded-lg object-cover"
                                  />
                                )}
                                <div>
                                  <div className="text-sm font-medium text-gray-900">{product.product_name}</div>
                                  {product.barcode && (
                                    <div className="text-sm text-gray-500">Barcode: {product.barcode}</div>
                                  )}
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.department}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.section}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.family}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.supplier}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                isExpired(product.expiry_date)
                                  ? 'bg-red-100 text-red-800'
                                  : isExpiringSoon(product.expiry_date)
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-green-100 text-green-800'
                              }`}>
                                {formatDate(product.expiry_date)}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`text-sm ${
                                product.quantity < 10 ? 'text-red-600 font-semibold' : 'text-gray-900'
                              }`}>
                                {product.quantity}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatCurrency(product.selling_price)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                              {/* Role-based access: Only admins can edit, users can only add new */}
                              {user?.is_admin && (
                                <>
                                  <button
                                    onClick={() => handleEdit(product)}
                                    className="text-indigo-600 hover:text-indigo-900"
                                  >
                                    Edit
                                  </button>
                                  <button
                                    onClick={() => handleDelete(product.id)}
                                    className="text-red-600 hover:text-red-900"
                                  >
                                    Delete
                                  </button>
                                </>
                              )}
                              {!user?.is_admin && (
                                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                  👀 View Only (Contact Admin to Edit)
                                </span>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            </div>
          </div>
        )}

        {/* Barcode Scanner Tab */}
        {activeTab === 'scanner' && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">📱 Enhanced Mobile Barcode Scanner</h2>
              <p className="text-gray-600 mb-6">
                Supports EAN-13, UPC-A, Code128, QR codes and more
              </p>
              
              {/* Error Display */}
              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-red-800 text-sm font-medium">{error}</span>
                  </div>
                </div>
              )}
              
              {/* Success Display */}
              {success && (
                <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-green-800 text-sm font-medium">{success}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Enhanced Scanner Interface */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Enter barcode manually or use camera scanner
                </h3>
                
                {/* Manual Input */}
                <form onSubmit={handleManualBarcodeSubmit} className="mb-6">
                  <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                    <input
                      type="text"
                      value={manualBarcode}
                      onChange={(e) => setManualBarcode(e.target.value)}
                      placeholder="Enter or scan barcode"
                      className="flex-1 p-3 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <button
                      type="submit"
                      disabled={!manualBarcode.trim()}
                      className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors font-medium"
                    >
                      🔍 Search
                    </button>
                  </div>
                </form>
                
                {/* Enhanced Camera Scanner */}
                <div className="mb-6">
                  {!isZxingScanning && !scannerActive ? (
                    <div className="space-y-3">
                      <button
                        onClick={startEnhancedBarcodeScanner}
                        className="bg-green-600 text-white px-8 py-4 rounded-lg hover:bg-green-700 transition-colors font-medium text-lg flex items-center justify-center mx-auto"
                      >
                        <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        📷 Start Enhanced Camera Scanner
                      </button>
                      <p className="text-sm text-gray-500">
                        Advanced multi-format barcode detection with mobile optimization
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <video
                          id="video-scanner"
                          ref={videoRef}
                          className="w-full max-w-sm mx-auto rounded-lg border-2 border-blue-300"
                          autoPlay
                          playsInline
                        />
                      </div>
                      <div className="flex space-x-3 justify-center">
                        <button
                          onClick={isZxingScanning ? stopEnhancedBarcodeScanner : stopBarcodeScanner}
                          className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors font-medium"
                        >
                          ⏹️ Stop Scanner
                        </button>
                        <button
                          onClick={async () => {
                            if (isZxingScanning) {
                              stopEnhancedBarcodeScanner();
                              setTimeout(() => startEnhancedBarcodeScanner(), 500);
                            } else {
                              stopBarcodeScanner();
                              setTimeout(() => startBarcodeScanner(), 500);
                            }
                          }}
                          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                        >
                          🔄 Restart Scanner
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Enhanced Scanner Options */}
                {!isZxingScanning && !scannerActive && (
                  <div className="space-y-3">
                    <button
                      onClick={startEnhancedBarcodeScanner}
                      className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center mx-auto"
                    >
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      🔄 Retry Scanner
                    </button>
                    <button
                      onClick={startBarcodeScanner}
                      className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors font-medium flex items-center justify-center mx-auto"
                    >
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      </svg>
                      📷 Fallback Scanner
                    </button>
                  </div>
                )}
              </div>
              
              {/* Original Scanner Container */}
              {scannerActive && (
                <div className="mt-6">
                  <div id="barcode-reader" ref={scannerRef} className="max-w-sm mx-auto"></div>
                </div>
              )}
            </div>

            {/* Mobile-Optimized Product Display */}
            {scannedProduct && (
              <div className="flex justify-center">
                <MobileProductCard product={scannedProduct} showStockValue={true} />
              </div>
            )}
          </div>
        )}

        {/* Supplier Returns Tab */}
        {activeTab === 'returns' && (
          <div className="space-y-6">
            {/* Header with Geant Logo */}
            <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-6 border border-orange-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <img 
                    src="/icons/geant_official_logo.png" 
                    alt="Geant Hypermarket" 
                    className="w-16 h-16 object-contain"
                  />
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">Supplier Return Form</h2>
                    <p className="text-gray-600 mt-1">
                      <span className="font-semibold text-orange-600">Geant Hypermarket</span> - Expired Items Return
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      Manually enter expired items for supplier returns with automatic value calculation
                    </p>
                  </div>
                </div>
                <div className="hidden md:block">
                  <img 
                    src="/icons/geant_main_page_logo.png" 
                    alt="Geant" 
                    className="w-20 h-20 object-contain opacity-80 hover:opacity-100 transition-opacity"
                  />
                </div>
              </div>
            </div>

            {/* Return Form */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Add Return Item</h3>
              
              {/* DEBUG MARKER - ENHANCED VERSION LOADED */}
              <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                🎉 <strong>ENHANCED RETURN FORM v2.0 LOADED!</strong> - All 9 fields with multi-currency support
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Supplier Code *
                  </label>
                  <input
                    type="text"
                    name="supplierCode"
                    value={returnForm.supplierCode}
                    onChange={handleReturnFormChange}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter supplier code"
                    readOnly={!!returnForm.supplierCode}  // Read-only if auto-populated
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Supplier Name *
                  </label>
                  <input
                    type="text"
                    name="supplierName"
                    value={returnForm.supplierName}
                    onChange={handleReturnFormChange}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter supplier name"
                    readOnly={!!returnForm.supplierName}  // Read-only if auto-populated
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Item Number
                  </label>
                  <input
                    type="text"
                    name="itemNumber"
                    value={returnForm.itemNumber}
                    onChange={handleReturnFormChange}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter item number"
                    readOnly={!!returnForm.itemNumber}  // Read-only if auto-populated
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Barcode
                  </label>
                  <input
                    type="text"
                    name="barcode"
                    value={returnForm.barcode}
                    onChange={handleReturnFormChange}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter barcode"
                    readOnly={!!returnForm.barcode}  // Read-only if auto-populated
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 mb-6">
                {/* Item Search and Name - Full Width */}
                <div className="relative">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Item Name *
                  </label>
                  <input
                    type="text"
                    value={itemSearchQuery}
                    onChange={(e) => {
                      setItemSearchQuery(e.target.value);
                      setShowItemSearchResults(true);
                      
                      // Also update the form if manually typing
                      setReturnForm({
                        ...returnForm,
                        itemName: e.target.value
                      });
                    }}
                    onFocus={() => setShowItemSearchResults(true)}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Search for an item or type manually..."
                  />
                  
                  {/* Enhanced Search Results Dropdown with Images */}
                  {showItemSearchResults && itemSearchResults.length > 0 && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-80 overflow-y-auto">
                      {itemSearchResults.map((item) => (
                        <div
                          key={item.id}
                          className="p-4 hover:bg-orange-50 cursor-pointer border-b border-gray-100 last:border-b-0 transition-colors"
                          onClick={() => handleItemSelect(item)}
                        >
                          <div className="flex items-start space-x-3">
                            {/* Product Image */}
                            <div className="flex-shrink-0">
                              {item.image_url ? (
                                <img
                                  src={item.image_url}
                                  alt={item.product_name}
                                  className="w-12 h-12 object-cover rounded-md border border-gray-200"
                                  onError={(e) => {
                                    e.target.style.display = 'none';
                                    e.target.nextSibling.style.display = 'flex';
                                  }}
                                />
                              ) : null}
                              <div className={`w-12 h-12 bg-gray-100 rounded-md border border-gray-200 flex items-center justify-center ${item.image_url ? 'hidden' : 'flex'}`}>
                                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                              </div>
                            </div>
                            
                            {/* Item Details */}
                            <div className="flex-1 min-w-0">
                              <div className="font-semibold text-gray-900 truncate">{item.product_name}</div>
                              
                              {/* Primary Details Row */}
                              <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600 mt-1">
                                <span className="font-medium text-blue-600">{item.supplier}</span>
                                <span className="text-gray-400">•</span>
                                <span className="font-medium text-green-600">
                                  {item.purchase_price?.toFixed(2) || 'N/A'} {item.purchase_currency || 'YER'}
                                </span>
                                <span className="text-gray-400">•</span>
                                <span className={`font-medium ${item.quantity > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  Qty: {item.quantity}
                                </span>
                              </div>
                              
                              {/* Secondary Details Row */}
                              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 mt-1">
                                {item.barcode && (
                                  <>
                                    <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">{item.barcode}</span>
                                    <span className="text-gray-400">•</span>
                                  </>
                                )}
                                {item.item_number && (
                                  <>
                                    <span className="font-medium">#{item.item_number}</span>
                                    <span className="text-gray-400">•</span>
                                  </>
                                )}
                                <span className="text-orange-600">
                                  {item.department} → {item.section} → {item.family}
                                </span>
                              </div>
                              
                              {/* Status Indicators */}
                              <div className="flex items-center gap-2 mt-2">
                                {item.quantity === 0 && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                    Out of Stock
                                  </span>
                                )}
                                {item.quantity > 0 && item.quantity <= 5 && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                    Low Stock
                                  </span>
                                )}
                                {item.expiry_date && new Date(item.expiry_date) < new Date() && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                    Expired
                                  </span>
                                )}
                                {item.expiry_date && new Date(item.expiry_date) > new Date() && new Date(item.expiry_date) < new Date(Date.now() + 30*24*60*60*1000) && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                                    Expiring Soon
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* No Results Message */}
                  {showItemSearchResults && itemSearchResults.length === 0 && itemSearchQuery.trim() && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-3">
                      <div className="text-gray-500 text-sm">
                        No items found for "{itemSearchQuery}". You can still type manually.
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Qty Returned *
                  </label>
                  <input
                    type="number"
                    name="quantity"
                    value={returnForm.quantity}
                    onChange={handleReturnFormChange}
                    min="0"
                    step="1"
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter quantity"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Purchase Price *
                  </label>
                  <input
                    type="number"
                    name="unitPrice"
                    value={returnForm.unitPrice}
                    onChange={handleReturnFormChange}
                    min="0"
                    step="0.01"
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    placeholder="Enter purchase price"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Currency *
                  </label>
                  <select
                    name="currency"
                    value={returnForm.currency}
                    onChange={handleReturnFormChange}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  >
                    <option value="YER">YER (Yemeni Rial)</option>
                    <option value="SAR">SAR (Saudi Riyal)</option>
                    <option value="EUR">EUR (Euro)</option>
                    <option value="USD">USD (US Dollar)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reason for Return *
                  </label>
                  <select
                    name="reasonForReturn"
                    value={returnForm.reasonForReturn}
                    onChange={handleReturnFormChange}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  >
                    <option value="Expired">Expired</option>
                    <option value="Damaged">Damaged</option>
                    <option value="Wrong Item">Wrong Item</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Expiry Date
                  </label>
                  <input
                    type="date"
                    name="expiryDate"
                    value={returnForm.expiryDate}
                    onChange={handleReturnFormChange}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  />
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Total Value Returned
                </label>
                <input
                  type="text"
                  value={`${returnForm.returnValue.toFixed(2)} ${returnForm.currency}`}
                  readOnly
                  className="w-full p-2 border border-gray-200 bg-gray-50 rounded-md text-gray-700 font-medium text-lg"
                  placeholder="Auto-calculated"
                />
                <p className="text-xs text-gray-500 mt-1">Auto-calculated: Qty × Purchase Price with exact currency</p>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Attach Image (JPG, PNG, PDF)
                </label>
                <input
                  type="file"
                  accept=".jpg,.jpeg,.png,.pdf"
                  onChange={(e) => {
                    const file = e.target.files[0];
                    if (file) {
                      if (file.size > 5 * 1024 * 1024) { // 5MB limit
                        setError('File size must be less than 5MB');
                        e.target.value = '';
                        return;
                      }
                      setReturnForm({...returnForm, attachedImage: file});
                    }
                  }}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                />
                <p className="text-xs text-gray-500 mt-1">Optional: Attach image evidence (Max 5MB)</p>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={clearReturnForm}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 transition-colors"
                >
                  Clear All
                </button>
                <button
                  type="button"
                  onClick={addReturnItem}
                  className="bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 transition-colors flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span>{editingReturnIndex >= 0 ? 'Update Item' : 'Add Item'}</span>
                </button>
              </div>
            </div>

            {/* Return Items List */}
            {returnItems.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    Return Items ({returnItems.length})
                  </h3>
                  <div className="space-x-3">
                    <button
                      onClick={exportReturnFormPDF}
                      className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors flex items-center space-x-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>Export PDF</span>
                    </button>
                    <button
                      onClick={exportReturnFormExcel}
                      className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors flex items-center space-x-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>Export Excel</span>
                    </button>
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Supplier Code
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Supplier Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Item Number
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Barcode
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Item Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Quantity
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Purchase Price
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Return Value
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {returnItems.map((item, index) => (
                        <tr key={item.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {item.supplierCode}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {item.supplierName}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.itemNumber || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {item.barcode || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {item.itemName}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {item.quantity}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {item.unitPrice.toFixed(2)} {item.currency || 'YER'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                            {item.returnValue.toFixed(2)} {item.currency || 'YER'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => editReturnItem(index)}
                                className="text-blue-600 hover:text-blue-900 transition-colors"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => deleteReturnItem(index)}
                                className="text-red-600 hover:text-red-900 transition-colors"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-gray-50">
                      <tr>
                        <td colSpan="7" className="px-6 py-4 text-right text-sm font-medium text-gray-900">
                          Total Return Value:
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-600">
                          {(() => {
                            // Calculate totals by currency
                            const totals = returnItems.reduce((acc, item) => {
                              const currency = item.currency || 'YER';
                              acc[currency] = (acc[currency] || 0) + item.returnValue;
                              return acc;
                            }, {});
                            
                            // Display all currency totals
                            return Object.entries(totals)
                              .map(([currency, total]) => `${total.toFixed(2)} ${currency}`)
                              .join(' + ');
                          })()}
                        </td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            )}

            {/* Future Excel Integration Notice */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <svg className="w-5 h-5 text-blue-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h4 className="text-sm font-medium text-blue-800">Future Enhancement</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    Excel import/export functionality will be added soon to automatically populate return items from spreadsheet data.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Admin Panel Tab */}
        {activeTab === 'admin' && user?.is_admin && (
          <div className="space-y-6">
            {/* Header with Geant Logo */}
            <div className="bg-gradient-to-r from-red-50 to-pink-50 rounded-lg p-6 border border-red-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <img 
                    src="/icons/geant_official_logo.png" 
                    alt="Geant Hypermarket" 
                    className="w-16 h-16 object-contain"
                  />
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">User Management Panel</h2>
                    <p className="text-gray-600 mt-1">
                      <span className="font-semibold text-red-600">Administrator Access</span> - Manage User Approvals
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      Review and approve user registrations for system access
                    </p>
                  </div>
                </div>
                <div className="hidden md:block">
                  <img 
                    src="/icons/geant_main_page_logo.png" 
                    alt="Geant" 
                    className="w-20 h-20 object-contain opacity-80 hover:opacity-100 transition-opacity"
                  />
                </div>
              </div>
            </div>

            {/* Pending Users */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Pending Approvals ({pendingUsers.length})
                </h3>
                <button
                  onClick={fetchPendingUsers}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>Refresh</span>
                </button>
              </div>
              
              {pendingUsers.length === 0 ? (
                <div className="text-center py-8">
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <p className="text-gray-500">No pending approvals</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Username
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Full Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Email
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Registration Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {pendingUsers.map((pendingUser) => (
                        <tr key={pendingUser.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {pendingUser.username}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {pendingUser.full_name || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {pendingUser.email || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(pendingUser.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => approveUser(pendingUser.id, 'approved')}
                                className="bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700 transition-colors flex items-center space-x-1"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                <span>Approve</span>
                              </button>
                              <button
                                onClick={() => approveUser(pendingUser.id, 'rejected')}
                                className="bg-red-600 text-white px-3 py-1 rounded-md hover:bg-red-700 transition-colors flex items-center space-x-1"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                                <span>Reject</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* All Users Management */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  All Users ({allUsers.length})
                </h3>
                <button
                  onClick={fetchAllUsers}
                  className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>Refresh</span>
                </button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Username
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Full Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Role
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {allUsers.map((userItem) => (
                      <tr key={userItem.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {userItem.username}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {userItem.full_name || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            userItem.approval_status === 'approved' 
                              ? 'bg-green-100 text-green-800'
                              : userItem.approval_status === 'rejected'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {userItem.approval_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            userItem.is_admin ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {userItem.is_admin ? 'Admin' : 'User'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            {!userItem.is_admin && userItem.approval_status === 'approved' && (
                              <button
                                onClick={() => makeUserAdmin(userItem.id)}
                                className="bg-purple-600 text-white px-3 py-1 rounded-md hover:bg-purple-700 transition-colors text-xs"
                              >
                                Make Admin
                              </button>
                            )}
                            {userItem.approval_status === 'pending' && (
                              <>
                                <button
                                  onClick={() => approveUser(userItem.id, 'approved')}
                                  className="bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700 transition-colors text-xs"
                                >
                                  Approve
                                </button>
                                <button
                                  onClick={() => approveUser(userItem.id, 'rejected')}
                                  className="bg-red-600 text-white px-3 py-1 rounded-md hover:bg-red-700 transition-colors text-xs"
                                >
                                  Reject
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Admin Instructions */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <svg className="w-5 h-5 text-yellow-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h4 className="text-sm font-medium text-yellow-800">Admin Instructions</h4>
                  <div className="text-sm text-yellow-700 mt-1">
                    <p><strong>Approve Users:</strong> Review pending registrations and approve legitimate users.</p>
                    <p><strong>Grant Admin:</strong> Make trusted users administrators to help manage the system.</p>
                    <p><strong>Security:</strong> Only approve users who should have access to Geant inventory data.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        {/* Out of Stock Tab */}
        {activeTab === 'out-of-stock' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
                <h2 className="text-2xl font-bold text-red-600 mb-4 md:mb-0">
                  🚨 Out of Stock Products
                </h2>
                <button
                  onClick={exportOutOfStock}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                >
                  📥 Export Out of Stock
                </button>
              </div>

              {/* Filters */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Section</label>
                  <select
                    value={outOfStockFilters.section}
                    onChange={(e) => setOutOfStockFilters({...outOfStockFilters, section: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  >
                    <option value="">All Sections</option>
                    {categories.sections?.map(section => (
                      <option key={section} value={section}>{section}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Supplier</label>
                  <select
                    value={outOfStockFilters.supplier}
                    onChange={(e) => setOutOfStockFilters({...outOfStockFilters, supplier: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  >
                    <option value="">All Suppliers</option>
                    {suppliers.map(supplier => (
                      <option key={supplier} value={supplier}>{supplier}</option>
                    ))}
                  </select>
                </div>
              </div>

              <button
                onClick={fetchOutOfStockProducts}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors mb-6"
              >
                🔍 Apply Filters
              </button>

              {/* Out of Stock Products Grid */}
              {loading ? (
                <div className="text-center py-8">Loading...</div>
              ) : outOfStockProducts.length === 0 ? (
                <div className="text-center py-8 text-green-600">
                  🎉 No out-of-stock products found! All items are in stock.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {outOfStockProducts.map(product => (
                    <EnhancedProductCard key={product.id} product={product} showStockValue={true} />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Suppliers Dashboard Tab */}
        {activeTab === 'suppliers' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">📊 Enhanced Supplier Dashboard</h2>

              {/* Section Filter */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Section</label>
                <div className="flex gap-4">
                  <select
                    value={supplierDashboardSection}
                    onChange={(e) => setSupplierDashboardSection(e.target.value)}
                    className="flex-1 p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">All Sections</option>
                    {categories.sections?.map(section => (
                      <option key={section} value={section}>{section}</option>
                    ))}
                  </select>
                  <button
                    onClick={fetchSupplierDashboard}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    🔍 Apply Filter
                  </button>
                </div>
              </div>

              {loading ? (
                <div className="text-center py-8">Loading dashboard...</div>
              ) : supplierDashboardData ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* High Stock Value Suppliers */}
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="text-lg font-bold text-green-800 mb-4">💰 High Stock Value Suppliers</h3>
                    <div className="space-y-3">
                      {supplierDashboardData.high_stock_value_suppliers?.map((supplier, index) => (
                        <div 
                          key={supplier.supplier} 
                          className="bg-white p-3 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer active:scale-[0.98]"
                          onClick={() => openSupplierDetails(supplier.supplier)}
                          style={{
                            WebkitTapHighlightColor: 'rgba(34, 197, 94, 0.1)',
                            touchAction: 'manipulation'
                          }}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <span className="font-medium text-gray-900">#{index + 1} {supplier.supplier}</span>
                              <div className="text-xs text-gray-500 mt-1">
                                Code: {supplier.supplier_code || 'N/A'}
                              </div>
                            </div>
                            <span className="font-bold text-green-600 text-right">
                              {supplier.total_stock_value_formatted || 
                               formatCurrency(supplier.total_stock_value, supplier.currency || 'YER')}
                            </span>
                          </div>
                          <div className="text-sm text-gray-600 mt-2">
                            {supplier.total_products} products • {supplier.total_quantity} total quantity
                          </div>
                          <div className="flex items-center justify-end mt-2">
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Zero Stock Suppliers */}
                  <div className="bg-red-50 p-4 rounded-lg">
                    <h3 className="text-lg font-bold text-red-800 mb-4">🚨 Zero Stock Suppliers</h3>
                    <div className="space-y-3">
                      {supplierDashboardData.zero_stock_suppliers?.map(supplier => (
                        <div 
                          key={supplier.supplier} 
                          className="bg-white p-3 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer active:scale-[0.98]"
                          onClick={() => openSupplierDetails(supplier.supplier)}
                          style={{
                            WebkitTapHighlightColor: 'rgba(239, 68, 68, 0.1)',
                            touchAction: 'manipulation'
                          }}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <span className="font-medium text-gray-900">{supplier.supplier}</span>
                              <div className="text-xs text-gray-500 mt-1">
                                Code: {supplier.supplier_code || 'N/A'}
                              </div>
                            </div>
                            <span className="font-bold text-red-600">{supplier.zero_stock_count} items</span>
                          </div>
                          <div className="text-sm text-gray-600 mt-2 mb-2">
                            Out of stock: {supplier.zero_stock_items.join(', ')}
                          </div>
                          <div className="flex items-center justify-end">
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  Click "Apply Filter" to load supplier dashboard data
                </div>
              )}
            </div>
          </div>
        )}

      </main>

      {/* Add/Edit Item Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 modal-overlay">
          <div className="relative top-10 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white modal-content">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingProduct ? 'Edit Item' : 'Add New Item'}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-4 form-container">
                {/* Image Upload - Enhanced with watermark protection */}
                <div className="file-input-wrapper">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    📷 Item Image
                  </label>
                  <div className="file-upload-area border-2 border-dashed border-gray-300 rounded-lg p-4">
                    {imagePreview ? (
                      <div className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4">
                        {/* Enhanced Image Preview with proper aspect ratio */}
                        <div className="flex-shrink-0">
                          <div className="w-32 h-32 bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
                            <img 
                              src={imagePreview} 
                              alt="Preview" 
                              className="w-full h-full object-contain"
                              style={{ maxHeight: '100%', maxWidth: '100%' }}
                            />
                          </div>
                          <p className="text-xs text-gray-500 mt-2 text-center">Original Preview</p>
                        </div>
                        <div className="flex-1 text-center sm:text-left">
                          <p className="text-sm font-medium text-green-600 mb-2">✅ Ready for AI Enhancement</p>
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                            <p className="text-xs font-medium text-blue-800 mb-2">🎯 Automatic Processing Features:</p>
                            <ul className="text-xs text-blue-700 space-y-1">
                              <li>• 📱 Auto-rotate based on device orientation</li>
                              <li>• 🎯 Smart object detection & centering</li>
                              <li>• 🖼️ Background blur for product focus</li>
                              <li>• ✨ Professional lighting enhancement</li>
                              <li>• 📐 Standardized 800×800 format</li>
                            </ul>
                          </div>
                          <input
                            type="file"
                            accept="image/*,.pdf"
                            onChange={handleImageChange}
                            className="upload-button block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 file:cursor-pointer file:transition-colors file:duration-200"
                          />
                          <p className="text-xs text-gray-400 mt-1">
                            PNG, JPG, PDF up to 10MB | AI-enhanced processing
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-6">
                        <div className="bg-gradient-to-br from-blue-50 to-green-50 rounded-lg p-4 mb-4">
                          <svg className="w-12 h-12 text-blue-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <p className="text-blue-700 font-medium text-sm mb-2">🤖 AI-Powered Image Processing</p>
                          <p className="text-blue-600 text-xs">Your photos will be automatically enhanced for perfect inventory display</p>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 mb-4">
                          <div className="flex items-center">
                            <span className="text-green-500 mr-1">✨</span>
                            <span>Auto-correct rotation</span>
                          </div>
                          <div className="flex items-center">
                            <span className="text-green-500 mr-1">🎯</span>
                            <span>Smart centering</span>
                          </div>
                          <div className="flex items-center">
                            <span className="text-green-500 mr-1">🖼️</span>
                            <span>Background enhancement</span>
                          </div>
                          <div className="flex items-center">
                            <span className="text-green-500 mr-1">📐</span>
                            <span>Standard sizing</span>
                          </div>
                        </div>
                        
                        <input
                          type="file"
                          accept="image/*,.pdf"
                          onChange={handleImageChange}
                          className="upload-button block w-full max-w-sm mx-auto text-sm text-gray-500 file:mr-4 file:py-3 file:px-6 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gradient-to-r file:from-blue-500 file:to-green-500 file:text-white hover:file:from-blue-600 hover:file:to-green-600 file:cursor-pointer file:transition-all file:duration-200"
                        />
                        <p className="text-xs text-gray-400 mt-2">
                          📸 PNG, JPG, PDF up to 10MB | Professional AI enhancement included
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Item Name*</label>
                    <input
                      type="text"
                      required
                      value={formData.product_name}
                      onChange={(e) => setFormData({...formData, product_name: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Item Number</label>
                    <input
                      type="text"
                      value={formData.item_number}
                      onChange={(e) => setFormData({...formData, item_number: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="Enter item number"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Department*</label>
                    <input
                      type="text"
                      required
                      value={formData.department}
                      onChange={(e) => setFormData({...formData, department: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Section*</label>
                    <input
                      type="text"
                      required
                      value={formData.section}
                      onChange={(e) => setFormData({...formData, section: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Family*</label>
                    <input
                      type="text"
                      required
                      value={formData.family}
                      onChange={(e) => setFormData({...formData, family: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Sub Family*</label>
                    <input
                      type="text"
                      required
                      value={formData.sub_family}
                      onChange={(e) => setFormData({...formData, sub_family: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Supplier Code</label>
                    <input
                      type="text"
                      value={formData.supplier_code}
                      onChange={(e) => setFormData({...formData, supplier_code: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="Enter supplier code"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Supplier*</label>
                    <input
                      type="text"
                      required
                      value={formData.supplier}
                      onChange={(e) => setFormData({...formData, supplier: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date*</label>
                    <input
                      type="date"
                      required
                      value={formData.expiry_date}
                      onChange={(e) => setFormData({...formData, expiry_date: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Quantity*</label>
                    <input
                      type="number"
                      required
                      min="0"
                      value={formData.quantity}
                      onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Barcode</label>
                    <input
                      type="text"
                      value={formData.barcode}
                      onChange={(e) => setFormData({...formData, barcode: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md scanner-input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Selling Price (YER)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.selling_price}
                      onChange={(e) => setFormData({...formData, selling_price: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  {/* Purchase Price and Currency */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Purchase Price
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.purchase_price}
                        onChange={(e) => setFormData({...formData, purchase_price: e.target.value})}
                        className="w-full p-2 border border-gray-300 rounded-md"
                        placeholder="0.00"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Purchase Currency {!user?.is_admin && <span className="text-red-500 text-xs">(Admin Only)</span>}
                      </label>
                      <select
                        value={formData.purchase_currency}
                        onChange={(e) => setFormData({...formData, purchase_currency: e.target.value})}
                        disabled={!user?.is_admin}
                        className={`w-full p-2 border border-gray-300 rounded-md ${
                          !user?.is_admin ? 'bg-gray-100 cursor-not-allowed' : ''
                        }`}
                      >
                        <option value="YER">YER (Yemeni Rial)</option>
                        <option value="SAR">SAR (Saudi Riyal)</option>
                        <option value="USD">USD (US Dollar)</option>
                        <option value="EUR">EUR (Euro)</option>
                        <option value="AED">AED (UAE Dirham)</option>
                        <option value="OMR">OMR (Omani Rial)</option>
                        <option value="KWD">KWD (Kuwaiti Dinar)</option>
                        <option value="QAR">QAR (Qatari Riyal)</option>
                        <option value="BHD">BHD (Bahraini Dinar)</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Arabic Description <span className="text-gray-500">العربية</span>
                    </label>
                    <input
                      type="text"
                      value={formData.arabic_description}
                      onChange={(e) => setFormData({...formData, arabic_description: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="أدخل الوصف بالعربية"
                      dir="rtl"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                    <input
                      type="text"
                      value={formData.location}
                      onChange={(e) => setFormData({...formData, location: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
                    <input
                      type="text"
                      value={formData.brand}
                      onChange={(e) => setFormData({...formData, brand: e.target.value})}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    rows="3"
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={resetForm}
                    className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
                  >
                    {loading && <div className="spinner"></div>}
                    <span>{loading ? 'Saving...' : (editingProduct ? 'Update' : 'Add')} Item</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 modal-overlay">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-lg shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Import from Excel</h3>
              <div className="space-y-4">
                
                {/* Import Mode Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Import Mode</label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="add_only"
                        checked={importMode === 'add_only'}
                        onChange={(e) => setImportMode(e.target.value)}
                        className="mr-2"
                      />
                      <span className="text-sm">Add new items only (skip existing)</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="update_existing"
                        checked={importMode === 'update_existing'}
                        onChange={(e) => setImportMode(e.target.value)}
                        className="mr-2"
                      />
                      <span className="text-sm">Update existing items only</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="add_and_update"
                        checked={importMode === 'add_and_update'}
                        onChange={(e) => setImportMode(e.target.value)}
                        className="mr-2"
                      />
                      <span className="text-sm">Add new + Update existing (Recommended)</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Excel File (.xlsx, .xlsm, .xls)
                  </label>
                  <input
                    type="file"
                    accept=".xlsx,.xlsm,.xls"
                    onChange={handleImport}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                </div>
                
                <div className="text-sm text-gray-600">
                  <p className="font-medium mb-2">Expected columns (exact match):</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li><strong>item Name</strong> (required)</li>
                    <li><strong>department</strong> (required)</li>
                    <li><strong>section </strong> (required - note the space)</li>
                    <li><strong>Family </strong> (required - note the space)</li>
                    <li><strong>Sub Family</strong> (required)</li>
                    <li><strong>Supplier</strong> (required)</li>
                    <li><strong>Expiry Date </strong> (required - note the space)</li>
                    <li><strong>Quantity</strong> (required)</li>
                    <li>Barcode, Selling Price, Description, Location, Brand (optional)</li>
                  </ul>
                </div>
                
                <div className="bg-blue-50 border border-blue-200 rounded p-3">
                  <p className="text-sm text-blue-800">
                    <strong>Perfect!</strong> Your Excel format matches exactly. Import will work flawlessly.
                  </p>
                </div>
                
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowImportModal(false)}
                    className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Authentication wrapper component
const AuthenticatedApp = () => {
  const { user, loading, isAuthenticated } = useAuth();
  const [showLogin, setShowLogin] = useState(true);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return showLogin ? (
      <LoginForm onToggleForm={() => setShowLogin(false)} />
    ) : (
      <RegisterForm onToggleForm={() => setShowLogin(true)} />
    );
  }

  return <App />;
};

// Main App wrapper with AuthProvider
const AppWithAuth = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AuthenticatedApp />
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default AppWithAuth;