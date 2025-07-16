import React, { useState } from 'react';

interface CSVUploadProps {
  onUploadSuccess?: (data: any[]) => void;
}

interface UploadStatus {
  type: 'idle' | 'loading' | 'success' | 'error';
  message?: string;
  data?: any[];
  columnTypes?: Record<string, string>;
  tableInfo?: {
    table_name: string;
    qualified_table_name: string;
    row_count: number;
  };

}

const CSVUpload: React.FC<CSVUploadProps> = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [tableName, setTableName] = useState('');
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ type: 'idle' });
  const [dateFormatPrompts, setDateFormatPrompts] = useState<Record<string, string>>({});
  const [dateFormats, setDateFormats] = useState<Record<string, string>>({});
  const [awaitingDateFormats, setAwaitingDateFormats] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'text/csv') {
      setSelectedFile(file);
      // Set default table name to filename without extension
      if (!tableName) {
        const fileName = file.name.replace(/\.csv$/i, '');
        setTableName(fileName);
      }
      setUploadStatus({ type: 'idle' });
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploadStatus({ type: 'loading', message: 'Uploading to Snowflake...' });

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('table_name', tableName || selectedFile.name.replace(/\.csv$/i, ''));
    // If awaiting date formats, append them
    if (awaitingDateFormats) {
      formData.append('date_formats', JSON.stringify(dateFormats));
    }

    try {
      const response = await fetch('http://localhost:8000/upload-csv', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      // Check if the response was successful
      if (!response.ok) {
        // Handle HTTP error responses
        const errorMessage = result.detail || result.message || 'Upload failed';
        setUploadStatus({ type: 'error', message: errorMessage });
        return;
      }

      if (result.message === 'Date format required' && result.date_format_prompts) {
        setDateFormatPrompts(result.date_format_prompts);
        setAwaitingDateFormats(true);
        setUploadStatus({ type: 'idle', message: 'Please specify date formats for the detected columns.' });
        return;
      }

      setUploadStatus({ 
        type: 'success', 
        message: result.message,
        data: result.preview_data || [],
        columnTypes: result.column_types || {},
        tableInfo: {
          table_name: result.table_name,
          qualified_table_name: result.qualified_table_name,
          row_count: result.row_count
        }
      });

      if (onUploadSuccess && result.preview_data) {
        onUploadSuccess(result.preview_data);
      }

      // Reset form
      setSelectedFile(null);
      setTableName('');
      setDateFormatPrompts({});
      setDateFormats({});
      setAwaitingDateFormats(false);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadStatus({ type: 'error', message: errorMessage });
    }
  };

  const getStatusColor = () => {
    switch (uploadStatus.type) {
      case 'loading': return 'text-blue-600';
      case 'success': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  // Handle date format input change
  const handleDateFormatChange = (col: string, value: string) => {
    setDateFormats(prev => ({ ...prev, [col]: value }));
  };

  // Handle submit of date formats
  const handleDateFormatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleUpload();
  };

  return (
    <div className="space-y-6">
      {/* File Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select CSV File
        </label>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileSelect}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        {selectedFile && (
          <div className="mt-2 text-sm text-gray-600">
            <p>Selected: {selectedFile.name}</p>
            <p>Size: {formatFileSize(selectedFile.size)}</p>
            <p className="text-xs text-gray-500">Max file size: 50MB</p>
          </div>
        )}
      </div>

      {/* Table Name Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Table Name (optional)
        </label>
        <input
          type="text"
          value={tableName}
          onChange={(e) => setTableName(e.target.value)}
          placeholder="Enter table name or leave blank to use filename"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Date Format Prompts */}
      {awaitingDateFormats && Object.keys(dateFormatPrompts).length > 0 && (
        <form onSubmit={handleDateFormatSubmit} className="space-y-4">
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h3 className="text-sm font-medium text-yellow-900 mb-2">Date Format Required</h3>
            {Object.entries(dateFormatPrompts).map(([col, prompt]) => (
              <div key={col} className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">{prompt}</label>
                <input
                  type="text"
                  value={dateFormats[col] || ''}
                  onChange={e => handleDateFormatChange(col, e.target.value)}
                  placeholder="e.g. YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  list={`date-format-suggestions-${col}`}
                  required
                />
                <datalist id={`date-format-suggestions-${col}`}>
                  <option value="YYYY-MM-DD" />
                  <option value="MM/DD/YYYY" />
                  <option value="DD-MM-YYYY" />
                  <option value="MM-DD-YYYY" />
                  <option value="YYYY/MM/DD" />
                </datalist>
              </div>
            ))}
            <button
              type="submit"
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              Submit Date Formats
            </button>
          </div>
        </form>
      )}

      {/* Upload Button */}
      {!awaitingDateFormats && (
        <button
          onClick={handleUpload}
          disabled={!selectedFile || uploadStatus.type === 'loading'}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {uploadStatus.type === 'loading' ? 'Uploading...' : 'Upload to Snowflake'}
        </button>
      )}

      {/* Status Message */}
      {uploadStatus.message && (
        <div className={`text-sm ${getStatusColor()}`}>
          {uploadStatus.message}
        </div>
      )}

      {/* Success Details */}
      {uploadStatus.type === 'success' && (
        <div className="space-y-4">
          {/* Table Info */}
          {uploadStatus.tableInfo && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="text-sm font-medium text-green-900 mb-2">Table Created Successfully</h3>
              <div className="text-sm text-green-700 space-y-1">
                <p><strong>Table Name:</strong> {uploadStatus.tableInfo.table_name}</p>
                <p><strong>Full Path:</strong> {uploadStatus.tableInfo.qualified_table_name}</p>
                <p><strong>Rows Uploaded:</strong> {uploadStatus.tableInfo.row_count.toLocaleString()}</p>
              </div>
            </div>
          )}



          {/* Column Types */}
          {uploadStatus.columnTypes && Object.keys(uploadStatus.columnTypes).length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-2">Column Types:</h3>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="grid gap-3 text-xs" style={{ gridTemplateColumns: `repeat(${Object.keys(uploadStatus.columnTypes).length}, minmax(0, 1fr))` }}>
                  {/* Column Names Row */}
                  {Object.keys(uploadStatus.columnTypes).map((column) => (
                    <div key={`name-${column}`} className="font-mono text-gray-570 font-bold text-center truncate text-sm" title={column}>
                      {column}
                    </div>
                  ))}
                  {/* Column Types Row */}
                  {Object.values(uploadStatus.columnTypes).map((type, index) => (
                    <div key={`type-${index}`} className="text-gray-600 bg-white px-2 py-1 rounded border text-center text-xs">
                      {type}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Preview Data */}
          {uploadStatus.data && uploadStatus.data.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-2">Preview (First 5 rows):</h3>
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(uploadStatus.data[0]).map((header) => (
                        <th key={header} className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {uploadStatus.data.map((row, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        {Object.values(row).map((cell, cellIndex) => (
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
          )}
        </div>
      )}
    </div>
  );
};

export default CSVUpload; 