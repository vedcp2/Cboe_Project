import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

interface TableInfo {
  name: string;
  database: string;
  schema: string;
  kind: string;
  comment: string | null;
  row_count: number;
}

interface TableData {
  columns: string[];
  rows: any[][];
}

interface ChartDataPoint {
  x: string | number;
  y: number;
}

interface ChartRequest {
  table_name: string;
  x_column: string;
  y_column: string;
  date_range: [string, string];
}

const ChartConsolePage: React.FC = () => {
  // Core state
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Chart configuration
  const [yAxisColumn, setYAxisColumn] = useState<string>('');
  const [chartType, setChartType] = useState<'line' | 'bar'>('line');
  const [dateRange, setDateRange] = useState<[string, string]>(['', '']);

  // Computed values
  const [dateColumn, setDateColumn] = useState<string>('');
  const [availableDateRange, setAvailableDateRange] = useState<[string, string]>(['', '']);

  // Check if a column is a date column
  const checkIfDateColumn = (columnName: string): boolean => {
    const lowerColumn = columnName.toLowerCase();
    return lowerColumn.includes('date') || 
           lowerColumn.includes('time') || 
           /^\d{4}-\d{2}-\d{2}$/.test(columnName) ||
           /^\d{2}-\d{2}-\d{4}$/.test(columnName) ||
           /^\d{2}\/\d{2}\/\d{4}$/.test(columnName);
  };

  // Helper for formatting values in tooltips and axis
  const formatValue = (value: any) => {
    if (typeof value === 'number' && isFinite(value)) {
      return value.toFixed(2);
    }
    if (value instanceof Date) {
      return value.toLocaleString();
    }
    return value;
  };

  // Helper to format date for HTML date inputs (YYYY-MM-DD)
  const formatDateForInput = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Helper to format date for display (MM-DD-YYYY)
  const formatDateForDisplay = (dateStr: string): string => {
    if (!dateStr) return dateStr;
    
    try {
      const date = new Date(dateStr);
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const year = date.getFullYear();
      return `${month}-${day}-${year}`;
    } catch (error) {
      return dateStr;
    }
  };

  // Fetch actual date range from backend
  const fetchDateRange = async (tableName: string, dateCol: string): Promise<[string, string]> => {
    try {
      const response = await fetch(`http://localhost:8000/table-date-range?table_name=${encodeURIComponent(tableName)}&date_column=${encodeURIComponent(dateCol)}`);
      if (response.ok) {
        const data = await response.json();
        return [data.min_date || '', data.max_date || ''];
      }
    } catch (error) {
      console.error('Error fetching date range:', error);
    }
    return ['', ''];
  };

  // Load available tables
  const loadTables = async () => {
    try {
      const response = await fetch('http://localhost:8000/list-tables');
      if (response.ok) {
        const data = await response.json();
        setTables(data.tables || []);
      }
    } catch (error) {
      console.error('Error loading tables:', error);
    }
  };

  // Load table data and detect date column
  const loadTableData = async (tableName: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/table-preview?table_name=${encodeURIComponent(tableName)}`);
      if (response.ok) {
        const data = await response.json();
        const columns = data.columns || [];
        const rows = data.rows || [];
        
        setTableData({ columns, rows });

        // Auto-detect date column for X-axis
        const dateCol = columns.find((col: string) => checkIfDateColumn(col));
        if (dateCol) {
          setDateColumn(dateCol);
          // Fetch date range for this column
          const [minDate, maxDate] = await fetchDateRange(tableName, dateCol);
          if (minDate && maxDate) {
            setAvailableDateRange([minDate, maxDate]);
            setDateRange([minDate, maxDate]);
          }
        } else {
          setDateColumn('');
          setAvailableDateRange(['', '']);
          setDateRange(['', '']);
        }
      }
    } catch (error) {
      console.error('Error loading table data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch chart data
  const fetchChartData = async () => {
    // Validation
    if (!selectedTable || !dateColumn || !yAxisColumn || !dateRange[0] || !dateRange[1]) {
      setChartData([]);
      return;
    }
    
    setIsLoading(true);
    try {
      const request: ChartRequest = {
        table_name: selectedTable,
        x_column: dateColumn,
        y_column: yAxisColumn,
        date_range: dateRange
      };
      
      const response = await fetch('http://localhost:8000/chart-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      
      if (response.ok) {
        const data = await response.json();
        setChartData(data.chart_data || []);
      } else {
        console.error('Error fetching chart data');
        setChartData([]);
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
      setChartData([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Effects
  useEffect(() => {
    loadTables();
  }, []);

  useEffect(() => {
    if (selectedTable) {
      loadTableData(selectedTable);
    } else {
      setTableData(null);
      setDateColumn('');
      setYAxisColumn('');
      setChartData([]);
      setDateRange(['', '']);
      setAvailableDateRange(['', '']);
    }
  }, [selectedTable]);

  useEffect(() => {
    fetchChartData();
  }, [selectedTable, dateColumn, yAxisColumn, dateRange]);

  // Render chart
  const renderChart = () => {
    if (!chartData.length) {
      return (
        <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
          <div className="text-center">
            <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p className="text-gray-500">Select Y-axis to display chart</p>
          </div>
        </div>
      );
    }

    // Calculate Y-axis domain with padding
    const yValues = chartData.map(point => point.y).filter(y => !isNaN(y) && isFinite(y));
    let yDomain: [number, number] | undefined = undefined;
    
    if (yValues.length > 0) {
      const minY = Math.min(...yValues);
      const maxY = Math.max(...yValues);
      const range = maxY - minY;
      
      // Add 5% padding above and below
      const padding = range * 0.05;
      const paddedMin = minY - padding;
      const paddedMax = maxY + padding;
      
      // Ensure we don't go below 0 for positive-only data
      const finalMin = minY >= 0 ? Math.max(0, paddedMin) : paddedMin;
      
      yDomain = [finalMin, paddedMax];
    }

    const commonProps = {
      data: chartData,
      margin: { top: 20, right: 30, left: 30, bottom: 40 }
    };

    if (chartType === 'line') {
      return (
        <LineChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="x" 
            stroke="#6b7280"
            fontSize={12}
            tick={{ fill: '#6b7280' }}
            label={{ 
              value: dateColumn, 
              position: 'bottom', 
              offset: 0,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 14, fontWeight: 500 }
            }}
          />
          <YAxis 
            domain={yDomain}
            stroke="#6b7280"
            fontSize={12}
            tick={{ fill: '#6b7280' }}
            tickFormatter={formatValue}
            label={{ 
              value: yAxisColumn, 
              angle: -90, 
              position: 'left',
              offset: 0,
              style: { textAnchor: 'middle', fill: '#374151', fontSize: 14, fontWeight: 500 }
            }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
            formatter={(value: any) => [formatValue(value), yAxisColumn]}
            labelFormatter={(label) => `${dateColumn}: ${label}`}
          />
          <Line 
            type="monotone" 
            dataKey="y" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
          />
        </LineChart>
      );
    }

    return (
      <BarChart {...commonProps}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis 
          dataKey="x" 
          stroke="#6b7280"
          fontSize={12}
          tick={{ fill: '#6b7280' }}
          label={{ 
            value: dateColumn, 
            position: 'bottom', 
            offset: 0,
            style: { textAnchor: 'middle', fill: '#374151', fontSize: 14, fontWeight: 500 }
          }}
        />
        <YAxis 
          domain={yDomain}
          stroke="#6b7280"
          fontSize={12}
          tick={{ fill: '#6b7280' }}
          tickFormatter={formatValue}
          label={{ 
            value: yAxisColumn, 
            angle: -90, 
            position: 'left',
            offset: 0,
            style: { textAnchor: 'middle', fill: '#374151', fontSize: 14, fontWeight: 500 }
          }}
        />
        <Tooltip 
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
          formatter={(value: any) => [formatValue(value), yAxisColumn]}
          labelFormatter={(label) => `${dateColumn}: ${label}`}
        />
        <Bar 
          dataKey="y" 
          fill="#3b82f6"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    );
  };

  // Validation
  const canRenderChart = selectedTable && dateColumn && yAxisColumn && dateRange[0] && dateRange[1] && 
    availableDateRange[0] && availableDateRange[1] &&
    dateRange[0] >= availableDateRange[0] && dateRange[1] <= availableDateRange[1] &&
    dateRange[0] <= dateRange[1];

  // Get validation message
  const getValidationMessage = (): string => {
    if (!selectedTable) return 'Please select a dataset';
    if (!dateColumn) return 'No date column found in dataset';
    if (!yAxisColumn) return 'Please select a Y-axis column';
    if (!dateRange[0] || !dateRange[1]) return 'Please select start and end dates';
    if (!availableDateRange[0] || !availableDateRange[1]) return 'Loading available date range...';
    if (dateRange[0] < availableDateRange[0] || dateRange[1] > availableDateRange[1]) {
      return 'Selected dates must be within the available range';
    }
    if (dateRange[0] > dateRange[1]) {
      return 'Start date must be before or equal to end date';
    }
    return 'Chart is ready to display';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 relative">
      {/* Background Pattern */}
      <div 
        className="absolute inset-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px'
        }}
      ></div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 z-10">
        {/* Header Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl shadow-2xl mb-6">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">
            Data Analytics
          </h1>
          <p className="text-xl text-blue-100 max-w-3xl mx-auto leading-relaxed">
            Visualize and explore data to uncover trends and insights with ease
          </p>
          <div className="mt-4 flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-blue-200">Real-time Market Insights</span>
          </div>
        </div>

        {/* Chart Console Card */}
        <div className="relative">
          <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
            <div className="bg-gradient-to-r from-slate-50 to-blue-50 px-8 py-6 border-b border-slate-200">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
                <h2 className="text-xl font-semibold text-slate-800">Chart Builder</h2>
                <span className="text-sm text-slate-600">Interactive Analytics</span>
              </div>
            </div>

            <div className="px-8 py-6">
              {/* Dataset Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Market Dataset
                </label>
                <select
                  value={selectedTable}
                  onChange={(e) => setSelectedTable(e.target.value)}
                  className="w-full h-10 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white bg-no-repeat bg-right pr-10"
                  style={{
                    backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e")`,
                    backgroundPosition: 'right 0.5rem center',
                    backgroundSize: '1.5em 1.5em'
                  }}
                >
                  <option value="">Select a market dataset...</option>
                  {tables.map((table, index) => (
                    <option key={index} value={table.name}>
                      {table.name} ({table.row_count.toLocaleString()} rows)
                    </option>
                  ))}
                </select>
              </div>

              {/* Chart Configuration */}
              {selectedTable && tableData && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  {/* X-Axis (Auto-detected) */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      X-Axis (Date Column)
                    </label>
                    <div className="w-full h-10 px-3 py-2 bg-slate-100 border border-slate-300 rounded-lg text-slate-600 flex items-center">
                      {dateColumn || 'No date column found'}
                    </div>
                  </div>

                  {/* Y-Axis Selection */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Y-Axis
                    </label>
                    <select
                      value={yAxisColumn}
                      onChange={(e) => setYAxisColumn(e.target.value)}
                      className="w-full h-10 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white bg-no-repeat bg-right pr-10"
                      style={{
                        backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e")`,
                        backgroundPosition: 'right 0.5rem center',
                        backgroundSize: '1.5em 1.5em'
                      }}
                    >
                      <option value="">Select Y-axis...</option>
                      {tableData.columns
                        .filter(col => col !== dateColumn)
                        .map((column, index) => (
                          <option key={index} value={column}>
                            {column}
                          </option>
                        ))}
                    </select>
                  </div>

                  {/* Chart Type */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Chart Type
                    </label>
                    <select
                      value={chartType}
                      onChange={(e) => setChartType(e.target.value as 'line' | 'bar')}
                      className="w-full h-10 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white bg-no-repeat bg-right pr-10"
                      style={{
                        backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e")`,
                        backgroundPosition: 'right 0.5rem center',
                        backgroundSize: '1.5em 1.5em'
                      }}
                    >
                      <option value="line">Line Chart</option>
                      <option value="bar">Bar Chart</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Date Range Selection */}
              {selectedTable && tableData && dateColumn && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Date Range
                  </label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">Available Range</label>
                      <div className="w-full h-10 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700 flex items-center">
                        {availableDateRange[0] && availableDateRange[1] 
                          ? `${formatDateForDisplay(availableDateRange[0])} to ${formatDateForDisplay(availableDateRange[1])}`
                          : 'No date range available'
                        }
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">Start Date</label>
                      <input
                        type="date"
                        value={dateRange[0]}
                        onChange={(e) => setDateRange([e.target.value, dateRange[1]])}
                        min={availableDateRange[0]}
                        max={availableDateRange[1]}
                        className="w-full h-10 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">End Date</label>
                      <input
                        type="date"
                        value={dateRange[1]}
                        onChange={(e) => setDateRange([dateRange[0], e.target.value])}
                        min={availableDateRange[0]}
                        max={availableDateRange[1]}
                        className="w-full h-10 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Validation Status */}
              {selectedTable && tableData && (
                <div className={`p-4 rounded-lg mb-6 ${
                  canRenderChart 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-yellow-50 border border-yellow-200'
                }`}>
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      canRenderChart ? 'bg-green-500' : 'bg-yellow-500'
                    }`}></div>
                    <div className="text-sm">
                      {getValidationMessage()}
                    </div>
                  </div>
                </div>
              )}

              {/* Data Info */}
              {tableData && (
                <div className="p-4 bg-blue-50 rounded-lg mb-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-slate-500">Dataset:</span>
                      <span className="ml-2 font-medium text-slate-900">
                        {selectedTable}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Columns:</span>
                      <span className="ml-2 font-medium text-slate-900">{tableData.columns.length}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Preview Rows:</span>
                      <span className="ml-2 font-medium text-slate-900">{tableData.rows.length}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Chart Type:</span>
                      <span className="ml-2 font-medium text-slate-900">
                        {chartType}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Chart Section */}
            <div className="p-8">
              {isLoading ? (
                <div className="flex items-center justify-center h-96">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="h-96 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    {renderChart()}
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
          
          {/* Decorative Elements */}
        </div>

        {/* Footer */}
        <div className="text-center mt-12">
          <p className="text-sm text-blue-200">
            © 2025 Ved Patel, Inc.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChartConsolePage; 