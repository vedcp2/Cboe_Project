import React, { useState, useEffect } from 'react';

interface TableInfo {
  name: string;
  database: string;
  schema: string;
  kind: string;
  comment?: string;
  row_count: number;
}

interface TableData {
  columns: string[];
  rows: any[][];
}

interface TableDisplayProps {
  tables: TableInfo[];
  isLoading: boolean;
  onRefresh: () => void;
}

const TableDisplay: React.FC<TableDisplayProps> = ({ tables, isLoading, onRefresh }) => {
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [tableData, setTableData] = useState<Record<string, TableData>>({});
  const [loadingData, setLoadingData] = useState<Set<string>>(new Set());
  const [deletingTable, setDeletingTable] = useState<string | null>(null);

  const toggleTableExpansion = async (tableName: string) => {
    const newExpanded = new Set(expandedTables);
    
    if (newExpanded.has(tableName)) {
      newExpanded.delete(tableName);
    } else {
      newExpanded.add(tableName);
      // Load table data if not already loaded
      if (!tableData[tableName]) {
        await loadTableData(tableName);
      }
    }
    
    setExpandedTables(newExpanded);
  };

  const loadTableData = async (tableName: string) => {
    setLoadingData(prev => new Set(prev).add(tableName));
    
    try {
      const response = await fetch(`http://localhost:8000/table-preview?table_name=${encodeURIComponent(tableName)}`);
      if (response.ok) {
        const data = await response.json();
        setTableData(prev => ({
          ...prev,
          [tableName]: {
            columns: data.columns || [],
            rows: data.rows || []
          }
        }));
      }
    } catch (error) {
      console.error('Error loading table data:', error);
    } finally {
      setLoadingData(prev => {
        const newSet = new Set(prev);
        newSet.delete(tableName);
        return newSet;
      });
    }
  };

  const handleDeleteTable = async (tableName: string) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete the dataset '${tableName}'? This will permanently remove the dataset from Snowflake.`
    );
    if (!confirmed) return;
    setDeletingTable(tableName);
    try {
      const response = await fetch('http://localhost:8000/delete-table', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ table_name: tableName })
      });
      if (response.ok) {
        onRefresh();
      } else {
        const data = await response.json();
        alert(data.detail || 'Failed to delete table.');
      }
    } catch (error) {
      alert('Failed to delete table.');
    } finally {
      setDeletingTable(null);
    }
  };

  const formatTableName = (table: TableInfo) => {
    return `${table.database}.${table.schema}.${table.name}`;
  };

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="inline-flex items-center space-x-2">
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        </div>
        <p className="text-sm text-gray-500 mt-2">Loading tables...</p>
      </div>
    );
  }

  if (tables.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No tables found</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by uploading a CSV file.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Existing Tables ({tables.length})</h3>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      <div className="grid gap-4">
        {tables.map((table) => (
          <div key={table.name} className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            {/* Table Header */}
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h4 className="text-lg font-semibold text-gray-900">{table.name}</h4>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {table.kind}
                    </span>
                  </div>
                  <div className="mt-1 text-sm text-gray-500">
                    <span className="font-mono">{formatTableName(table)}</span>
                    {table.row_count > 0 && (
                      <span className="ml-3">• {table.row_count.toLocaleString()} rows</span>
                    )}
                  </div>
                  {table.comment && (
                    <p className="mt-1 text-sm text-gray-600">{table.comment}</p>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => toggleTableExpansion(table.name)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    {expandedTables.has(table.name) ? 'Collapse' : 'Expand'}
                    <svg
                      className={`ml-2 w-4 h-4 transition-transform ${expandedTables.has(table.name) ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDeleteTable(table.name)}
                    disabled={deletingTable === table.name}
                    className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                  >
                    {deletingTable === table.name ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>
            </div>

            {/* Expanded Content */}
            {expandedTables.has(table.name) && (
              <div className="px-6 py-4">
                {loadingData.has(table.name) ? (
                  <div className="text-center py-4">
                    <div className="inline-flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <p className="text-sm text-gray-500 mt-2">Loading data preview...</p>
                  </div>
                ) : tableData[table.name] ? (
                  <div className="space-y-4">
                    {/* Data Preview */}
                    <div>
                      <h5 className="text-sm font-medium text-gray-900 mb-3">Data Preview (First 5 rows)</h5>
                      <div className="overflow-x-auto border border-gray-200 rounded-lg">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              {tableData[table.name].columns.map((column) => (
                                <th key={column} className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  {column}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {tableData[table.name].rows.map((row, index) => (
                              <tr key={index} className="hover:bg-gray-50">
                                {row.map((cell, cellIndex) => (
                                  <td key={cellIndex} className="px-3 py-2 text-sm text-gray-900">
                                    {String(cell)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-sm text-gray-500">No data available for preview.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TableDisplay; 