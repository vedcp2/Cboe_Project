import React, { useState } from 'react';
import { Message } from '../types';
import AgentReasoning from './AgentReasoning';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [isSqlExpanded, setIsSqlExpanded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const isUser = message.type === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-3xl px-4 py-3 rounded-lg ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-white border border-gray-200 shadow-sm'
        }`}
      >
        {/* Message Content */}
        <div className="text-sm leading-relaxed">
          {isUser && message.content}
        </div>
        
        {/* Agent Reasoning Section */}
        <AgentReasoning 
          reasoningSteps={message.reasoningSteps || []} 
          isVisible={!isUser} 
          isLive={!isUser && message.isStreaming}
        />

        {/* Final Answer Section - Only show for assistant, not streaming, and if content exists */}
        {!isUser && message.content && (
          <div className={`mt-4 p-4 rounded-lg ${message.isStreaming ? 'border bg-yellow-50 border-yellow-200' : 'border-2 bg-blue-50 border-blue-300'}`}>
            <div className={`text-sm ${message.isStreaming ? 'text-yellow-900' : 'text-blue-900'}`}>
              {message.content}
              {message.isStreaming && <span className="animate-pulse">▍</span>}
            </div>
          </div>
        )}

        {/* SQL Query Section */}
        {message.sqlQuery && (
          <div className="mt-3">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsSqlExpanded(!isSqlExpanded)}
                className={`text-xs font-medium flex items-center space-x-1 ${
                  isUser ? 'text-blue-100 hover:text-white' : 'text-gray-600 hover:text-gray-800'
                } transition-colors`}
              >
                <span>{isSqlExpanded ? 'Hide' : 'Show'} SQL Query</span>
                <svg
                  className={`w-3 h-3 transition-transform ${isSqlExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
            
            {isSqlExpanded && (
              <div className="mt-2 p-3 bg-gray-100 rounded-md border border-gray-200">
                <div className="text-xs font-mono text-gray-800 whitespace-pre-wrap break-all">
                  {message.sqlQuery}
                </div>
                <button
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(message.sqlQuery || '');
                      setIsCopied(true);
                      setTimeout(() => setIsCopied(false), 2000);
                    } catch (err) {
                      console.error('Failed to copy SQL query:', err);
                    }
                  }}
                  className={`mt-2 text-xs font-medium transition-colors flex items-center space-x-1 ${
                    isCopied 
                      ? 'text-green-600 hover:text-green-700' 
                      : 'text-blue-600 hover:text-blue-800'
                  }`}
                >
                  {isCopied ? (
                    <>
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      <span>Copy SQL</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-xs mt-2 ${
          isUser ? 'text-blue-100' : 'text-gray-500'
        }`}>
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage; 