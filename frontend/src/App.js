import React, { useState, useEffect, useRef, useMemo } from "react";
import axios from "axios";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import "./App.css";

// Enhanced Components
import EnhancedDashboard from "./components/EnhancedDashboard";
import EnhancedProductManagement from "./components/EnhancedProductManagement";
import SettingsPanel from "./components/SettingsPanel";

// Icons
import { 
  Home, 
  Package, 
  Users, 
  Settings, 
  Search, 
  Bell, 
  LogOut, 
  Menu, 
  X,
  BarChart3,
  AlertTriangle,
  Calendar,
  Download
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Main Application Component
function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);

  // Check authentication on app load
  useEffect(() => {
    if (token) {
      // TODO: Verify token with backend
      setUser({ 
        username: "imadqejji", 
        role: "admin", 
        full_name: "Imad Qejji",
        department: null // Admin can access all departments
      });
    }
    setLoading(false);
  }, [token]);

  // Auto-refresh notifications
  useEffect(() => {
    if (user) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 60000); // Every minute
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchNotifications = async () => {
    try {
      // Fetch alerts/notifications from backend
      const response = await axios.get(`${BACKEND_URL}/api/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.recent_alerts) {
        setNotifications(response.data.recent_alerts);
      }
    } catch (error) {
      console.error("Error fetching notifications:", error);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-4 border-green-500 mx-auto mb-4"></div>
          <h2 className="text-2xl font-semibold text-gray-700 mb-2">Expiry Tracker</h2>
          <p className="text-gray-600">Loading inventory system...</p>
        </div>
      </div>
    );
  }

  if (!token || !user) {
    return <LoginForm onLogin={setToken} />;
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <Navigation 
          user={user} 
          onLogout={handleLogout}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          notifications={notifications}
        />

        {/* Main Content */}
        <div className={`transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'} lg:ml-64`}>
          <main className="p-6">
            <Routes>
              <Route path="/" element={<EnhancedDashboard user={user} />} />
              <Route path="/products" element={<EnhancedProductManagement user={user} />} />
              <Route path="/settings" element={<SettingsPanel user={user} />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

// Login Form Component
const LoginForm = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/login`, credentials);
      
      if (response.data.access_token) {
        localStorage.setItem("token", response.data.access_token);
        onLogin(response.data.access_token);
      }
    } catch (error) {
      setError(
        error.response?.data?.detail || "Login failed. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-400 via-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <Package size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Expiry Tracker</h1>
          <p className="text-gray-600">Inventory Management System</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) =>
                setCredentials({ ...credentials, username: e.target.value })
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors"
              placeholder="Enter your username"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) =>
                setCredentials({ ...credentials, password: e.target.value })
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-colors"
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white py-3 rounded-lg font-semibold transition-all hover:from-green-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Signing in...
              </div>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        {/* Help Text */}
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>Need help? Contact your system administrator</p>
        </div>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = ({ user, onLogout, sidebarOpen, setSidebarOpen, notifications }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const navItems = [
    { path: "/", icon: Home, label: "Dashboard", color: "text-green-600" },
    { path: "/products", icon: Package, label: "Products", color: "text-blue-600" },
    { path: "/reports", icon: BarChart3, label: "Reports", color: "text-purple-600" },
    { path: "/settings", icon: Settings, label: "Settings", color: "text-gray-600" }
  ];

  // Filter nav items based on user role
  const accessibleNavItems = navItems.filter(item => {
    if (item.path === "/settings") {
      return user?.role === "admin" || user?.role === "manager";
    }
    return true;
  });

  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden bg-white shadow-sm border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg text-gray-600 hover:bg-gray-100"
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
          
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
              <Package size={16} className="text-white" />
            </div>
            <span className="font-semibold text-gray-800">Expiry</span>
          </div>

          <div className="flex items-center space-x-3">
            {/* Notifications */}
            <div className="relative">
              <Bell size={20} className="text-gray-600" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {notifications.length}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 bg-white shadow-xl border-r border-gray-200 transform transition-transform duration-300 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0 ${sidebarOpen ? 'w-64' : 'w-16 lg:w-64'}`}>
        
        {/* Sidebar Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
              <Package size={20} className="text-white" />
            </div>
            <div className={`${sidebarOpen || 'lg:block'} ${!sidebarOpen && 'hidden'}`}>
              <h1 className="text-xl font-bold text-gray-800">Expiry Tracker</h1>
              <p className="text-sm text-gray-600">Inventory System</p>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {accessibleNavItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <li key={item.path}>
                  <button
                    onClick={() => navigate(item.path)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-green-50 text-green-700 border border-green-200'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                    }`}
                  >
                    <item.icon size={20} className={isActive ? 'text-green-600' : item.color} />
                    <span className={`font-medium ${sidebarOpen || 'lg:block'} ${!sidebarOpen && 'hidden'}`}>
                      {item.label}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User Info and Logout */}
        <div className="border-t border-gray-200 p-4">
          <div className={`flex items-center space-x-3 mb-4 ${sidebarOpen || 'lg:flex'} ${!sidebarOpen && 'hidden lg:flex'}`}>
            <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
              <span className="text-sm font-semibold text-gray-700">
                {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
              </span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-800">{user?.full_name || user?.username}</p>
              <p className="text-xs text-gray-600 uppercase">{user?.role}</p>
            </div>
          </div>

          <button
            onClick={onLogout}
            className={`w-full flex items-center space-x-3 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors ${
              sidebarOpen || 'lg:justify-start'
            } ${!sidebarOpen && 'justify-center lg:justify-start'}`}
          >
            <LogOut size={20} />
            <span className={`${sidebarOpen || 'lg:block'} ${!sidebarOpen && 'hidden'}`}>Logout</span>
          </button>
        </div>
      </div>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </>
  );
};

export default App;