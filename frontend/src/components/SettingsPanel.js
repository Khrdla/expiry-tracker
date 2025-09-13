import React, { useState, useEffect } from 'react';
import { Save, Clock, Mail, Palette, Bell, Download, Settings, TestTube, AlertCircle, CheckCircle } from 'lucide-react';

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

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchSettings();
  }, []);

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
        setMessage('Email settings saved successfully!');
        setTimeout(() => setMessage(''), 3000);
      } else {
        setMessage('Failed to save email settings');
      }
    } catch (error) {
      setMessage('Error saving email settings');
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

  const tabs = [
    { id: 'email', label: 'Email & Alerts', icon: Mail },
    { id: 'company', label: 'Company Settings', icon: Palette },
    { id: 'reports', label: 'Reports', icon: Download }
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
                    Enable Daily Email Alerts (08:00 AM Aden time)
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

              <div className="flex space-x-4">
                <button
                  onClick={saveEmailSettings}
                  disabled={loading}
                  className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <Save size={16} />
                  <span>{loading ? 'Saving...' : 'Save Settings'}</span>
                </button>

                <button
                  onClick={sendTestAlert}
                  disabled={loading}
                  className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <Bell size={16} />
                  <span>Send Test Alert</span>
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
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;