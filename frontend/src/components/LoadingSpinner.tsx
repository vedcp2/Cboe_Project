import React from 'react';

const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex items-center justify-center space-x-3 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/50 rounded-xl px-6 py-4 shadow-sm backdrop-blur-sm">
      {/* Modern animated dots */}
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0ms', animationDuration: '1.4s' }}></div>
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '200ms', animationDuration: '1.4s' }}></div>
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '400ms', animationDuration: '1.4s' }}></div>
      </div>
      
      {/* Elegant text with icon */}
      <div className="flex items-center space-x-2">
        <svg className="w-4 h-4 text-blue-600 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <span className="text-sm font-medium text-blue-700">Analyzing data...</span>
      </div>
    </div>
  );
};

export default LoadingSpinner; 