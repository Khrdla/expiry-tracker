import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  Alert,
  SafeAreaView,
  StatusBar,
  RefreshControl,
  TextInput,
  Modal,
  ScrollView,
  Platform,
  KeyboardAvoidingView
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';

const API_BASE_URL = Constants.expoConfig?.extra?.EXPO_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface InventoryItem {
  id: string;
  department: string;
  section: string;
  supplier_name: string;
  item_code: string;
  barcode: string;
  item_name: string;
  stock_available: number;
  expiry_date: string;
  product_image?: string;
  created_at: string;
  updated_at: string;
}

interface ExpiryAlerts {
  total_items: number;
  expiring_soon: number;
  expired: number;
  items_expiring_soon: InventoryItem[];
  expired_items: InventoryItem[];
}

export default function ExpiryTracker() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [alerts, setAlerts] = useState<ExpiryAlerts | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'expiring' | 'expired'>('all');
  
  // Form state for adding/editing items
  const [formData, setFormData] = useState({
    section: '',
    supplier_name: '',
    item_code: '',
    barcode: '',
    item_name: '',
    stock_available: '',
    expiry_date: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([loadInventoryItems(), loadExpiryAlerts()]);
    } catch (error) {
      console.error('Error loading data:', error);
      Alert.alert('Error', 'Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadInventoryItems = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/inventory`);
      if (response.ok) {
        const data = await response.json();
        setItems(data);
      } else {
        throw new Error('Failed to fetch inventory items');
      }
    } catch (error) {
      console.error('Error loading inventory:', error);
    }
  };

  const loadExpiryAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/analytics/expiry-alerts`);
      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      } else {
        throw new Error('Failed to fetch expiry alerts');
      }
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const addItem = async () => {
    try {
      if (!formData.item_name || !formData.expiry_date || !formData.section) {
        Alert.alert('Error', 'Please fill in all required fields');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/inventory`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          stock_available: parseInt(formData.stock_available) || 0,
        }),
      });

      if (response.ok) {
        Alert.alert('Success', 'Item added successfully');
        setModalVisible(false);
        resetForm();
        await loadData();
      } else {
        throw new Error('Failed to add item');
      }
    } catch (error) {
      console.error('Error adding item:', error);
      Alert.alert('Error', 'Failed to add item. Please try again.');
    }
  };

  const deleteItem = async (itemId: string) => {
    Alert.alert(
      'Confirm Delete',
      'Are you sure you want to delete this item?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await fetch(`${API_BASE_URL}/api/inventory/${itemId}`, {
                method: 'DELETE',
              });

              if (response.ok) {
                Alert.alert('Success', 'Item deleted successfully');
                await loadData();
              } else {
                throw new Error('Failed to delete item');
              }
            } catch (error) {
              console.error('Error deleting item:', error);
              Alert.alert('Error', 'Failed to delete item. Please try again.');
            }
          },
        },
      ]
    );
  };

  const resetForm = () => {
    setFormData({
      section: '',
      supplier_name: '',
      item_code: '',
      barcode: '',
      item_name: '',
      stock_available: '',
      expiry_date: ''
    });
  };

  const getExpiryStatus = (expiryDate: string) => {
    const today = new Date();
    const expiry = new Date(expiryDate);
    const diffTime = expiry.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return { status: 'expired', color: '#ff4757', text: `Expired ${Math.abs(diffDays)} days ago` };
    } else if (diffDays <= 7) {
      return { status: 'expiring', color: '#ffa726', text: `Expires in ${diffDays} days` };
    } else {
      return { status: 'good', color: '#2ed573', text: `${diffDays} days remaining` };
    }
  };

  const getFilteredItems = () => {
    let filtered = items;

    if (searchText) {
      filtered = filtered.filter(item =>
        item.item_name.toLowerCase().includes(searchText.toLowerCase()) ||
        item.supplier_name.toLowerCase().includes(searchText.toLowerCase()) ||
        item.barcode.includes(searchText)
      );
    }

    if (activeTab === 'expiring') {
      filtered = filtered.filter(item => {
        const status = getExpiryStatus(item.expiry_date);
        return status.status === 'expiring';
      });
    } else if (activeTab === 'expired') {
      filtered = filtered.filter(item => {
        const status = getExpiryStatus(item.expiry_date);
        return status.status === 'expired';
      });
    }

    return filtered;
  };

  const renderItem = ({ item }: { item: InventoryItem }) => {
    const expiryStatus = getExpiryStatus(item.expiry_date);

    return (
      <View style={styles.itemCard}>
        <View style={styles.itemHeader}>
          <Text style={styles.itemName}>{item.item_name}</Text>
          <TouchableOpacity
            onPress={() => deleteItem(item.id)}
            style={styles.deleteButton}
          >
            <Ionicons name="trash-outline" size={20} color="#ff4757" />
          </TouchableOpacity>
        </View>
        
        <View style={styles.itemDetails}>
          <Text style={styles.itemText}>Supplier: {item.supplier_name}</Text>
          <Text style={styles.itemText}>Section: {item.section}</Text>
          <Text style={styles.itemText}>Stock: {item.stock_available}</Text>
          <Text style={styles.itemText}>Code: {item.item_code}</Text>
          <Text style={styles.itemText}>Barcode: {item.barcode}</Text>
        </View>

        <View style={[styles.expiryStatus, { backgroundColor: expiryStatus.color }]}>
          <Text style={styles.expiryText}>{expiryStatus.text}</Text>
        </View>
      </View>
    );
  };

  const renderDashboard = () => (
    <View style={styles.dashboard}>
      <Text style={styles.dashboardTitle}>Expiry Dashboard</Text>
      <View style={styles.statsContainer}>
        <View style={[styles.statCard, { backgroundColor: '#3742fa' }]}>
          <Text style={styles.statNumber}>{alerts?.total_items || 0}</Text>
          <Text style={styles.statLabel}>Total Items</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#ffa726' }]}>
          <Text style={styles.statNumber}>{alerts?.expiring_soon || 0}</Text>
          <Text style={styles.statLabel}>Expiring Soon</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#ff4757' }]}>
          <Text style={styles.statNumber}>{alerts?.expired || 0}</Text>
          <Text style={styles.statLabel}>Expired</Text>
        </View>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#2f3542" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Expiry Tracker</Text>
        <TouchableOpacity
          onPress={() => setModalVisible(true)}
          style={styles.addButton}
        >
          <Ionicons name="add" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Dashboard */}
      {renderDashboard()}

      {/* Search */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#666" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search items, suppliers, or barcodes..."
          value={searchText}
          onChangeText={setSearchText}
          placeholderTextColor="#999"
        />
      </View>

      {/* Tabs */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'all' && styles.activeTab]}
          onPress={() => setActiveTab('all')}
        >
          <Text style={[styles.tabText, activeTab === 'all' && styles.activeTabText]}>
            All ({items.length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'expiring' && styles.activeTab]}
          onPress={() => setActiveTab('expiring')}
        >
          <Text style={[styles.tabText, activeTab === 'expiring' && styles.activeTabText]}>
            Expiring ({alerts?.expiring_soon || 0})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'expired' && styles.activeTab]}
          onPress={() => setActiveTab('expired')}
        >
          <Text style={[styles.tabText, activeTab === 'expired' && styles.activeTabText]}>
            Expired ({alerts?.expired || 0})
          </Text>
        </TouchableOpacity>
      </View>

      {/* Items List */}
      <FlatList
        data={getFilteredItems()}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        style={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="archive-outline" size={64} color="#999" />
            <Text style={styles.emptyText}>No items found</Text>
          </View>
        }
      />

      {/* Add Item Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add New Item</Text>
              <TouchableOpacity
                onPress={() => setModalVisible(false)}
                style={styles.closeButton}
              >
                <Ionicons name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.formContainer}>
              <TextInput
                style={styles.input}
                placeholder="Item Name *"
                value={formData.item_name}
                onChangeText={(text) => setFormData({...formData, item_name: text})}
                placeholderTextColor="#999"
              />
              
              <TextInput
                style={styles.input}
                placeholder="Section (e.g., S-10 Beverage) *"
                value={formData.section}
                onChangeText={(text) => setFormData({...formData, section: text})}
                placeholderTextColor="#999"
              />
              
              <TextInput
                style={styles.input}
                placeholder="Supplier Name"
                value={formData.supplier_name}
                onChangeText={(text) => setFormData({...formData, supplier_name: text})}
                placeholderTextColor="#999"
              />
              
              <TextInput
                style={styles.input}
                placeholder="Item Code"
                value={formData.item_code}
                onChangeText={(text) => setFormData({...formData, item_code: text})}
                placeholderTextColor="#999"
              />
              
              <TextInput
                style={styles.input}
                placeholder="Barcode"
                value={formData.barcode}
                onChangeText={(text) => setFormData({...formData, barcode: text})}
                placeholderTextColor="#999"
              />
              
              <TextInput
                style={styles.input}
                placeholder="Stock Available"
                value={formData.stock_available}
                onChangeText={(text) => setFormData({...formData, stock_available: text})}
                keyboardType="numeric"
                placeholderTextColor="#999"
              />
              
              <TextInput
                style={styles.input}
                placeholder="Expiry Date (YYYY-MM-DD) *"
                value={formData.expiry_date}
                onChangeText={(text) => setFormData({...formData, expiry_date: text})}
                placeholderTextColor="#999"
              />

              <TouchableOpacity style={styles.submitButton} onPress={addItem}>
                <Text style={styles.submitButtonText}>Add Item</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f1f2f6',
  },
  header: {
    backgroundColor: '#2f3542',
    paddingHorizontal: 20,
    paddingVertical: 15,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  addButton: {
    backgroundColor: '#3742fa',
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  dashboard: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  dashboardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    color: '#2f3542',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statCard: {
    flex: 1,
    padding: 16,
    borderRadius: 8,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  statNumber: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  statLabel: {
    color: '#fff',
    fontSize: 12,
    marginTop: 4,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginBottom: 16,
    paddingHorizontal: 16,
    borderRadius: 8,
    elevation: 1,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 16,
    color: '#333',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 8,
    elevation: 1,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    backgroundColor: '#3742fa',
    borderRadius: 8,
  },
  tabText: {
    fontSize: 14,
    color: '#666',
  },
  activeTabText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  list: {
    flex: 1,
    paddingHorizontal: 16,
  },
  itemCard: {
    backgroundColor: '#fff',
    marginBottom: 12,
    borderRadius: 8,
    padding: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  itemName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2f3542',
    flex: 1,
  },
  deleteButton: {
    padding: 4,
  },
  itemDetails: {
    marginBottom: 12,
  },
  itemText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  expiryStatus: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    alignSelf: 'flex-start',
  },
  expiryText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    marginTop: 16,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2f3542',
  },
  closeButton: {
    padding: 4,
  },
  formContainer: {
    padding: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    marginBottom: 16,
    backgroundColor: '#fff',
    color: '#333',
  },
  submitButton: {
    backgroundColor: '#3742fa',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});