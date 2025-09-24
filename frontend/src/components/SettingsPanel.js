import React, { useState, useEffect } from 'react';
import { Save, Clock, Mail, Palette, Bell, Download, Settings, TestTube, AlertCircle, CheckCircle, Trash2, RefreshCw, Database, Upload, FileSpreadsheet, X, DollarSign } from 'lucide-react';

const SettingsPanel = ({ user }) => {
  const [emailSettings, setEmailSettings] = useState({
    daily_alert_time: '06:00',  // Updated to 06:00 AM as requested
    timezone: 'Asia/Aden',
    default_recipient: 'imad@geantyemen.com',
    department_recipients: {},
    weekly_reports_enabled: true,
    daily_alerts_enabled: true,
    expiry_threshold_days: 7,
    beverage_expiry_threshold_days: 15,
    email_failures: [],
    last_test_email: null
  });

  const [emailStatus, setEmailStatus] = useState(null);
  const [testEmailLoading, setTestEmailLoading] = useState(false);

  const [companySettings, setCompanySettings] = useState({
    company_name: 'Geant Hypermarket',
    logo_url: '/geant_main_page_logo.png',
    primary_color: '#22c55e',
    secondary_color: '#3b82f6',
    accent_color: '#f59e0b',
    contact_email: 'imad@geantyemen.com',
    contact_phone: '',
    address: ''
  });

  const [activeTab, setActiveTab] = useState('email');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  
  // System Reset States
  const [resetLoading, setResetLoading] = useState(false);
  const [resetConfirmation, setResetConfirmation] = useState('');
  const [systemStatus, setSystemStatus] = useState(null);
  
  // Excel Import States
  const [importFile, setImportFile] = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [showImportResult, setShowImportResult] = useState(false);

  // Currency Settings States
  const [currencySettings, setCurrencySettings] = useState({
    base_currency: 'USD',
    exchange_rates: {
      'YER': 0.004,
      'SAR': 0.267,
      'EUR': 1.10,
      'USD': 1.0
    },
    last_updated: null,
    updated_by: null
  });
  const [currencyLoading, setCurrencyLoading] = useState(false);
  const [editingCurrency, setEditingCurrency] = useState(null);
  const [tempRate, setTempRate] = useState('');

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchSettings();
    fetchEmailStatus();
    fetchSystemStatus();
    fetchCurrencySettings();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/system/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSystemStatus(data);
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const resetSystemData = async () => {
    if (resetConfirmation !== 'RESET') {
      alert('Please type "RESET" to confirm data deletion');
      return;
    }

    if (!window.confirm('⚠️ WARNING: This will permanently delete ALL data (products, waste entries, alerts, return forms). This action cannot be undone. Are you absolutely sure?')) {
      return;
    }

    setResetLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/system/reset`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ SYSTEM RESET COMPLETED!\n\nDeleted:\n- Products: ${result.reset_summary.cleared_collections.products?.documents_deleted || 0}\n- Waste Entries: ${result.reset_summary.cleared_collections.waste_entries?.documents_deleted || 0}\n- Alerts: ${result.reset_summary.cleared_collections.alerts?.documents_deleted || 0}\n- Return Forms: ${result.reset_summary.cleared_collections.return_forms?.documents_deleted || 0}\n\nTotal: ${result.reset_summary.total_documents_deleted} documents deleted`);
        
        // Reset confirmation field
        setResetConfirmation('');
        
        // Refresh system status
        fetchSystemStatus();
        
        // Suggest page refresh
        if (window.confirm('System reset complete! Would you like to refresh the page to see the updated dashboard?')) {
          window.location.reload();
        }
      } else {
        const errorData = await response.json();
        alert(`❌ Reset failed: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Error resetting system:', error);
      alert('❌ Reset failed: Network error');
    } finally {
      setResetLoading(false);
    }
  };

  const downloadTemplate = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/system/import-template`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `product_import_template_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        alert('❌ Failed to download template');
      }
    } catch (error) {
      console.error('Error downloading template:', error);
      alert('❌ Failed to download template: Network error');
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        alert('❌ Please select an Excel file (.xlsx or .xls)');
        event.target.value = '';
        return;
      }
      
      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert('❌ File too large. Maximum size is 10MB');
        event.target.value = '';
        return;
      }
      
      setImportFile(file);
      setImportResult(null);
      setShowImportResult(false);
    }
  };

  const importExcelData = async () => {
    if (!importFile) {
      alert('Please select an Excel file first');
      return;
    }

    setImportLoading(true);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append('file', importFile);

      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/system/import-excel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      const result = await response.json();

      if (response.ok) {
        setImportResult(result);
        setShowImportResult(true);
        
        // Refresh system status
        fetchSystemStatus();
        
        // Show success message
        const stats = result.import_summary;
        alert(`✅ EXCEL IMPORT COMPLETED!\n\nResults:\n- Total Rows: ${stats.total_rows}\n- Successful: ${stats.successful_imports}\n- Failed: ${stats.failed_imports}\n- Success Rate: ${((stats.successful_imports / stats.total_rows) * 100).toFixed(1)}%\n\nCheck the detailed results below.`);
        
      } else {
        setImportResult({
          message: result.detail || 'Import failed',
          import_summary: { 
            total_rows: 0, 
            successful_imports: 0, 
            failed_imports: 0, 
            errors: [result.detail || 'Unknown error'] 
          },
          status: 'error'
        });
        setShowImportResult(true);
        alert(`❌ Import failed: ${result.detail}`);
      }
    } catch (error) {
      console.error('Error importing Excel:', error);
      setImportResult({
        message: 'Network error during import',
        import_summary: { 
          total_rows: 0, 
          successful_imports: 0, 
          failed_imports: 0, 
          errors: ['Network error: ' + error.message] 
        },
        status: 'error'
      });
      setShowImportResult(true);
      alert('❌ Import failed: Network error');
    } finally {
      setImportLoading(false);
    }
  };

  const clearImportData = () => {
    setImportFile(null);
    setImportResult(null);
    setShowImportResult(false);
    // Clear file input
    const fileInput = document.getElementById('excel-file-input');
    if (fileInput) {
      fileInput.value = '';
    }
  };

  const fetchEmailStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/alerts/email-status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const statusData = await response.json();
        setEmailStatus(statusData);
      }
    } catch (error) {
      console.error('Error fetching email status:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch email settings
      const emailResponse = await fetch(`${BACKEND_URL}/api/settings/email`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (emailResponse.ok) {
        const emailData = await emailResponse.json();
        setEmailSettings(emailData);
      }

      // Fetch company settings
      const companyResponse = await fetch(`${BACKEND_URL}/api/settings/company`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (companyResponse.ok) {
        const companyData = await companyResponse.json();
        setCompanySettings(companyData);
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const saveEmailSettings = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/settings/email`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(emailSettings)
      });

      if (response.ok) {
        const result = await response.json();
        setMessage(`✅ Email settings saved successfully! Time: ${result.daily_alert_time} (${result.timezone})`);
        setTimeout(() => setMessage(''), 5000);
        // Refresh email status after successful save
        await fetchEmailStatus();
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        setMessage(`❌ Failed to save email settings: ${errorData.detail || 'Server error'}`);
        setTimeout(() => setMessage(''), 8000);
      }
    } catch (error) {
      console.error('Email settings save error:', error);
      setMessage(`❌ Error saving email settings: ${error.message}`);
      setTimeout(() => setMessage(''), 8000);
    } finally {
      setLoading(false);
    }
  };

  const saveCompanySettings = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/settings/company`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(companySettings)
      });

      if (response.ok) {
        setMessage('Company settings saved successfully!');
        setTimeout(() => setMessage(''), 3000);
      } else {
        setMessage('Failed to save company settings');
      }
    } catch (error) {
      setMessage('Error saving company settings');
    } finally {
      setLoading(false);
    }
  };

  const sendTestAlert = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/alerts/send-daily`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const result = await response.json();
        setMessage(`Test alert sent! Out of stock: ${result.out_of_stock_count}, Near expiry: ${result.near_expiry_count}`);
      } else {
        setMessage('Failed to send test alert');
      }
    } catch (error) {
      setMessage('Error sending test alert');
    } finally {
      setLoading(false);
    }
  };

  const sendTestEmail = async () => {
    setTestEmailLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/alerts/send-test-email`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const result = await response.json();
        setMessage(`✅ Test email sent successfully to ${result.sent_to[0]}! Check your inbox. Sent at: ${result.aden_time}`);
        await fetchEmailStatus(); // Refresh status
        setTimeout(() => setMessage(''), 8000);
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        const errorMsg = errorData.detail || 'Unknown error';
        
        if (errorMsg.includes('EMAIL_PASSWORD') || errorMsg.includes('not configured')) {
          setMessage(`❌ Email not configured: EMAIL_PASSWORD missing in server environment. Please contact system administrator to configure email credentials.`);
        } else {
          setMessage(`❌ Failed to send test email: ${errorMsg}`);
        }
        setTimeout(() => setMessage(''), 10000);
      }
    } catch (error) {
      console.error('Test email error:', error);
      setMessage(`❌ Error sending test email: ${error.message}. Check network connection.`);
      setTimeout(() => setMessage(''), 8000);
    } finally {
      setTestEmailLoading(false);
    }
  };

  // Currency Settings Functions
  const fetchCurrencySettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/currency/settings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrencySettings(data.settings);
      }
    } catch (error) {
      console.error('Error fetching currency settings:', error);
    }
  };

  const updateCurrencySettings = async () => {
    setCurrencyLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/currency/settings`, {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(currencySettings)
      });

      if (response.ok) {
        const result = await response.json();
        setCurrencySettings(result.settings);
        setMessage(`✅ Currency settings updated successfully by ${result.updated_by}!`);
        setTimeout(() => setMessage(''), 5000);
      } else {
        const errorData = await response.json();
        setMessage(`❌ Failed to update currency settings: ${errorData.detail}`);
        setTimeout(() => setMessage(''), 5000);
      }
    } catch (error) {
      console.error('Currency update error:', error);
      setMessage(`❌ Error updating currency settings: ${error.message}`);
      setTimeout(() => setMessage(''), 5000);
    } finally {
      setCurrencyLoading(false);
    }
  };

  const updateSingleRate = async (currency, newRate) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/currency/rates/quick-update`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          currency: currency,
          rate: parseFloat(newRate)
        })
      });

      if (response.ok) {
        const result = await response.json();
        // Update local state
        setCurrencySettings(prev => ({
          ...prev,
          exchange_rates: {
            ...prev.exchange_rates,
            [currency]: parseFloat(newRate)
          },
          last_updated: new Date().toISOString(),
          updated_by: user?.username || 'Current User'
        }));
        
        setMessage(`✅ ${currency} rate updated to ${newRate} successfully!`);
        setTimeout(() => setMessage(''), 3000);
        setEditingCurrency(null);
        setTempRate('');
      } else {
        const errorData = await response.json();
        setMessage(`❌ Failed to update ${currency} rate: ${errorData.detail}`);
        setTimeout(() => setMessage(''), 5000);
      }
    } catch (error) {
      console.error('Rate update error:', error);
      setMessage(`❌ Error updating rate: ${error.message}`);
      setTimeout(() => setMessage(''), 5000);
    }
  };

  const startEditing = (currency) => {
    setEditingCurrency(currency);
    setTempRate(currencySettings.exchange_rates[currency].toString());
  };

  const cancelEditing = () => {
    setEditingCurrency(null);
    setTempRate('');
  };

  const confirmRateUpdate = () => {
    if (tempRate && parseFloat(tempRate) > 0) {
      updateSingleRate(editingCurrency, tempRate);
    }
  };

  const tabs = [
    { id: 'email', label: 'Email & Alerts', icon: Mail },
    { id: 'company', label: 'Company Settings', icon: Palette },
    { id: 'currency', label: 'Currency Settings', icon: DollarSign },
    { id: 'reports', label: 'Reports', icon: Download },
    { id: 'import', label: 'Excel Import', icon: Upload },
    { id: 'reset', label: 'System Reset', icon: Database }
  ];

  if (user?.role !== 'admin' && user?.role !== 'manager') {
    return (
      <div className="text-center p-8">
        <div className="text-gray-400 mb-4">
          <Settings size={64} className="mx-auto" />
        </div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Access Restricted</h2>
        <p className="text-gray-600">Only administrators and managers can access settings.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white p-6 rounded-xl">
        <h1 className="text-3xl font-bold">Settings Panel</h1>
        <p className="text-green-100">Configure system settings and preferences</p>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg ${message.includes('Error') || message.includes('Failed') 
          ? 'bg-red-50 text-red-700 border border-red-200' 
          : 'bg-green-50 text-green-700 border border-green-200'
        }`}>
          {message}
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === id
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon size={16} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Email & Alerts Tab */}
          {activeTab === 'email' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-800">Email & Alert Settings</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Daily Alert Time (Aden Timezone)
                  </label>
                  <div className="flex items-center space-x-2">
                    <Clock size={16} className="text-gray-400" />
                    <input
                      type="time"
                      value={emailSettings.daily_alert_time}
                      onChange={(e) => setEmailSettings({
                        ...emailSettings,
                        daily_alert_time: e.target.value
                      })}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Email Recipient
                  </label>
                  <input
                    type="email"
                    value={emailSettings.default_recipient}
                    onChange={(e) => setEmailSettings({
                      ...emailSettings,
                      default_recipient: e.target.value
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    placeholder="imad@geantyemen.com"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Expiry Threshold (Days)
                  </label>
                  <input
                    type="number"
                    value={emailSettings.expiry_threshold_days}
                    onChange={(e) => setEmailSettings({
                      ...emailSettings,
                      expiry_threshold_days: parseInt(e.target.value)
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    min="1"
                    max="30"
                  />
                  <p className="text-xs text-gray-500 mt-1">General expiry alert threshold</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Beverage Expiry Threshold (Days)
                  </label>
                  <input
                    type="number"
                    value={emailSettings.beverage_expiry_threshold_days}
                    onChange={(e) => setEmailSettings({
                      ...emailSettings,
                      beverage_expiry_threshold_days: parseInt(e.target.value)
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    min="1"
                    max="60"
                  />
                  <p className="text-xs text-gray-500 mt-1">Special threshold for S-10 Beverages</p>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium text-gray-800">Alert Options</h4>
                
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    id="daily_alerts"
                    checked={emailSettings.daily_alerts_enabled}
                    onChange={(e) => setEmailSettings({
                      ...emailSettings,
                      daily_alerts_enabled: e.target.checked
                    })}
                    className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                  />
                  <label htmlFor="daily_alerts" className="text-sm font-medium text-gray-700">
                    Enable Daily Email Alerts (06:00 AM Aden time as requested)
                  </label>
                </div>

                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    id="weekly_reports"
                    checked={emailSettings.weekly_reports_enabled}
                    onChange={(e) => setEmailSettings({
                      ...emailSettings,
                      weekly_reports_enabled: e.target.checked
                    })}
                    className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                  />
                  <label htmlFor="weekly_reports" className="text-sm font-medium text-gray-700">
                    Enable Weekly Summary Reports
                  </label>
                </div>
              </div>

              {/* Email Configuration Guide */}
              {emailStatus && !emailStatus.email_configured && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h4 className="font-medium text-yellow-800 mb-2 flex items-center">
                    <AlertCircle size={16} className="mr-2" />
                    Email Configuration Required
                  </h4>
                  <div className="text-sm text-yellow-700 space-y-2">
                    <p><strong>To enable email functionality:</strong></p>
                    <ol className="list-decimal list-inside space-y-1 ml-2">
                      <li>The system administrator needs to set the <code className="bg-yellow-100 px-1 rounded">EMAIL_PASSWORD</code> environment variable</li>
                      <li>This should be an app-specific password for: <code className="bg-yellow-100 px-1 rounded">{emailStatus.sender_email || 'inventory@geantyemen.com'}</code></li>
                      <li>After configuration, restart the backend server</li>
                      <li>Use "Send Test Email Now" to verify the setup</li>
                    </ol>
                    <p className="text-xs text-yellow-600 mt-2">
                      <strong>Note:</strong> Until configured, email alerts and test emails will not be sent.
                    </p>
                  </div>
                </div>
              )}

              {/* Demo Mode Notice */}
              {emailStatus && emailStatus.demo_mode && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-800 mb-2 flex items-center">
                    <CheckCircle size={16} className="mr-2" />
                    Demo Mode Active
                  </h4>
                  <div className="text-sm text-blue-700 space-y-2">
                    <p><strong>Email system is running in demo mode:</strong></p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li>Emails are simulated (not actually sent)</li>
                      <li>Test email functionality is working</li>
                      <li>Email logs and timestamps are recorded</li>
                      <li>Perfect for testing and development</li>
                    </ul>
                    <p className="text-xs text-blue-600 mt-2">
                      <strong>To enable real emails:</strong> Configure actual SMTP credentials in production environment.
                    </p>
                  </div>
                </div>
              )}

              {/* Email System Status */}
              {emailStatus && (
                <div className="bg-gray-50 p-4 rounded-lg border">
                  <h4 className="font-medium text-gray-800 mb-3 flex items-center">
                    <Settings size={16} className="mr-2" />
                    Email System Status {emailStatus.demo_mode && <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">DEMO MODE</span>}
                  </h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Current Aden Time:</span>
                      <br />
                      <span className="text-gray-600">{emailStatus.current_aden_time}</span>
                    </div>
                    <div>
                      <span className="font-medium">Daily Alert Schedule:</span>
                      <br />
                      <span className="text-gray-600">{emailStatus.daily_alert_time} AM (Asia/Aden)</span>
                    </div>
                    <div>
                      <span className="font-medium">Email Configuration:</span>
                      <br />
                      <span className={`${emailStatus.email_configured ? 'text-green-600' : 'text-red-600'} font-medium`}>
                        {emailStatus.email_configured ? (emailStatus.demo_mode ? '🧪 Demo Mode' : '✅ Configured') : '❌ Not Configured'}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium">Last Test Email:</span>
                      <br />
                      <span className="text-gray-600">
                        {emailStatus.last_test_email ? new Date(emailStatus.last_test_email).toLocaleString() : 'Never sent'}
                      </span>
                    </div>
                  </div>

                  {/* Recent Email Failures */}
                  {emailStatus.recent_failures && emailStatus.recent_failures.length > 0 && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
                      <h5 className="font-medium text-red-800 flex items-center mb-2">
                        <AlertCircle size={14} className="mr-1" />
                        Recent Email Failures ({emailStatus.recent_failures.length})
                      </h5>
                      <div className="space-y-1 text-xs">
                        {emailStatus.recent_failures.slice(-3).map((failure, index) => (
                          <div key={index} className="text-red-700">
                            <span className="font-medium">{new Date(failure.timestamp).toLocaleString()}:</span> {failure.error}
                            {failure.type && <span className="text-red-500"> ({failure.type})</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
                <button
                  onClick={saveEmailSettings}
                  disabled={loading}
                  className="flex items-center justify-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <Save size={16} />
                  <span>{loading ? 'Saving...' : 'Save Settings'}</span>
                </button>

                <button
                  onClick={sendTestEmail}
                  disabled={testEmailLoading}
                  className="flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <TestTube size={16} />
                  <span>{testEmailLoading ? 'Sending...' : 'Send Test Email Now'}</span>
                </button>

                <button
                  onClick={sendTestAlert}
                  disabled={loading}
                  className="flex items-center justify-center space-x-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50"
                >
                  <Bell size={16} />
                  <span>Send Daily Alert</span>
                </button>
              </div>
            </div>
          )}

          {/* Company Settings Tab */}
          {activeTab === 'company' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-800">Company Branding Settings</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Company Name
                  </label>
                  <input
                    type="text"
                    value={companySettings.company_name}
                    onChange={(e) => setCompanySettings({
                      ...companySettings,
                      company_name: e.target.value
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contact Email
                  </label>
                  <input
                    type="email"
                    value={companySettings.contact_email}
                    onChange={(e) => setCompanySettings({
                      ...companySettings,
                      contact_email: e.target.value
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Company Address
                </label>
                <textarea
                  value={companySettings.address}
                  onChange={(e) => setCompanySettings({
                    ...companySettings,
                    address: e.target.value
                  })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div className="space-y-4">
                <h4 className="font-medium text-gray-800">Theme Colors</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Primary Color (Green)
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="color"
                        value={companySettings.primary_color}
                        onChange={(e) => setCompanySettings({
                          ...companySettings,
                          primary_color: e.target.value
                        })}
                        className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                      />
                      <input
                        type="text"
                        value={companySettings.primary_color}
                        onChange={(e) => setCompanySettings({
                          ...companySettings,
                          primary_color: e.target.value
                        })}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Secondary Color (Blue)
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="color"
                        value={companySettings.secondary_color}
                        onChange={(e) => setCompanySettings({
                          ...companySettings,
                          secondary_color: e.target.value
                        })}
                        className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                      />
                      <input
                        type="text"
                        value={companySettings.secondary_color}
                        onChange={(e) => setCompanySettings({
                          ...companySettings,
                          secondary_color: e.target.value
                        })}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Accent Color (Orange)
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="color"
                        value={companySettings.accent_color}
                        onChange={(e) => setCompanySettings({
                          ...companySettings,
                          accent_color: e.target.value
                        })}
                        className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                      />
                      <input
                        type="text"
                        value={companySettings.accent_color}
                        onChange={(e) => setCompanySettings({
                          ...companySettings,
                          accent_color: e.target.value
                        })}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <button
                onClick={saveCompanySettings}
                disabled={loading}
                className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                <Save size={16} />
                <span>{loading ? 'Saving...' : 'Save Settings'}</span>
              </button>
            </div>
          )}

          {/* Currency Settings Tab */}
          {activeTab === 'currency' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-800">Currency & Exchange Rate Settings</h3>
                <div className="text-sm text-gray-500">
                  {currencySettings.last_updated && (
                    <span>Last updated: {new Date(currencySettings.last_updated).toLocaleString()}</span>
                  )}
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <DollarSign className="text-blue-600" size={20} />
                  <h4 className="font-semibold text-blue-800">Exchange Rate Management</h4>
                </div>
                <p className="text-blue-700 text-sm">
                  Manage exchange rates for currency conversions in reports. Waste reports will show both original currency and USD values using these rates.
                </p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Base Currency Selection */}
                <div className="bg-white border border-gray-200 p-6 rounded-lg">
                  <h4 className="font-semibold text-gray-800 mb-4">Base Currency</h4>
                  <div className="space-y-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Reference Currency (All rates convert to this)
                    </label>
                    <select
                      value={currencySettings.base_currency}
                      onChange={(e) => setCurrencySettings(prev => ({...prev, base_currency: e.target.value}))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="USD">USD - US Dollar</option>
                      <option value="EUR">EUR - Euro</option>
                      <option value="SAR">SAR - Saudi Riyal</option>
                      <option value="YER">YER - Yemeni Rial</option>
                    </select>
                    <p className="text-xs text-gray-500">
                      Currently set to {currencySettings.base_currency}. Waste reports will show conversions to this currency.
                    </p>
                  </div>
                </div>

                {/* Exchange Rates */}
                <div className="bg-white border border-gray-200 p-6 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold text-gray-800">Exchange Rates</h4>
                    <button
                      onClick={updateCurrencySettings}
                      disabled={currencyLoading}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                    >
                      {currencyLoading ? 'Saving...' : 'Save All'}
                    </button>
                  </div>
                  
                  <div className="space-y-3">
                    {Object.entries(currencySettings.exchange_rates).map(([currency, rate]) => (
                      <div key={currency} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <span className="font-medium text-gray-700 w-12">{currency}</span>
                          <span className="text-sm text-gray-500">→ {currencySettings.base_currency}</span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {editingCurrency === currency ? (
                            <>
                              <input
                                type="number"
                                step="0.0001"
                                value={tempRate}
                                onChange={(e) => setTempRate(e.target.value)}
                                className="w-24 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                                onKeyPress={(e) => e.key === 'Enter' && confirmRateUpdate()}
                              />
                              <button
                                onClick={confirmRateUpdate}
                                className="p-1 text-green-600 hover:text-green-800"
                                title="Save"
                              >
                                <CheckCircle size={16} />
                              </button>
                              <button
                                onClick={cancelEditing}
                                className="p-1 text-red-600 hover:text-red-800"
                                title="Cancel"
                              >
                                <X size={16} />
                              </button>
                            </>
                          ) : (
                            <>
                              <span className="font-mono text-sm w-20 text-right">
                                {rate.toFixed(4)}
                              </span>
                              <button
                                onClick={() => startEditing(currency)}
                                className="p-1 text-blue-600 hover:text-blue-800"
                                title="Edit rate"
                              >
                                <Settings size={16} />
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-xs text-yellow-800">
                      💡 <strong>Tip:</strong> Click the settings icon to edit individual rates, or update multiple rates and click "Save All".
                      These rates will be used for USD conversion in waste reports.
                    </p>
                  </div>
                </div>
              </div>

              {/* Current Rate Summary */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-3">Current Rate Summary</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(currencySettings.exchange_rates).map(([currency, rate]) => (
                    <div key={currency} className="text-center">
                      <div className="text-sm text-gray-500">1 {currency}</div>
                      <div className="font-mono font-semibold">
                        {rate.toFixed(4)} {currencySettings.base_currency}
                      </div>
                    </div>
                  ))}
                </div>
                
                {currencySettings.updated_by && (
                  <div className="mt-3 text-xs text-gray-500 text-center">
                    Last updated by: {currencySettings.updated_by}
                  </div>
                )}
              </div>

              {/* Example Conversion */}
              <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
                <h4 className="font-semibold text-green-800 mb-2">Example Waste Report Conversion</h4>
                <p className="text-green-700 text-sm mb-3">
                  When generating waste reports, values will be converted as follows:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                  <div className="bg-white p-3 rounded border">
                    <div className="font-semibold">1,000 YER waste</div>
                    <div className="text-gray-600">= {(1000 * currencySettings.exchange_rates.YER).toFixed(2)} USD</div>
                  </div>
                  <div className="bg-white p-3 rounded border">
                    <div className="font-semibold">100 SAR waste</div>
                    <div className="text-gray-600">= {(100 * currencySettings.exchange_rates.SAR).toFixed(2)} USD</div>
                  </div>
                  <div className="bg-white p-3 rounded border">
                    <div className="font-semibold">50 EUR waste</div>
                    <div className="text-gray-600">= {(50 * currencySettings.exchange_rates.EUR).toFixed(2)} USD</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Reports Tab */}
          {activeTab === 'reports' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-800">Report Settings</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-800 mb-3">Daily Reports</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Out-of-stock items by department</li>
                    <li>• Near-expiry items (7 days general, 15 days beverages)</li>
                    <li>• Department-level KPIs</li>
                    <li>• Supplier performance summary</li>
                  </ul>
                  <p className="text-xs text-gray-500 mt-2">
                    Sent daily at {emailSettings.daily_alert_time} Aden time
                  </p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-800 mb-3">Weekly Reports</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Comprehensive inventory summary</li>
                    <li>• Stock movement analysis</li>
                    <li>• Top performing/problematic suppliers</li>
                    <li>• Department comparisons</li>
                  </ul>
                  <p className="text-xs text-gray-500 mt-2">
                    Sent every Monday at 09:00 AM
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium text-gray-800">Export Options</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button 
                    className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center"
                    onClick={() => window.open(`${BACKEND_URL}/api/export/excel`, '_blank')}
                  >
                    <Download size={24} className="mx-auto mb-2 text-green-600" />
                    <div className="text-sm font-medium">Export to Excel</div>
                    <div className="text-xs text-gray-500">Complete inventory data</div>
                  </button>

                  <button 
                    className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center"
                    onClick={() => window.open(`${BACKEND_URL}/api/reports/low-stock`, '_blank')}
                  >
                    <Download size={24} className="mx-auto mb-2 text-orange-600" />
                    <div className="text-sm font-medium">Low Stock Report</div>
                    <div className="text-xs text-gray-500">Items needing reorder</div>
                  </button>

                  <button 
                    className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center"
                    onClick={() => window.open(`${BACKEND_URL}/api/reports/suppliers`, '_blank')}
                  >
                    <Download size={24} className="mx-auto mb-2 text-blue-600" />
                    <div className="text-sm font-medium">Supplier Report</div>
                    <div className="text-xs text-gray-500">Supplier performance data</div>
                  </button>
                </div>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-800 mb-2">📧 Email Configuration</h4>
                <p className="text-sm text-blue-700">
                  All reports are automatically sent to: <strong>{emailSettings.default_recipient}</strong>
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Configure additional department-specific recipients in the Email & Alerts tab.
                </p>
              </div>
            </div>
          )}

          {/* Excel Import Tab */}
          {activeTab === 'import' && (
            <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Upload size={20} className="text-green-600" />
                  <h3 className="text-lg font-semibold text-green-800">📊 Excel Data Import</h3>
                </div>
                <p className="text-green-700 text-sm">
                  Import your product data from Excel files. Download the template first to ensure proper formatting.
                </p>
              </div>

              {/* Step 1: Download Template */}
              <div className="bg-white border border-gray-200 p-6 rounded-lg">
                <div className="flex items-center space-x-3 mb-4">
                  <FileSpreadsheet size={24} className="text-blue-600" />
                  <h4 className="text-lg font-semibold text-gray-800">Step 1: Download Excel Template</h4>
                </div>
                
                <p className="text-gray-600 mb-4">
                  Download the Excel template with proper column headers and sample data to ensure successful import.
                </p>

                <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-4">
                  <h5 className="font-medium text-blue-800 mb-2">Template includes:</h5>
                  <div className="grid grid-cols-2 gap-2 text-sm text-blue-700">
                    <div>✓ Required columns (product_name, department, etc.)</div>
                    <div>✓ Optional columns (barcode, expiry_date, etc.)</div>
                    <div>✓ Sample data for reference</div>
                    <div>✓ Instructions sheet with field descriptions</div>
                    <div>✓ Valid department codes (01-FMG, 01-CGD, 01-OPSS)</div>
                    <div>✓ Supported currencies (YER, SAR, EUR, USD)</div>
                  </div>
                </div>

                <button
                  onClick={downloadTemplate}
                  className="flex items-center space-x-2 bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition-colors font-medium"
                >
                  <Download size={16} />
                  <span>Download Excel Template</span>
                </button>
              </div>

              {/* Step 2: Upload Excel File */}
              <div className="bg-white border border-gray-200 p-6 rounded-lg">
                <div className="flex items-center space-x-3 mb-4">
                  <Upload size={24} className="text-green-600" />
                  <h4 className="text-lg font-semibold text-gray-800">Step 2: Upload Your Excel File</h4>
                </div>

                <p className="text-gray-600 mb-4">
                  Select your completed Excel file with product data. Supported formats: .xlsx, .xls (max 10MB)
                </p>

                <div className="space-y-4">
                  <div>
                    <input
                      id="excel-file-input"
                      type="file"
                      accept=".xlsx,.xls"
                      onChange={handleFileSelect}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                  </div>

                  {importFile && (
                    <div className="bg-gray-50 border border-gray-200 p-4 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <FileSpreadsheet size={20} className="text-green-600" />
                          <div>
                            <p className="font-medium text-gray-900">{importFile.name}</p>
                            <p className="text-sm text-gray-600">
                              {(importFile.size / 1024 / 1024).toFixed(2)} MB • {new Date(importFile.lastModified).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={clearImportData}
                          className="text-red-500 hover:text-red-700 p-1"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    </div>
                  )}

                  <button
                    onClick={importExcelData}
                    disabled={!importFile || importLoading}
                    className="w-full flex items-center justify-center space-x-2 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {importLoading ? (
                      <>
                        <RefreshCw size={16} className="animate-spin" />
                        <span>Importing Data...</span>
                      </>
                    ) : (
                      <>
                        <Upload size={16} />
                        <span>Import Excel Data</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Import Results */}
              {showImportResult && importResult && (
                <div className="bg-white border border-gray-200 p-6 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <CheckCircle size={24} className={importResult.status === 'success' ? 'text-green-600' : 'text-red-600'} />
                      <h4 className="text-lg font-semibold text-gray-800">Import Results</h4>
                    </div>
                    <button
                      onClick={() => setShowImportResult(false)}
                      className="text-gray-500 hover:text-gray-700 p-1"
                    >
                      <X size={16} />
                    </button>
                  </div>

                  <div className={`p-4 rounded-lg mb-4 ${
                    importResult.status === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                  }`}>
                    <p className={`font-medium ${importResult.status === 'success' ? 'text-green-800' : 'text-red-800'}`}>
                      {importResult.message}
                    </p>
                  </div>

                  {importResult.import_summary && (
                    <div className="space-y-4">
                      {/* Statistics */}
                      <div className="grid grid-cols-4 gap-4">
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="text-2xl font-bold text-gray-900">{importResult.import_summary.total_rows}</div>
                          <div className="text-sm text-gray-600">Total Rows</div>
                        </div>
                        <div className="text-center p-3 bg-green-50 rounded-lg">
                          <div className="text-2xl font-bold text-green-600">{importResult.import_summary.successful_imports}</div>
                          <div className="text-sm text-gray-600">Successful</div>
                        </div>
                        <div className="text-center p-3 bg-red-50 rounded-lg">
                          <div className="text-2xl font-bold text-red-600">{importResult.import_summary.failed_imports}</div>
                          <div className="text-sm text-gray-600">Failed</div>
                        </div>
                        <div className="text-center p-3 bg-blue-50 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">
                            {((importResult.import_summary.successful_imports / importResult.import_summary.total_rows) * 100).toFixed(1)}%
                          </div>
                          <div className="text-sm text-gray-600">Success Rate</div>
                        </div>
                      </div>

                      {/* Successful Imports */}
                      {importResult.import_summary.imported_products && importResult.import_summary.imported_products.length > 0 && (
                        <div>
                          <h5 className="font-medium text-green-800 mb-2">✅ Successfully Imported Products:</h5>
                          <div className="bg-green-50 border border-green-200 p-3 rounded-lg max-h-40 overflow-y-auto">
                            {importResult.import_summary.imported_products.slice(0, 10).map((product, index) => (
                              <div key={index} className="text-sm text-green-700 py-1">
                                Row {product.row}: {product.product_name} ({product.department})
                                {product.barcode && ` - ${product.barcode}`}
                              </div>
                            ))}
                            {importResult.import_summary.imported_products.length > 10 && (
                              <div className="text-sm text-green-600 pt-2 border-t border-green-200">
                                ... and {importResult.import_summary.imported_products.length - 10} more products
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Errors */}
                      {importResult.import_summary.errors && importResult.import_summary.errors.length > 0 && (
                        <div>
                          <h5 className="font-medium text-red-800 mb-2">❌ Import Errors:</h5>
                          <div className="bg-red-50 border border-red-200 p-3 rounded-lg max-h-40 overflow-y-auto">
                            {importResult.import_summary.errors.map((error, index) => (
                              <div key={index} className="text-sm text-red-700 py-1">
                                {error}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Skipped Rows */}
                      {importResult.import_summary.skipped_rows && importResult.import_summary.skipped_rows.length > 0 && (
                        <div>
                          <h5 className="font-medium text-yellow-800 mb-2">⚠️ Skipped Rows:</h5>
                          <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg max-h-40 overflow-y-auto">
                            {importResult.import_summary.skipped_rows.map((skip, index) => (
                              <div key={index} className="text-sm text-yellow-700 py-1">
                                {skip}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Recommendations */}
                      {importResult.recommendations && (
                        <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                          <h5 className="font-medium text-blue-800 mb-2">💡 Next Steps:</h5>
                          <ul className="text-sm text-blue-700 space-y-1">
                            {importResult.recommendations.map((rec, index) => (
                              <li key={index}>• {rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Current System Status After Import */}
              {systemStatus && (
                <div className="bg-gray-50 border border-gray-200 p-4 rounded-lg">
                  <div className="flex items-center space-x-3 mb-3">
                    <Database size={20} className="text-gray-600" />
                    <h5 className="font-medium text-gray-800">Current System Data</h5>
                    <button
                      onClick={fetchSystemStatus}
                      className="ml-auto text-blue-600 hover:text-blue-800 text-sm"
                    >
                      <RefreshCw size={14} className="inline mr-1" />
                      Refresh
                    </button>
                  </div>
                  <div className="grid grid-cols-4 gap-3">
                    <div className="text-center">
                      <div className="text-lg font-bold text-gray-900">{systemStatus.data_counts.products || 0}</div>
                      <div className="text-xs text-gray-600">Products</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-gray-900">{systemStatus.data_counts.waste_entries || 0}</div>
                      <div className="text-xs text-gray-600">Waste Entries</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-gray-900">{systemStatus.data_counts.alerts || 0}</div>
                      <div className="text-xs text-gray-600">Alerts</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-gray-900">{systemStatus.data_counts.return_forms || 0}</div>
                      <div className="text-xs text-gray-600">Return Forms</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* System Reset Tab */}
          {activeTab === 'reset' && (
            <div className="space-y-6">
              <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <AlertCircle size={20} className="text-red-600" />
                  <h3 className="text-lg font-semibold text-red-800">⚠️ DANGER ZONE - System Reset</h3>
                </div>
                <p className="text-red-700 text-sm">
                  This action will permanently delete ALL data from the system and cannot be undone.
                </p>
              </div>

              {/* Current System Status */}
              <div className="bg-white border border-gray-200 p-6 rounded-lg">
                <div className="flex items-center space-x-3 mb-4">
                  <Database size={24} className="text-blue-600" />
                  <h4 className="text-lg font-semibold text-gray-800">Current System Data</h4>
                  <button
                    onClick={fetchSystemStatus}
                    className="ml-auto flex items-center space-x-2 text-blue-600 hover:text-blue-800 text-sm"
                  >
                    <RefreshCw size={16} />
                    <span>Refresh</span>
                  </button>
                </div>

                {systemStatus ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">{systemStatus.data_counts.products || 0}</div>
                      <div className="text-sm text-gray-600">Products</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">{systemStatus.data_counts.waste_entries || 0}</div>
                      <div className="text-sm text-gray-600">Waste Entries</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">{systemStatus.data_counts.alerts || 0}</div>
                      <div className="text-sm text-gray-600">Alerts</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-900">{systemStatus.data_counts.return_forms || 0}</div>
                      <div className="text-sm text-gray-600">Return Forms</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    <RefreshCw size={24} className="mx-auto mb-2 animate-spin" />
                    <p>Loading system status...</p>
                  </div>
                )}

                <div className="mt-4 text-xs text-gray-500">
                  Last updated: {systemStatus ? new Date(systemStatus.last_updated).toLocaleString() : 'Never'}
                </div>
              </div>

              {/* Reset Form */}
              <div className="bg-white border border-gray-200 p-6 rounded-lg">
                <div className="flex items-center space-x-3 mb-4">
                  <Trash2 size={24} className="text-red-600" />
                  <h4 className="text-lg font-semibold text-gray-800">Reset All System Data</h4>
                </div>

                <div className="space-y-4">
                  <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                    <h5 className="font-medium text-yellow-800 mb-2">What will be deleted:</h5>
                    <ul className="text-sm text-yellow-700 space-y-1">
                      <li>✗ All Products (inventory items)</li>
                      <li>✗ All Waste Entries (waste tracking data)</li>
                      <li>✗ All Alerts (system notifications)</li>
                      <li>✗ All Return Forms (return documentation)</li>
                    </ul>
                  </div>

                  <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
                    <h5 className="font-medium text-green-800 mb-2">What will be preserved:</h5>
                    <ul className="text-sm text-green-700 space-y-1">
                      <li>✓ User accounts and login credentials</li>
                      <li>✓ Email settings and configurations</li>
                      <li>✓ Company branding settings</li>
                      <li>✓ System settings and preferences</li>
                    </ul>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Type "RESET" to confirm permanent data deletion:
                      </label>
                      <input
                        type="text"
                        value={resetConfirmation}
                        onChange={(e) => setResetConfirmation(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                        placeholder="Type RESET to confirm"
                      />
                    </div>

                    <button
                      onClick={resetSystemData}
                      disabled={resetLoading || resetConfirmation !== 'RESET'}
                      className="w-full flex items-center justify-center space-x-2 bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                    >
                      {resetLoading ? (
                        <>
                          <RefreshCw size={16} className="animate-spin" />
                          <span>Resetting System...</span>
                        </>
                      ) : (
                        <>
                          <Trash2 size={16} />
                          <span>RESET ALL DATA</span>
                        </>
                      )}
                    </button>
                  </div>

                  <div className="text-xs text-gray-500 text-center">
                    ⚠️ This action is irreversible. Make sure you have backups if needed.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;