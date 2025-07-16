import React, { useState, useRef, useEffect } from 'react';
import { Message } from '../types';
import ChatMessage from './ChatMessage';
import LoadingSpinner from './LoadingSpinner';

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);
  const prevMessageCountRef = useRef(0);
  const prevReasoningStepsRef = useRef<number[]>([]);
  const prevStreamingStatesRef = useRef<boolean[]>([]);

  // Load messages from localStorage on component mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('chatHistory');
    if (savedMessages) {
      try {
        const parsedMessages = JSON.parse(savedMessages);
        // Convert timestamp strings back to Date objects
        const messagesWithDates = parsedMessages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(messagesWithDates);
        prevMessageCountRef.current = messagesWithDates.length;
      } catch (error) {
        console.error('Error loading chat history from localStorage:', error);
        // If there's an error parsing, clear the corrupted data
        localStorage.removeItem('chatHistory');
      }
    }
    setInitialLoadComplete(true);
  }, []);

  // Save messages to localStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chatHistory', JSON.stringify(messages));
    }
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleInputFocus = () => {
    // Scroll to chat area when user focuses on input
    if (messages.length === 0) {
      // If no messages, scroll to the chat area
      const chatContainer = document.querySelector('.flex-1.overflow-y-auto');
      if (chatContainer) {
        chatContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    } else {
      // If there are messages, scroll to bottom
      scrollToBottom();
    }
  };

  useEffect(() => {
    // Only scroll to bottom if:
    // 1. Initial load is complete (to avoid scrolling on page load)
    // 2. New messages were added OR reasoning steps were added to existing messages OR streaming finished
    if (initialLoadComplete) {
      let shouldScroll = false;
      
      // Check if new messages were added
      if (messages.length > prevMessageCountRef.current) {
        shouldScroll = true;
        prevMessageCountRef.current = messages.length;
      }
      
      // Check if reasoning steps were added to any message
      const currentReasoningSteps = messages.map(msg => msg.reasoningSteps?.length || 0);
      if (currentReasoningSteps.length > 0) {
        for (let i = 0; i < currentReasoningSteps.length; i++) {
          if (!prevReasoningStepsRef.current[i] || currentReasoningSteps[i] > prevReasoningStepsRef.current[i]) {
            // Only scroll if it's a streaming message (live reasoning)
            if (messages[i]?.isStreaming) {
              shouldScroll = true;
            }
            break;
          }
        }
        prevReasoningStepsRef.current = currentReasoningSteps;
      }
      
      // Check if any message just finished streaming (transitioned from streaming to not streaming)
      const currentStreamingStates = messages.map(msg => msg.isStreaming || false);
      for (let i = 0; i < currentStreamingStates.length; i++) {
        // If a message was streaming before but is not streaming now, it just finished
        if (prevStreamingStatesRef.current[i] === true && currentStreamingStates[i] === false) {
          shouldScroll = true;
          break;
        }
      }
      prevStreamingStatesRef.current = currentStreamingStates;
      
      if (shouldScroll) {
        // Add a small delay to ensure DOM updates are complete
        setTimeout(() => {
          scrollToBottom();
        }, 100);
      }
    }
  }, [messages, initialLoadComplete]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    // Create assistant message that will be updated with streaming data
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      reasoningSteps: []
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      // Use streaming endpoint
      const response = await fetch('http://localhost:8000/ask-data-agent-streaming', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: inputValue.trim() }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'reasoning_step') {
                // Add reasoning step to the message
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessage.id 
                    ? { ...msg, reasoningSteps: [...(msg.reasoningSteps || []), data.step] }
                    : msg
                ));
              } else if (data.type === 'chat_token') {
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMessage.id
                    ? { ...msg, content: (msg.content || '') + data.content }
                    : msg
                ));
              } else if (data.type === 'chat_done') {
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMessage.id
                    ? { ...msg, isStreaming: false }
                    : msg
                ));
              } else if (data.type === 'final_result') {
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessage.id 
                    ? { 
                        ...msg, 
                        content: data.summary || data.answer,
                        sqlQuery: data.sql_query,
                        queryResults: data.query_results,
                        columns: data.columns,
                        isStreaming: false
                      }
                    : msg
                ));
                break;
              } else if (data.type === 'error') {
                throw new Error(data.content);
              }
            } catch (parseError) {
              console.error('Error parsing SSE data:', parseError);
            }
          }
        }
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      
      // Update the assistant message with error
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessage.id 
          ? { 
              ...msg, 
              content: `Sorry, I encountered an error: ${errorMessage}`,
              isStreaming: false
            }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const clearChatHistory = () => {
    setMessages([]);
    localStorage.removeItem('chatHistory');
  };

  return (
    <div className="flex flex-col h-[700px]">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="text-lg font-medium text-gray-900 mb-2">Start a conversation</p>
            <p className="text-sm text-gray-500 max-w-md mx-auto">
              Ask me anything about your data. I can help you analyze, query, and understand your datasets.
            </p>
          </div>
        )}
        
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        
        {/* Show spinner only if the latest assistant message is streaming */}
        {(() => {
          const lastAssistant = [...messages].reverse().find(m => m.type === 'assistant');
          return lastAssistant && lastAssistant.isStreaming ? (
            <div className="flex justify-center py-4">
              <LoadingSpinner />
            </div>
          ) : null;
        })()}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="border-t border-gray-200/50 px-8 py-6 bg-gradient-to-r from-gray-50/50 to-white/50">
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm text-gray-500">
            {messages.length > 0 && `${messages.length} message${messages.length === 1 ? '' : 's'}`}
          </div>
        </div>
        
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onFocus={handleInputFocus}
            placeholder="Ask a question about your data..."
            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm shadow-sm"
            disabled={isLoading}
          />
          <div className="flex flex-col space-y-2">
            {messages.length > 0 && (
              <button
                type="button"
                onClick={clearChatHistory}
                className="px-6 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 font-medium transition-all duration-200 rounded-lg border border-red-200 hover:border-red-300"
                title="Clear chat history"
              >
                Clear History
              </button>
            )}
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Sending...</span>
                </div>
                          ) : (
              <div className="flex items-center justify-center space-x-2">
                <span>Send</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </div>
            )}
            </button>
          </div>
        </form>
        
        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-red-700">Error: {error}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface; 