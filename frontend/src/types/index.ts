export interface ReasoningStep {
  type: 'thought' | 'action' | 'observation';
  // For action type
  tool?: string;
  input?: string;
  // For thought and observation types
  content?: string;
}

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  sqlQuery?: string;
  queryResults?: any[][];
  reasoningSteps?: ReasoningStep[];
  timestamp: Date;
  isStreaming?: boolean;
}

export interface ChatResponse {
  answer: string;
  sql_query: string;
  query_results: any[][];
}

export interface ApiError {
  message: string;
  status?: number;
} 