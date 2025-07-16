"""
Test cases for SQL agent functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import queue
from backend.agents.sql_agent import (
    format_results_markdown_table,
    run_sql_agent
)

class TestSQLAgent:
    """Test cases for SQL agent functionality."""

    
    def test_format_results_markdown_table_with_data(self):
        """Test formatting results as markdown table with data."""
        results = [
            ("AAPL", 150.50, 1000),
            ("GOOGL", 2800.25, 500)
        ]
        columns = ["Symbol", "Price", "Volume"]
        
        formatted = format_results_markdown_table(results, columns)
        
        # Check markdown table structure
        assert "| Symbol | Price | Volume |" in formatted
        assert "| AAPL | 150.5 | 1000 |" in formatted  # Note: 150.5 not 150.50
        assert "| GOOGL | 2800.25 | 500 |" in formatted
        assert "| --- |" in formatted

    def test_format_results_markdown_table_empty_results(self):
        """Test formatting empty results."""
        results = []
        columns = ["Symbol", "Price", "Volume"]
        
        formatted = format_results_markdown_table(results, columns)
        
        # Should indicate no results
        assert "No results" in formatted or "empty" in formatted.lower()

    def test_format_results_markdown_table_no_columns(self):
        """Test formatting with no columns."""
        results = [("AAPL", 150.50)]
        columns = []
        
        formatted = format_results_markdown_table(results, columns)
        
        # Should handle gracefully
        assert len(formatted) > 0

    @patch('backend.agents.sql_agent.llm')
    @patch('backend.agents.sql_agent.create_sql_agent')
    @patch('backend.agents.sql_agent.SQLDatabaseToolkit')
    @patch('backend.agents.sql_agent.SQLDatabase')
    @patch('backend.agents.sql_agent.get_snowflake_engine')
    def test_run_sql_agent_success(self, mock_get_engine, mock_sql_db, mock_toolkit, mock_create_agent, mock_llm):
        """Test successful SQL agent execution."""
        # Mock engine
        engine = MagicMock()
        mock_get_engine.return_value = engine
        
        # Mock database
        db = MagicMock()
        mock_sql_db.return_value = db
        
        # Mock toolkit
        toolkit = MagicMock()
        mock_toolkit.return_value = toolkit
        
        # Mock SQL agent
        agent_executor = MagicMock()
        agent_executor.run.return_value = "Query executed successfully"
        mock_create_agent.return_value = agent_executor
        
        # Mock LLM
        mock_llm.invoke.return_value = MagicMock(content="Summary of results")
        
        # Mock callback
        with patch('backend.agents.sql_agent.StreamingSQLCaptureCallbackHandler') as mock_callback_class:
            callback = MagicMock()
            callback.sql_query = "SELECT * FROM test"
            callback.reasoning_steps = []
            mock_callback_class.return_value = callback
            
            # Run the agent
            results = list(run_sql_agent("Test query"))
            
            # Should return results
            assert len(results) > 0
            assert any("summary" in str(result).lower() for result in results)

    @patch('backend.agents.sql_agent.llm')
    @patch('backend.agents.sql_agent.create_sql_agent')
    @patch('backend.agents.sql_agent.SQLDatabaseToolkit')
    @patch('backend.agents.sql_agent.SQLDatabase')
    @patch('backend.agents.sql_agent.get_snowflake_engine')
    def test_run_sql_agent_with_stream_queue(self, mock_get_engine, mock_sql_db, mock_toolkit, mock_create_agent, mock_llm):
        """Test SQL agent execution with streaming queue."""
        # Mock engine
        engine = MagicMock()
        mock_get_engine.return_value = engine
        
        # Mock database
        db = MagicMock()
        mock_sql_db.return_value = db
        
        # Mock toolkit
        toolkit = MagicMock()
        mock_toolkit.return_value = toolkit
        
        # Mock SQL agent
        agent_executor = MagicMock()
        agent_executor.run.return_value = "Query executed"
        mock_create_agent.return_value = agent_executor
        
        # Mock LLM
        mock_llm.invoke.return_value = MagicMock(content="Test summary")
        
        # Create a queue for streaming
        stream_queue = queue.Queue()
        
        # Mock callback
        with patch('backend.agents.sql_agent.StreamingSQLCaptureCallbackHandler') as mock_callback_class:
            callback = MagicMock()
            callback.sql_query = "SELECT 1"
            callback.reasoning_steps = []
            mock_callback_class.return_value = callback
            
            # Run the agent with stream queue
            results = list(run_sql_agent("Test query", stream_queue=stream_queue))
            
            # When using stream_queue, results are put in the queue, not yielded
            # So the generator should be empty
            assert len(results) == 0
            
            # But the queue should have the final result
            assert not stream_queue.empty()
            final_result = stream_queue.get()
            assert final_result["type"] == "final_result"

    @patch('backend.agents.sql_agent.create_sql_agent')
    @patch('backend.agents.sql_agent.SQLDatabaseToolkit')
    @patch('backend.agents.sql_agent.SQLDatabase')
    @patch('backend.agents.sql_agent.get_snowflake_engine')
    def test_run_sql_agent_handles_exception(self, mock_get_engine, mock_sql_db, mock_toolkit, mock_create_agent):
        """Test SQL agent handles exceptions gracefully."""
        # Mock engine
        engine = MagicMock()
        mock_get_engine.return_value = engine
        
        # Mock database
        db = MagicMock()
        mock_sql_db.return_value = db
        
        # Mock toolkit
        toolkit = MagicMock()
        mock_toolkit.return_value = toolkit
        
        # Mock SQL agent to raise exception
        agent_executor = MagicMock()
        agent_executor.run.side_effect = Exception("Database connection failed")
        mock_create_agent.return_value = agent_executor
        
        # Mock callback
        with patch('backend.agents.sql_agent.StreamingSQLCaptureCallbackHandler') as mock_callback_class:
            callback = MagicMock()
            callback.reasoning_steps = []
            mock_callback_class.return_value = callback
            
            # Run the agent
            results = list(run_sql_agent("Test query"))
            
            # Should handle exception and return error message
            assert len(results) > 0
            assert any("error" in str(result).lower() for result in results)

    @patch('backend.agents.sql_agent.llm')
    @patch('backend.agents.sql_agent.create_sql_agent')
    @patch('backend.agents.sql_agent.SQLDatabaseToolkit')
    @patch('backend.agents.sql_agent.SQLDatabase')
    @patch('backend.agents.sql_agent.get_snowflake_engine')
    def test_run_sql_agent_sql_execution_error(self, mock_get_engine, mock_sql_db, mock_toolkit, mock_create_agent, mock_llm):
        """Test SQL agent handles SQL execution errors."""
        # Mock engine
        engine = MagicMock()
        mock_get_engine.return_value = engine
        
        # Mock database
        db = MagicMock()
        mock_sql_db.return_value = db
        
        # Mock toolkit
        toolkit = MagicMock()
        mock_toolkit.return_value = toolkit
        
        # Mock SQL agent
        agent_executor = MagicMock()
        agent_executor.run.return_value = "Query executed"
        mock_create_agent.return_value = agent_executor
        
        # Mock LLM
        mock_llm.invoke.return_value = MagicMock(content="Query failed")
        
        # Mock callback with SQL query
        with patch('backend.agents.sql_agent.StreamingSQLCaptureCallbackHandler') as mock_callback_class:
            callback = MagicMock()
            callback.sql_query = "SELECT * FROM invalid_table"
            callback.reasoning_steps = []
            mock_callback_class.return_value = callback
            
            # Mock SQL execution failure
            with patch('backend.agents.sql_agent.text') as mock_text:
                mock_text.return_value = MagicMock()
                
                # Run the agent
                results = list(run_sql_agent("Test query"))
                
                # Should return results even with SQL error
                assert len(results) > 0 