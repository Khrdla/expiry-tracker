import React, { useRef, useMemo, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text, Box, Sphere, Cylinder } from '@react-three/drei';
import { BarChart3, PieChart, TrendingUp, Package } from 'lucide-react';

// 3D Bar Chart Component
const Bar3D = ({ position, height, color, label, value, maxValue }) => {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);
  
  // Calculate relative height (max 4 units)
  const relativeHeight = (height / maxValue) * 4;
  
  return (
    <group position={position}>
      <Box
        ref={meshRef}
        args={[0.8, relativeHeight, 0.8]}
        position={[0, relativeHeight / 2, 0]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial 
          color={hovered ? '#ffffff' : color} 
          transparent 
          opacity={hovered ? 0.9 : 0.8}
          metalness={0.3}
          roughness={0.4}
        />
      </Box>
      {/* Label */}
      <Text
        position={[0, -0.5, 0]}
        fontSize={0.3}
        color="#333"
        anchorX="center"
        anchorY="middle"
      >
        {label}
      </Text>
      {/* Value display when hovered */}
      {hovered && (
        <Text
          position={[0, relativeHeight + 0.5, 0]}
          fontSize={0.25}
          color="#000"
          anchorX="center"
          anchorY="middle"
        >
          {value.toLocaleString()}
        </Text>
      )}
    </group>
  );
};

// 3D Pie Slice Component
const PieSlice3D = ({ 
  position, 
  radius, 
  startAngle, 
  endAngle, 
  color, 
  label, 
  value, 
  percentage 
}) => {
  const [hovered, setHovered] = useState(false);
  
  // Calculate slice geometry
  const midAngle = (startAngle + endAngle) / 2;
  const labelRadius = radius + 1;
  const labelX = Math.cos(midAngle) * labelRadius;
  const labelZ = Math.sin(midAngle) * labelRadius;
  
  return (
    <group position={position}>
      {/* Create pie slice using cylinder with custom geometry */}
      <Cylinder
        args={[radius, radius, 0.2, 32, 1, false, startAngle, endAngle - startAngle]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        position={hovered ? [0, 0.1, 0] : [0, 0, 0]}
      >
        <meshStandardMaterial 
          color={hovered ? '#ffffff' : color}
          transparent
          opacity={hovered ? 0.9 : 0.8}
          metalness={0.3}
          roughness={0.4}
        />
      </Cylinder>
      
      {/* Label */}
      <Text
        position={[labelX, 0.5, labelZ]}
        fontSize={0.2}
        color="#333"
        anchorX="center"
        anchorY="middle"
      >
        {label}
      </Text>
      
      {/* Value display when hovered */}
      {hovered && (
        <Text
          position={[0, 0.8, 0]}
          fontSize={0.18}
          color="#000"
          anchorX="center"
          anchorY="middle"
        >
          {`${value.toLocaleString()} (${percentage}%)`}
        </Text>
      )}
    </group>
  );
};

// 3D Stock Levels Component
const StockLevels3D = ({ data }) => {
  const maxValue = Math.max(...data.map(item => item.total_items));
  
  return (
    <Canvas camera={{ position: [5, 5, 5], fov: 60 }}>
      <ambientLight intensity={0.6} />
      <pointLight position={[10, 10, 10]} intensity={0.8} />
      <pointLight position={[-10, -10, -10]} intensity={0.4} />
      
      {data.map((item, index) => (
        <Bar3D
          key={index}
          position={[(index - 1) * 2, 0, 0]}
          height={item.total_items}
          maxValue={maxValue}
          color={item.color}
          label={item.department}
          value={item.total_items}
        />
      ))}
      
      <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />
    </Canvas>
  );
};

// 3D Waste Distribution Component
const WasteDistribution3D = ({ data }) => {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  let currentAngle = 0;
  
  const slices = data.map((item, index) => {
    const percentage = ((item.value / total) * 100).toFixed(1);
    const startAngle = currentAngle;
    const sliceAngle = (item.value / total) * Math.PI * 2;
    currentAngle += sliceAngle;
    
    return {
      ...item,
      startAngle,
      endAngle: currentAngle,
      percentage
    };
  });
  
  return (
    <Canvas camera={{ position: [0, 6, 6], fov: 60 }}>
      <ambientLight intensity={0.6} />
      <pointLight position={[10, 10, 10]} intensity={0.8} />
      <pointLight position={[-10, -10, -10]} intensity={0.4} />
      
      {slices.map((slice, index) => (
        <PieSlice3D
          key={index}
          position={[0, 0, 0]}
          radius={2}
          startAngle={slice.startAngle}
          endAngle={slice.endAngle}
          color={slice.color}
          label={slice.currency}
          value={slice.value}
          percentage={slice.percentage}
        />
      ))}
      
      <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />
    </Canvas>
  );
};

// 3D Department Breakdown Component
const DepartmentBreakdown3D = ({ data }) => {
  const [activeMetric, setActiveMetric] = useState('stock_value');
  
  const metrics = {
    stock_value: 'Stock Value',
    total_items: 'Total Items',
    out_of_stock: 'Out of Stock',
    low_stock: 'Low Stock'
  };
  
  const maxValue = Math.max(...data.map(item => item[activeMetric] || 0));
  
  return (
    <div className="relative">
      {/* Metric Selector */}
      <div className="absolute top-4 left-4 z-10 bg-white bg-opacity-90 rounded-lg p-2">
        <select
          value={activeMetric}
          onChange={(e) => setActiveMetric(e.target.value)}
          className="text-sm border rounded px-2 py-1"
        >
          {Object.entries(metrics).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
      </div>
      
      <Canvas camera={{ position: [6, 6, 6], fov: 60 }}>
        <ambientLight intensity={0.6} />
        <pointLight position={[10, 10, 10]} intensity={0.8} />
        <pointLight position={[-10, -10, -10]} intensity={0.4} />
        
        {data.map((item, index) => (
          <Bar3D
            key={index}
            position={[(index - 1) * 2.5, 0, 0]}
            height={item[activeMetric] || 0}
            maxValue={maxValue || 1}
            color={item.color}
            label={item.department}
            value={item[activeMetric] || 0}
          />
        ))}
        
        <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />
      </Canvas>
    </div>
  );
};

// Main 3D Charts Container Component
const Dashboard3DCharts = ({ dashboardData, wasteData }) => {
  const [activeChart, setActiveChart] = useState('stock');
  
  // Prepare data for 3D charts
  const stockData = useMemo(() => {
    if (!dashboardData?.kpis) return [];
    
    return dashboardData.kpis.map(kpi => ({
      department: kpi.department.replace('01-', ''),
      total_items: kpi.total_items,
      stock_value: kpi.total_stock_value,
      out_of_stock: kpi.out_of_stock_items,
      low_stock: kpi.low_stock_items,
      color: kpi.department === '01-FMG' ? '#22c55e' : 
             kpi.department === '01-CGD' ? '#3b82f6' : '#8b5cf6'
    }));
  }, [dashboardData]);
  
  const wasteChartData = useMemo(() => {
    if (!wasteData?.currency_totals) return [];
    
    const colors = { YER: '#22c55e', SAR: '#3b82f6', EUR: '#f59e0b' };
    
    return Object.entries(wasteData.currency_totals)
      .filter(([_, value]) => value > 0)
      .map(([currency, value]) => ({
        currency,
        value,
        color: colors[currency] || '#6b7280'
      }));
  }, [wasteData]);
  
  const chartTypes = {
    stock: { component: StockLevels3D, data: stockData, title: '3D Stock Levels', icon: Package },
    waste: { component: WasteDistribution3D, data: wasteChartData, title: '3D Waste Distribution', icon: PieChart },
    department: { component: DepartmentBreakdown3D, data: stockData, title: '3D Department Breakdown', icon: BarChart3 }
  };
  
  const ActiveComponent = chartTypes[activeChart].component;
  const activeData = chartTypes[activeChart].data;
  
  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-white bg-opacity-20 p-2 rounded-full">
              <TrendingUp size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold">📊 Enhanced 3D Analytics</h2>
              <p className="text-purple-100 text-sm">Interactive 3D data visualization</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Chart Selector */}
      <div className="bg-gray-50 border-b p-4">
        <div className="flex flex-wrap gap-2">
          {Object.entries(chartTypes).map(([key, { title, icon: Icon }]) => (
            <button
              key={key}
              onClick={() => setActiveChart(key)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeChart === key 
                  ? 'bg-purple-500 text-white' 
                  : 'bg-white text-gray-700 hover:bg-purple-50 border'
              }`}
            >
              <Icon size={16} />
              <span>{title}</span>
            </button>
          ))}
        </div>
      </div>
      
      {/* 3D Chart Container */}
      <div className="relative" style={{ height: '400px' }}>
        {activeData.length > 0 ? (
          <ActiveComponent data={activeData} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <TrendingUp size={48} className="mx-auto mb-4 opacity-30" />
              <p className="text-lg font-medium">No Data Available</p>
              <p className="text-sm">Data will appear when available</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Instructions */}
      <div className="bg-blue-50 border-t p-3">
        <p className="text-blue-700 text-sm flex items-center">
          <TrendingUp size={16} className="mr-2" />
          <strong>Interactive 3D Charts:</strong> Click and drag to rotate • Scroll to zoom • Right-click to pan
        </p>
      </div>
    </div>
  );
};

export default Dashboard3DCharts;