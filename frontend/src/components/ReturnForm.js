import React, { useState } from 'react';
import { FileText, Download, Upload, Signature, User, Building } from 'lucide-react';

const ReturnForm = ({ user }) => {
  const [returnData, setReturnData] = useState({
    // Item Details
    product_code: '',
    product_name: '',
    quantity: '',
    purchase_price: '',
    purchase_currency: 'YER',
    supplier: '',
    reason_for_return: '',
    
    // Signatures & Approvals
    prepared_by_supervisor: user?.full_name || user?.username || '',
    supervisor_signature: '',
    section_manager_name: '',
    section_manager_signature: '',
    department_head_name: '',
    department_head_signature: '',
    finance_signature: '',
    finance_stamp: false,
    
    // Additional Fields
    return_date: new Date().toISOString().split('T')[0],
    reference_number: `RTN-${Date.now()}`,
    notes: ''
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const token = localStorage.getItem('token');
      
      const apiData = {
        ...returnData,
        purchase_price: parseFloat(returnData.purchase_price) || 0,
        quantity: parseInt(returnData.quantity) || 0,
        created_by: user?.username || 'Unknown',
        status: 'pending'
      };

      const response = await fetch(`${BACKEND_URL}/api/returns`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(apiData)
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Return form submitted successfully!' });
        // Reset form
        setReturnData({
          ...returnData,
          product_code: '',
          product_name: '',
          quantity: '',
          purchase_price: '',
          supplier: '',
          reason_for_return: '',
          notes: '',
          reference_number: `RTN-${Date.now()}`
        });
      } else {
        const errorData = await response.json();
        setMessage({ type: 'error', text: errorData.detail || 'Failed to submit return form' });
      }
    } catch (error) {
      console.error('Error submitting return form:', error);
      setMessage({ type: 'error', text: 'Network error occurred' });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setReturnData({
      ...returnData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const exportToPDF = () => {
    // This would generate a PDF of the return form
    console.log('Exporting to PDF:', returnData);
    alert('PDF export functionality will be implemented');
  };

  const exportToExcel = () => {
    // This would generate an Excel file of the return form
    console.log('Exporting to Excel:', returnData);
    alert('Excel export functionality will be implemented');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-500 to-pink-500 text-white p-4 md:p-6 rounded-xl">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
          <div className="text-center lg:text-left">
            <h1 className="text-2xl md:text-3xl font-bold">Return Form</h1>
            <p className="text-red-100 text-sm md:text-base">Digital return form with approvals and signatures</p>
          </div>
          
          <div className="flex space-x-3 mt-4 lg:mt-0">
            <button
              onClick={exportToPDF}
              className="flex items-center space-x-2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <FileText size={16} />
              <span>Export PDF</span>
            </button>
            
            <button
              onClick={exportToExcel}
              className="flex items-center space-x-2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Download size={16} />
              <span>Export Excel</span>
            </button>
          </div>
        </div>
      </div>

      {/* Return Form */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="mb-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-pink-500 rounded-full flex items-center justify-center">
              <FileText size={24} className="text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800">Geant Hypermarket</h2>
              <p className="text-gray-600">Product Return Form</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Reference Number:</span> {returnData.reference_number}
            </div>
            <div>
              <span className="font-medium">Date:</span> {returnData.return_date}
            </div>
          </div>
        </div>

        {message.text && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Item Details Section */}
          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <Upload size={20} className="mr-2" />
              Item Details
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product Code *</label>
                <input
                  type="text"
                  name="product_code"
                  value={returnData.product_code}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Enter product code"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product Name *</label>
                <input
                  type="text"
                  name="product_name"
                  value={returnData.product_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Enter product name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label>
                <input
                  type="number"
                  name="quantity"
                  value={returnData.quantity}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Price</label>
                <div className="flex space-x-2">
                  <input
                    type="number"
                    step="0.01"
                    name="purchase_price"
                    value={returnData.purchase_price}
                    onChange={handleChange}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    placeholder="0.00"
                  />
                  <select
                    name="purchase_currency"
                    value={returnData.purchase_currency}
                    onChange={handleChange}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  >
                    <option value="YER">YER</option>
                    <option value="SAR">SAR</option>
                    <option value="EUR">EUR</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Supplier</label>
                <input
                  type="text"
                  name="supplier"
                  value={returnData.supplier}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Enter supplier name"
                />
              </div>

              <div className="md:col-span-2 lg:col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">Reason for Return *</label>
                <textarea
                  name="reason_for_return"
                  value={returnData.reason_for_return}
                  onChange={handleChange}
                  required
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Explain the reason for returning this item"
                />
              </div>
            </div>
          </div>

          {/* Signatures & Approvals Section */}
          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <Signature size={20} className="mr-2" />
              Signatures & Approvals
            </h3>
            
            <div className="space-y-6">
              {/* Prepared by Supervisor */}
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-medium text-gray-800 mb-3 flex items-center">
                  <User size={16} className="mr-2" />
                  Prepared by Supervisor
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      name="prepared_by_supervisor"
                      value={returnData.prepared_by_supervisor}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      placeholder="Supervisor name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Signature</label>
                    <input
                      type="text"
                      name="supervisor_signature"
                      value={returnData.supervisor_signature}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      placeholder="Digital signature or initials"
                    />
                  </div>
                </div>
              </div>

              {/* Reviewed & Approved by Section Manager */}
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-medium text-gray-800 mb-3 flex items-center">
                  <User size={16} className="mr-2" />
                  Reviewed & Approved by Section Manager
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      name="section_manager_name"
                      value={returnData.section_manager_name}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      placeholder="Section manager name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Signature</label>
                    <input
                      type="text"
                      name="section_manager_signature"
                      value={returnData.section_manager_signature}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      placeholder="Digital signature or initials"
                    />
                  </div>
                </div>
              </div>

              {/* Approved by Department Head */}
              <div className="border-l-4 border-purple-500 pl-4">
                <h4 className="font-medium text-gray-800 mb-3 flex items-center">
                  <User size={16} className="mr-2" />
                  Approved by Department Head
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      name="department_head_name"
                      value={returnData.department_head_name}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      placeholder="Department head name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Signature</label>
                    <input
                      type="text"
                      name="department_head_signature"
                      value={returnData.department_head_signature}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      placeholder="Digital signature or initials"
                    />
                  </div>
                </div>
              </div>

              {/* Finance Department */}
              <div className="border-l-4 border-yellow-500 pl-4">
                <h4 className="font-medium text-gray-800 mb-3 flex items-center">
                  <Building size={16} className="mr-2" />
                  Finance Department
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Signature</label>
                    <input
                      type="text"
                      name="finance_signature"
                      value={returnData.finance_signature}
                      onChange={handleChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      placeholder="Finance signature"
                    />
                  </div>
                  <div className="flex items-center space-x-2 pt-7">
                    <input
                      type="checkbox"
                      name="finance_stamp"
                      checked={returnData.finance_stamp}
                      onChange={handleChange}
                      className="w-4 h-4 text-red-600 bg-gray-100 border-gray-300 rounded focus:ring-red-500"
                    />
                    <label className="text-sm font-medium text-gray-700">Official Stamp Applied</label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Additional Notes */}
          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Additional Notes</h3>
            <textarea
              name="notes"
              value={returnData.notes}
              onChange={handleChange}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="Any additional notes or comments"
            />
          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => setReturnData({
                ...returnData,
                product_code: '',
                product_name: '',
                quantity: '',
                purchase_price: '',
                supplier: '',
                reason_for_return: '',
                notes: '',
                reference_number: `RTN-${Date.now()}`
              })}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Clear Form
            </button>
            
            <button
              type="submit"
              disabled={loading}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                loading
                  ? 'bg-gray-400 cursor-not-allowed text-white'
                  : 'bg-red-500 hover:bg-red-600 text-white'
              }`}
            >
              {loading ? 'Submitting...' : 'Submit Return Form'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ReturnForm;