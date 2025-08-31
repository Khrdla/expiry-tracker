import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  ScrollView,
  Alert,
  ActivityIndicator,
  Dimensions
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import Constants from 'expo-constants';
import { LineChart, BarChart, PieChart } from 'react-native-chart-kit';
import ViewShot from 'react-native-view-shot';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';

const API_BASE_URL = Constants.expoConfig?.extra?.EXPO_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;
const screenWidth = Dimensions.get('window').width;

interface AnalyticsData {
  totalItems: number;
  expiringSoon: number;
  expired: number;
  supplierData: any[];
  sectionData: any[];
}

export default function Reports() {
  const [loading, setLoading] = useState(true);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [generatingPDF, setGeneratingPDF] = useState(false);
  const router = useRouter();
  const viewShotRef = useRef<ViewShot>(null);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const [alertsResponse, supplierResponse, sectionResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/analytics/expiry-alerts`),
        fetch(`${API_BASE_URL}/api/analytics/by-supplier`),
        fetch(`${API_BASE_URL}/api/analytics/by-section`)
      ]);

      if (alertsResponse.ok && supplierResponse.ok && sectionResponse.ok) {
        const alerts = await alertsResponse.json();
        const suppliers = await supplierResponse.json();
        const sections = await sectionResponse.json();

        setAnalyticsData({
          totalItems: alerts.total_items,
          expiringSoon: alerts.expiring_soon,
          expired: alerts.expired,
          supplierData: suppliers.suppliers || [],
          sectionData: sections.sections || []
        });
      } else {
        throw new Error('Failed to load analytics data');
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
      Alert.alert('Error', 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const generatePDFReport = async () => {
    try {
      setGeneratingPDF(true);
      
      // Capture the current view as image
      if (viewShotRef.current) {
        const uri = await viewShotRef.current.capture({
          format: 'png',
          quality: 0.8,
        });

        // Create a simple HTML report
        const htmlContent = `
          <!DOCTYPE html>
          <html>
          <head>
            <title>Expiry Tracker Report</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 40px; }
              .header { text-align: center; margin-bottom: 30px; }
              .summary { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
              .stat { display: inline-block; margin: 10px 20px; text-align: center; }
              .stat-number { font-size: 24px; font-weight: bold; color: #3742fa; }
              .stat-label { font-size: 14px; color: #666; }
              .section { margin-bottom: 30px; }
              .section h3 { color: #2f3542; border-bottom: 2px solid #3742fa; padding-bottom: 10px; }
              table { width: 100%; border-collapse: collapse; margin-top: 15px; }
              th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
              th { background-color: #f8f9fa; font-weight: bold; }
              .expired { color: #ff4757; font-weight: bold; }
              .expiring { color: #ffa726; font-weight: bold; }
              .good { color: #2ed573; font-weight: bold; }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>Expiry Tracker Report</h1>
              <p>Generated on ${new Date().toLocaleDateString()}</p>
            </div>
            
            <div class="summary">
              <h2>Executive Summary</h2>
              <div class="stat">
                <div class="stat-number">${analyticsData?.totalItems || 0}</div>
                <div class="stat-label">Total Items</div>
              </div>
              <div class="stat">
                <div class="stat-number expiring">${analyticsData?.expiringSoon || 0}</div>
                <div class="stat-label">Expiring Soon (30 days)</div>
              </div>
              <div class="stat">
                <div class="stat-number expired">${analyticsData?.expired || 0}</div>
                <div class="stat-label">Expired Items</div>
              </div>
            </div>

            <div class="section">
              <h3>Supplier Analysis</h3>
              <table>
                <tr>
                  <th>Supplier</th>
                  <th>Total Items</th>
                  <th>Total Stock</th>
                  <th>Expiring Soon</th>
                  <th>Expired</th>
                </tr>
                ${analyticsData?.supplierData.map(supplier => `
                  <tr>
                    <td>${supplier._id}</td>
                    <td>${supplier.total_items}</td>
                    <td>${supplier.total_stock}</td>
                    <td class="expiring">${supplier.expiring_soon}</td>
                    <td class="expired">${supplier.expired_items}</td>
                  </tr>
                `).join('') || ''}
              </table>
            </div>

            <div class="section">
              <h3>Section Analysis</h3>
              <table>
                <tr>
                  <th>Section</th>
                  <th>Total Items</th>
                  <th>Total Stock</th>
                  <th>Expiring Soon</th>
                  <th>Expired</th>
                </tr>
                ${analyticsData?.sectionData.map(section => `
                  <tr>
                    <td>${section._id}</td>
                    <td>${section.total_items}</td>
                    <td>${section.total_stock}</td>
                    <td class="expiring">${section.expiring_soon}</td>
                    <td class="expired">${section.expired_items}</td>
                  </tr>
                `).join('') || ''}
              </table>
            </div>
          </body>
          </html>
        `;

        // Save HTML file
        const htmlUri = FileSystem.documentDirectory + 'expiry_report.html';
        await FileSystem.writeAsStringAsync(htmlUri, htmlContent);

        // Share the HTML file
        if (await Sharing.isAvailableAsync()) {
          await Sharing.shareAsync(htmlUri, {
            mimeType: 'text/html',
            dialogTitle: 'Share Expiry Report'
          });
        } else {
          Alert.alert('Success', 'Report generated successfully!');
        }
      }
    } catch (error) {
      console.error('Error generating PDF:', error);
      Alert.alert('Error', 'Failed to generate report');
    } finally {
      setGeneratingPDF(false);
    }
  };

  const getChartData = () => {
    if (!analyticsData) return null;

    const pieData = [
      {
        name: 'Good',
        population: Math.max(0, analyticsData.totalItems - analyticsData.expiringSoon - analyticsData.expired),
        color: '#2ed573',
        legendFontColor: '#7F7F7F',
        legendFontSize: 15,
      },
      {
        name: 'Expiring Soon',
        population: analyticsData.expiringSoon,
        color: '#ffa726',
        legendFontColor: '#7F7F7F',
        legendFontSize: 15,
      },
      {
        name: 'Expired',
        population: analyticsData.expired,
        color: '#ff4757',
        legendFontColor: '#7F7F7F',
        legendFontSize: 15,
      },
    ];

    const supplierBarData = {
      labels: analyticsData.supplierData.slice(0, 5).map(s => s._id.substring(0, 8)),
      datasets: [{
        data: analyticsData.supplierData.slice(0, 5).map(s => s.total_items)
      }]
    };

    return { pieData, supplierBarData };
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color="#3742fa" />
          <Text style={styles.loadingText}>Loading analytics...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const chartData = getChartData();

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#2f3542" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Reports & Analytics</Text>
        <TouchableOpacity onPress={generatePDFReport} style={styles.pdfButton}>
          {generatingPDF ? (
            <ActivityIndicator size={20} color="#fff" />
          ) : (
            <Ionicons name="document-text" size={24} color="#fff" />
          )}
        </TouchableOpacity>
      </View>

      <ViewShot ref={viewShotRef} options={{ format: 'png', quality: 0.8 }}>
        <ScrollView style={styles.scrollView}>
          {/* Executive Summary */}
          <View style={styles.summaryCard}>
            <Text style={styles.cardTitle}>Executive Summary</Text>
            <View style={styles.summaryStats}>
              <View style={[styles.summaryItem, { backgroundColor: '#3742fa' }]}>
                <Text style={styles.summaryNumber}>{analyticsData?.totalItems || 0}</Text>
                <Text style={styles.summaryLabel}>Total Items</Text>
              </View>
              <View style={[styles.summaryItem, { backgroundColor: '#ffa726' }]}>
                <Text style={styles.summaryNumber}>{analyticsData?.expiringSoon || 0}</Text>
                <Text style={styles.summaryLabel}>Expiring Soon</Text>
              </View>
              <View style={[styles.summaryItem, { backgroundColor: '#ff4757' }]}>
                <Text style={styles.summaryNumber}>{analyticsData?.expired || 0}</Text>
                <Text style={styles.summaryLabel}>Expired</Text>
              </View>
            </View>
          </View>

          {/* Expiry Status Chart */}
          {chartData && chartData.pieData.some(item => item.population > 0) && (
            <View style={styles.chartCard}>
              <Text style={styles.cardTitle}>Expiry Status Distribution</Text>
              <PieChart
                data={chartData.pieData}
                width={screenWidth - 32}
                height={220}
                chartConfig={{
                  backgroundColor: '#ffffff',
                  backgroundGradientFrom: '#ffffff',
                  backgroundGradientTo: '#ffffff',
                  color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                }}
                accessor="population"
                backgroundColor="transparent"
                paddingLeft="15"
                absolute
              />
            </View>
          )}

          {/* Top Suppliers Chart */}
          {chartData && analyticsData?.supplierData.length > 0 && (
            <View style={styles.chartCard}>
              <Text style={styles.cardTitle}>Top Suppliers by Item Count</Text>
              <BarChart
                data={chartData.supplierBarData}
                width={screenWidth - 32}
                height={220}
                yAxisLabel=""
                yAxisSuffix=""
                chartConfig={{
                  backgroundColor: '#ffffff',
                  backgroundGradientFrom: '#ffffff',
                  backgroundGradientTo: '#ffffff',
                  decimalPlaces: 0,
                  color: (opacity = 1) => `rgba(55, 66, 250, ${opacity})`,
                  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  style: {
                    borderRadius: 16
                  },
                  propsForDots: {
                    r: "6",
                    strokeWidth: "2",
                    stroke: "#3742fa"
                  }
                }}
                style={{
                  marginVertical: 8,
                  borderRadius: 16
                }}
              />
            </View>
          )}

          {/* Supplier Details */}
          <View style={styles.detailCard}>
            <Text style={styles.cardTitle}>Supplier Analysis</Text>
            {analyticsData?.supplierData.map((supplier, index) => (
              <View key={index} style={styles.supplierRow}>
                <View style={styles.supplierInfo}>
                  <Text style={styles.supplierName}>{supplier._id}</Text>
                  <Text style={styles.supplierDetails}>
                    {supplier.total_items} items • {supplier.total_stock} stock
                  </Text>
                </View>
                <View style={styles.supplierStats}>
                  <View style={[styles.statBadge, { backgroundColor: '#ffa726' }]}>
                    <Text style={styles.statText}>{supplier.expiring_soon}</Text>
                  </View>
                  <View style={[styles.statBadge, { backgroundColor: '#ff4757' }]}>
                    <Text style={styles.statText}>{supplier.expired_items}</Text>
                  </View>
                </View>
              </View>
            ))}
          </View>

          {/* Section Details */}
          <View style={styles.detailCard}>
            <Text style={styles.cardTitle}>Section Analysis</Text>
            {analyticsData?.sectionData.map((section, index) => (
              <View key={index} style={styles.supplierRow}>
                <View style={styles.supplierInfo}>
                  <Text style={styles.supplierName}>{section._id}</Text>
                  <Text style={styles.supplierDetails}>
                    {section.total_items} items • {section.total_stock} stock
                  </Text>
                </View>
                <View style={styles.supplierStats}>
                  <View style={[styles.statBadge, { backgroundColor: '#ffa726' }]}>
                    <Text style={styles.statText}>{section.expiring_soon}</Text>
                  </View>
                  <View style={[styles.statBadge, { backgroundColor: '#ff4757' }]}>
                    <Text style={styles.statText}>{section.expired_items}</Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        </ScrollView>
      </ViewShot>
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
  backButton: {
    padding: 5,
  },
  headerTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  pdfButton: {
    padding: 5,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 16,
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  summaryCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2f3542',
    marginBottom: 16,
  },
  summaryStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  summaryItem: {
    flex: 1,
    padding: 16,
    borderRadius: 8,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  summaryNumber: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  summaryLabel: {
    color: '#fff',
    fontSize: 12,
    marginTop: 4,
  },
  chartCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  detailCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  supplierRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  supplierInfo: {
    flex: 1,
  },
  supplierName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2f3542',
  },
  supplierDetails: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  supplierStats: {
    flexDirection: 'row',
  },
  statBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginLeft: 8,
    minWidth: 24,
    alignItems: 'center',
  },
  statText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
});