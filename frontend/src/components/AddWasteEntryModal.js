import React, { useState } from 'react';
import { X, Trash2, AlertTriangle, Package } from 'lucide-react';

const AddWasteEntryModal = ({ isOpen, onClose, product, onWasteAdded }) => {
  const [formData, setFormData] = useState({
    quantity_wasted: '',
    waste_reason: 'damaged',
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const wasteReasons = [
    { value: 'damaged', label: 'Damaged', icon: '💥' },
    { value: 'expired', label: 'Expired', icon: '⏰' },
    { value: 'unsellable', label: 'Unsellable', icon: '❌' },
    { value: 'contaminated', label: 'Contaminated', icon: '🦠' },
    { value: 'broken_packaging', label: 'Broken Packaging', icon: '📦' },
    { value: 'quality_issue', label: 'Quality Issue', icon: '⚠️' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const wasteData = {
        product_id: product.id,
        quantity_wasted: parseInt(formData.quantity_wasted),
        waste_reason: formData.waste_reason,
        notes: formData.notes
      };

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/waste/entries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(wasteData)
      });

      if (response.ok) {
        const result = await response.json();
        setSuccess('Waste entry created successfully!');
        
        // Reset form
        setFormData({
          quantity_wasted: '',
          waste_reason: 'damaged',
          notes: ''
        });

        // Call callback to refresh data
        if (onWasteAdded) {
          onWasteAdded();
        }

        // Close modal after short delay
        setTimeout(() => {
          onClose();
          setSuccess('');
        }, 2000);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create waste entry');
      }
    } catch (error) {
      console.error('Error creating waste entry:', error);
      setError('Failed to create waste entry. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const calculateWasteValue = () => {
    if (!formData.quantity_wasted || !product.purchase_price) return 0;
    return parseInt(formData.quantity_wasted) * parseFloat(product.purchase_price);
  };

  if (!isOpen || !product) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="bg-red-100 p-2 rounded-full">
              <Trash2 size={20} className="text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Add Waste Entry</h2>
              <p className="text-sm text-gray-600">Report damaged or unsellable product</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        {/* Product Info */}
        <div className="p-4 bg-gray-50 border-b">
          <div className="flex items-center space-x-3">
            <Package size={16} className="text-gray-500" />
            <div>
              <p className="font-medium text-gray-900">{product.product_name}</p>
              <p className="text-sm text-gray-600">
                {product.department} • {product.section}
              </p>
              <p className="text-sm text-gray-600">
                Purchase Price: {product.purchase_price} {product.purchase_currency}
              </p>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <AlertTriangle size={16} />
                <span>{error}</span>
              </div>
            </div>
          )}

          {success && (
            <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <Package size={16} />
                <span>{success}</span>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {/* Quantity Wasted */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quantity Wasted *
              </label>
              <input
                type="number"
                min="1"
                max={product.quantity || 1000}
                value={formData.quantity_wasted}
                onChange={(e) => setFormData(prev => ({ ...prev, quantity_wasted: e.target.value }))}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="Enter quantity"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Available quantity: {product.quantity || 0}
              </p>
            </div>

            {/* Waste Reason */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Waste Reason *
              </label>
              <select
                value={formData.waste_reason}
                onChange={(e) => setFormData(prev => ({ ...prev, waste_reason: e.target.value }))}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                required
              >
                {wasteReasons.map(reason => (
                  <option key={reason.value} value={reason.value}>
                    {reason.icon} {reason.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes (Optional)
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                rows="3"
                placeholder="Additional details about the waste..."
              />
            </div>

            {/* Waste Value Calculation */}
            {formData.quantity_wasted && (
              <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-red-800">
                    Estimated Waste Value:
                  </span>
                  <span className="text-lg font-bold text-red-900">
                    {calculateWasteValue().toLocaleString()} {product.purchase_currency}
                  </span>
                </div>
                <p className="text-xs text-red-600 mt-1">
                  {formData.quantity_wasted} × {product.purchase_price} {product.purchase_currency}
                </p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !formData.quantity_wasted}
              className="flex-1 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Creating...</span>
                </>
              ) : (
                <>
                  <Trash2 size={16} />
                  <span>Add Waste Entry</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddWasteEntryModal;