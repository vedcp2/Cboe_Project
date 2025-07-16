import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app



client = TestClient(app)

class TestAgentRouter:
    """Test suite for agent router endpoints."""
    
    @patch('backend.routers.agent.stream_query_response')
    def test_ask_data_agent_streaming_success(self, mock_stream_response):
        """Test successful streaming data agent query."""
        # Mock streaming response
        mock_stream_response.return_value = [
            'data: {"type": "reasoning_step", "step": {"type": "thought", "content": "I need to query the database"}}\n\n',
            'data: {"type": "reasoning_step", "step": {"type": "action", "tool": "sql_db_query", "input": "SELECT * FROM stocks"}}\n\n',
            'data: {"type": "reasoning_step", "step": {"type": "observation", "content": "Query executed successfully"}}\n\n',
            'data: {"type": "final_result", "answer": "Found 100 records", "sql_query": "SELECT * FROM stocks", "query_results": [["AAPL", 150.50]]}\n\n'
        ]
        
        # Request data
        request_data = {"question": "Show me all stock data"}
        
        # Make request
        response = client.post("/ask-data-agent-streaming", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify streaming response headers
        assert "no-cache" in response.headers.get("cache-control", "")
        assert "keep-alive" in response.headers.get("connection", "")
        
        # Verify stream_query_response was called
        mock_stream_response.assert_called_once_with("Show me all stock data")
    
    @patch('backend.routers.agent.stream_query_response')
    def test_ask_data_agent_streaming_data_query(self, mock_stream_response):
        """Test streaming data agent with data-related query."""
        # Mock streaming response for data query
        mock_stream_response.return_value = [
            'data: {"type": "reasoning_step", "step": {"type": "thought", "content": "This is a data query"}}\n\n',
            'data: {"type": "reasoning_step", "step": {"type": "action", "tool": "sql_db_list_tables", "input": ""}}\n\n',
            'data: {"type": "reasoning_step", "step": {"type": "observation", "content": "stocks, trades"}}\n\n',
            'data: {"type": "final_result", "answer": "Found tables: stocks, trades"}\n\n'
        ]
        
        # Request data with data-related keywords
        request_data = {"question": "What tables are available for stock price analysis?"}
        
        # Make request
        response = client.post("/ask-data-agent-streaming", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify stream_query_response was called with the question
        mock_stream_response.assert_called_once_with("What tables are available for stock price analysis?")
    
    @patch('backend.routers.agent.stream_query_response')
    def test_ask_data_agent_streaming_general_query(self, mock_stream_response):
        """Test streaming data agent with general query."""
        # Mock streaming response for general query
        mock_stream_response.return_value = [
            'data: {"type": "chat_token", "content": "Hello! "}\n\n',
            'data: {"type": "chat_token", "content": "I can help you "}\n\n',
            'data: {"type": "chat_token", "content": "with data analysis."}\n\n',
            'data: {"type": "chat_done"}\n\n',
            'data: {"type": "final_result", "summary": "Hello! I can help you with data analysis."}\n\n'
        ]
        
        # Request data with general query
        request_data = {"question": "Hello, how are you?"}
        
        # Make request
        response = client.post("/ask-data-agent-streaming", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify stream_query_response was called
        mock_stream_response.assert_called_once_with("Hello, how are you?")
    
    def test_ask_data_agent_streaming_missing_question(self):
        """Test streaming data agent with missing question."""
        # Request data without question
        request_data = {}
        
        # Make request
        response = client.post("/ask-data-agent-streaming", json=request_data)
        
        # Verify validation error
        assert response.status_code == 422
    
    
    @patch('backend.routers.agent.stream_query_response')
    def test_ask_data_agent_streaming_error_handling(self, mock_stream_response):
        """Test streaming data agent error handling."""
        # Mock streaming response with error
        mock_stream_response.return_value = [
            'data: {"type": "reasoning_step", "step": {"type": "thought", "content": "Processing query"}}\n\n',
            'data: {"type": "error", "content": "Database connection failed"}\n\n'
        ]
        
        # Request data
        request_data = {"question": "Show me stock data"}
        
        # Make request
        response = client.post("/ask-data-agent-streaming", json=request_data)
        
        # Verify response (should still return 200 as it's streaming)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify stream_query_response was called
        mock_stream_response.assert_called_once_with("Show me stock data")
    
    @patch('backend.routers.agent.stream_query_response')
    def test_ask_data_agent_streaming_long_query(self, mock_stream_response):
        """Test streaming data agent with long query."""
        # Mock streaming response
        mock_stream_response.return_value = [
            'data: {"type": "reasoning_step", "step": {"type": "thought", "content": "This is a complex query"}}\n\n',
            'data: {"type": "final_result", "answer": "Processed complex query"}\n\n'
        ]
        
        # Request data with long question
        long_question = "Show me a detailed analysis of stock price trends over the last 5 years, including volume patterns, seasonal variations, and correlation with market indices for all technology stocks in the database"
        request_data = {"question": long_question}
        
        # Make request
        response = client.post("/ask-data-agent-streaming", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify stream_query_response was called with the long question
        mock_stream_response.assert_called_once_with(long_question)
    
    
    @patch('backend.routers.agent.stream_query_response')
    def test_ask_data_agent_streaming_sql_injection_attempt(self, mock_stream_response):
        """Test streaming data agent with potential SQL injection."""
        # Mock streaming response
        mock_stream_response.return_value = [
            'data: {"type": "final_result", "answer": "Query processed safely"}\n\n'
        ]
        
        # Request data with SQL injection attempt
        malicious_query = "Show me stocks'; DROP TABLE stocks; --"
        request_data = {"question": malicious_query}
        
        # Make request
        response = client.post("/ask-data-agent-streaming", json=request_data)
        
        # Verify response (should still work as the agent handles this)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify stream_query_response was called
        mock_stream_response.assert_called_once_with(malicious_query)
    
    @patch('backend.routers.agent.stream_query_response')
    def test_ask_data_agent_streaming_unicode_query(self, mock_stream_response):
        """Test streaming data agent with Unicode characters."""
        # Mock streaming response
        mock_stream_response.return_value = [
            'data: {"type": "final_result", "answer": "Processed Unicode query"}\n\n'
        ]
        
        # Request data with Unicode characters
        unicode_query = "Show me stocks with names containing 'café' or 'naïve' symbols 📈📊"
        request_data = {"question": unicode_query}
        
        # Make request
        response = client.post("/ask-data-agent-streaming", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify stream_query_response was called
        mock_stream_response.assert_called_once_with(unicode_query) 
  