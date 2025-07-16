import React, { useState, useEffect } from 'react';
import CSVUpload from '../components/CSVUpload';
import TableDisplay from '../components/TableDisplay';

interface TableInfo {
  name: string;
  database: string;
  schema: string;
  kind: string;
  comment?: string;
  row_count: number;
}

const DatasetManagementPage: React.FC = () => {
  const [existingTables, setExistingTables] = useState<TableInfo[]>([]);
  const [isLoadingTables, setIsLoadingTables] = useState(false);

  const loadExistingTables = async () => {
    setIsLoadingTables(true);
    try {
      const response = await fetch('http://localhost:8000/list-tables');
      if (response.ok) {
        const data = await response.json();
        setExistingTables(data.tables || []);
      } else {
        console.error('Failed to load tables');
      }
    } catch (error) {
      console.error('Error loading tables:', error);
    } finally {
      setIsLoadingTables(false);
    }
  };

  useEffect(() => {
    loadExistingTables();
  }, []);

  const handleUploadSuccess = () => {
    // Refresh the table list after a successful upload
    loadExistingTables();
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">
            Data Management
          </h1>
          <p className="text-xl text-blue-100 max-w-3xl mx-auto leading-relaxed">
            Upload and manage datasets for intelligence analysis
          </p>
          <div className="mt-4 flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-blue-200">Secure Data Management</span>
          </div>
        </div>

        <div className="grid gap-8">
          {/* CSV Upload Section */}
          <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
            <div className="bg-gradient-to-r from-slate-50 to-blue-50 px-8 py-6 border-b border-slate-200">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
                <h2 className="text-xl font-semibold text-slate-800">Upload Market Data</h2>
                <span className="text-sm text-slate-600">Create new datasets</span>
              </div>
            </div>
            <div className="p-8">
              <CSVUpload onUploadSuccess={handleUploadSuccess} />
            </div>
          </div>

          {/* Existing Tables Section */}
          <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
            <div className="bg-gradient-to-r from-slate-50 to-blue-50 px-8 py-6 border-b border-slate-200">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
                <h2 className="text-xl font-semibold text-slate-800">Market Datasets</h2>
                <span className="text-sm text-slate-600">Explore uploaded data</span>
              </div>
            </div>
            <div className="p-8">
              <TableDisplay 
                tables={existingTables}
                isLoading={isLoadingTables}
                onRefresh={loadExistingTables}
              />
            </div>
          </div>
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

export default DatasetManagementPage; 