import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";
import Dashboard from "./components/Dashboard";
import ProductManagement from "./components/ProductManagement";
import CategoryManagement from "./components/CategoryManagement";
import SupplierManagement from "./components/SupplierManagement";
import InventoryManagement from "./components/InventoryManagement";
import Reports from "./components/Reports";
import { Package, BarChart3, Users, Tags, Warehouse, Home } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navigation Component
const Navigation = () => {
  const location = useLocation();
  
  const navItems = [
    { path: "/", icon: Home, label: "Dashboard" },
    { path: "/products", icon: Package, label: "Products" },
    { path: "/inventory", icon: Warehouse, label: "Inventory" },
    { path: "/categories", icon: Tags, label: "Categories" },
    { path: "/suppliers", icon: Users, label: "Suppliers" },
    { path: "/reports", icon: BarChart3, label: "Reports" }
  ];

  return (
    <nav className="bg-slate-900 text-white w-64 min-h-screen p-4 fixed left-0 top-0 shadow-lg">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-blue-400 mb-2">Giant Hypermarket</h1>
        <p className="text-sm text-slate-400">Inventory Tracker</p>
      </div>
      
      <div className="space-y-2">
        {navItems.map(({ path, icon: Icon, label }) => (
          <Link
            key={path}
            to={path}
            className={`flex items-center space-x-3 p-3 rounded-lg transition-colors ${
              location.pathname === path
                ? "bg-blue-600 text-white"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            }`}
          >
            <Icon size={20} />
            <span>{label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
};

// Layout Component
const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="ml-64 p-6">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};

// Main App Component
function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState(null);

  useEffect(() => {
    const checkApiConnection = async () => {
      try {
        const response = await axios.get(`${API}/health`);
        setApiStatus("connected");
        console.log("API Status:", response.data);
      } catch (error) {
        setApiStatus("error");
        console.error("API Connection Error:", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkApiConnection();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading Giant Hypermarket System...</p>
        </div>
      </div>
    );
  }

  if (apiStatus === "error") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center p-8 bg-white rounded-lg shadow-lg">
          <div className="text-red-500 mb-4">
            <Package size={64} className="mx-auto" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">System Connection Error</h2>
          <p className="text-gray-600 mb-4">Unable to connect to the inventory management system.</p>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<ProductManagement />} />
            <Route path="/inventory" element={<InventoryManagement />} />
            <Route path="/categories" element={<CategoryManagement />} />
            <Route path="/suppliers" element={<SupplierManagement />} />
            <Route path="/reports" element={<Reports />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </div>
  );
}

export default App;