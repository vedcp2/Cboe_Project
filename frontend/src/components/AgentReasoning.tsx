import React, { useState, useEffect, useRef } from 'react';
import { ReasoningStep } from '../types';

interface AgentReasoningProps {
  reasoningSteps: ReasoningStep[];
  isVisible: boolean;
  isLive?: boolean;
}

const AgentReasoning: React.FC<AgentReasoningProps> = ({ reasoningSteps, isVisible, isLive }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const latestStepRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const prevStepCountRef = useRef(0);

  // Helper function to validate reasoning steps
  const isValidStep = (step: any): step is ReasoningStep => {
    if (!step || typeof step !== 'object' || !step.type || typeof step.type !== 'string') {
      return false;
    }
    
    // More lenient validation - allow action steps with empty input
    if (step.type === 'action') {
      return step.tool !== undefined && step.input !== undefined;
    }
    
    // For other types, require content
    return step.content !== undefined;
  };

  // Validate and filter reasoning steps to ensure they have the required properties
  const validReasoningSteps = reasoningSteps.filter(isValidStep);

  // Auto-expand and scroll when new reasoning steps are added during live streaming
  useEffect(() => {
    if (isLive && validReasoningSteps.length > prevStepCountRef.current) {
      // Auto-expand if not already expanded
      if (!isExpanded) {
        setIsExpanded(true);
      }
      
      // Scroll to the latest step after a short delay to ensure DOM is updated
      setTimeout(() => {
        if (latestStepRef.current) {
          latestStepRef.current.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'nearest',
            inline: 'nearest'
          });
        }
      }, 100);
      
      prevStepCountRef.current = validReasoningSteps.length;
    }
  }, [validReasoningSteps.length, isLive, isExpanded]);

  // Update the reference when steps change (for non-live updates)
  useEffect(() => {
    if (!isLive) {
      prevStepCountRef.current = validReasoningSteps.length;
    }
  }, [validReasoningSteps.length, isLive]);

  if (!isVisible || validReasoningSteps.length === 0) {
    return null;
  }

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'thought':
        return (
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-sm">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
        );
      case 'action':
        return (
          <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-sm">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        );
      case 'observation':
        return (
          <div className="w-8 h-8 bg-gradient-to-br from-amber-500 to-amber-600 rounded-xl flex items-center justify-center shadow-sm">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-8 h-8 bg-gradient-to-br from-slate-500 to-slate-600 rounded-xl flex items-center justify-center shadow-sm">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
    }
  };

  const getStepLabel = (type: string) => {
    switch (type) {
      case 'thought': return 'Thinking';
      case 'action': return 'Action';
      case 'observation': return 'Result';
      default: return type;
    }
  };

  const getStepColor = (type: string) => {
    switch (type) {
      case 'thought': return 'bg-gradient-to-r from-blue-50/80 to-blue-100/40';
      case 'action': return 'bg-gradient-to-r from-emerald-50/80 to-emerald-100/40';
      case 'observation': return 'bg-gradient-to-r from-amber-50/80 to-amber-100/40';
      default: return 'bg-gradient-to-r from-slate-50/80 to-slate-100/40';
    }
  };

  const getStepBorderColor = (type: string) => {
    switch (type) {
      case 'thought': return 'border-l-blue-500';
      case 'action': return 'border-l-emerald-500';
      case 'observation': return 'border-l-amber-500';
      default: return 'border-l-slate-500';
    }
  };

  const renderStepContent = (step: ReasoningStep) => {
    if (step.type === 'action' && step.tool !== undefined && step.input !== undefined) {
      return (
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-slate-600">Tool:</span>
            <code className="text-xs font-mono text-slate-800">{step.tool}</code>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-xs font-semibold text-slate-600">Input:</span>
            <code className="text-xs font-mono flex-1 whitespace-pre-wrap break-all text-slate-800">
              {step.input || '(empty)'}
            </code>
          </div>
        </div>
      );
    }
    return (
      <div className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
        {step.content || 'No content available'}
      </div>
    );
  };

  return (
    <div className="mt-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center space-x-3 text-sm font-semibold text-slate-700 hover:text-slate-900 transition-all duration-200 hover:bg-slate-50 px-3 py-2 rounded-lg"
      >
        <svg
          className={`w-5 h-5 transition-transform duration-200 text-blue-600 ${isExpanded ? 'rotate-90' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        <span className="flex items-center space-x-2">
          <span>Live Agent Reasoning ({validReasoningSteps.length} steps)</span>
          {isLive && (
            <div className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs text-emerald-600 font-medium">LIVE</span>
            </div>
          )}
        </span>
      </button>

      {isExpanded && (
        <div ref={containerRef} className="mt-4 space-y-3 max-h-96 overflow-y-auto pr-2">
          {validReasoningSteps.map((step, index) => (
            <div
              key={index}
              ref={index === validReasoningSteps.length - 1 ? latestStepRef : null}
              className={`p-4 rounded-xl ${getStepColor(step.type)} ${getStepBorderColor(step.type)} border-l-4 transition-all duration-300 shadow-sm hover:shadow-md`}
            >
              <div className="flex items-start space-x-4">
                {getStepIcon(step.type)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      {getStepLabel(step.type)}
                    </span>
                    <span className="text-xs text-slate-500">#{index + 1}</span>
                  </div>
                  {renderStepContent(step)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentReasoning; 