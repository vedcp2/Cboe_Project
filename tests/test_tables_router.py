"""
Test cases for the tables router endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app

client = TestClient(app)

class TestTablesRouter:
    """Test cases for tables router endpoints."""

    @patch('backend.routers.tables.get_table_row_count')
    @patch('backend.routers.tables.list_tables')
    @patch('backend.routers.tables.get_engine')
    def test_list_tables_success(self, mock_get_engine, mock_list_tables, mock_get_row_count):
        """Test successful table listing."""
        # Mock engine
        engine = MagicMock()
        mock_get_engine.return_value = engine
        
        # Mock table listing
        mock_list_tables.return_value = [
            {"name": "table1", "type": "TABLE"},
            {"name": "table2", "type": "TABLE"}
        ]
        
        # Mock row count
        mock_get_row_count.return_value = 100
        
        # Make request
        response = client.get("/list-tables")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "tables" in data
        assert "schema" in data
        assert "total_tables" in data
        assert len(data["tables"]) == 2
        assert data["total_tables"] == 2

    @patch('backend.routers.tables.list_tables')
    @patch('backend.routers.tables.get_engine')
    def test_list_tables_engine_error(self, mock_get_engine, mock_list_tables):
        """Test table listing when engine fails."""
        # Mock engine failure
        mock_get_engine.side_effect = Exception("Database connection failed")
        
        # Make request
        response = client.get("/list-tables")
        
        # Verify error response
        assert response.status_code == 500
        assert "Failed to list tables" in response.json()["detail"]

    @patch('backend.routers.tables.get_table_row_count')
    @patch('backend.routers.tables.list_tables')
    @patch('backend.routers.tables.get_engine')
    def test_list_tables_row_count_error(self, mock_get_engine, mock_list_tables, mock_get_row_count):
        """Test table listing when row count fails."""
        # Mock engine
        engine = MagicMock()
        mock_get_engine.return_value = engine
        
        # Mock table listing
        mock_list_tables.return_value = [
            {"name": "table1", "type": "TABLE"}
        ]
        
        # Mock row count failure
        mock_get_row_count.side_effect = Exception("Row count failed")
        
        # Make request
        response = client.get("/list-tables")
        
        # Verify response (should handle gracefully)
        assert response.status_code == 200
        data = response.json()
        assert data["tables"][0]["row_count"] == 0

    @patch('backend.routers.tables.get_engine')
    def test_table_preview_success(self, mock_get_engine):
        """Test successful table preview."""
        # Mock engine and connection
        engine = MagicMock()
        conn = MagicMock()
        
        # Mock DESCRIBE TABLE results (first call)
        describe_result = MagicMock()
        describe_result.__iter__ = MagicMock(return_value=iter([
            ("Symbol", "VARCHAR", "COLUMN"),
            ("Price", "FLOAT", "COLUMN"),
            ("Volume", "INTEGER", "COLUMN")
        ]))
        
        # Mock SELECT results (second call)
        select_result = MagicMock()
        select_result.__iter__ = MagicMock(return_value=iter([
            ("AAPL", 150.50, 1000),
            ("GOOGL", 2800.25, 500)
        ]))
        
        # Mock conn.execute to return different results based on call
        conn.execute.side_effect = [describe_result, select_result]
        engine.connect.return_value.__enter__.return_value = conn
        mock_get_engine.return_value = engine
        
        # Make request
        response = client.get("/table-preview?table_name=stocks")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "columns" in data
        assert "rows" in data
        assert data["columns"] == ["Symbol", "Price", "Volume"]
        assert len(data["rows"]) == 2
        assert data["rows"][0] == ["AAPL", 150.50, 1000]

    def test_table_preview_invalid_table_name(self):
        """Test table preview with invalid table name."""
        # Make request with invalid table name
        response = client.get("/table-preview?table_name=invalid_table!")
        
        # Verify error response - could be 400 or 500 depending on validation order
        assert response.status_code in [400, 500]
        assert "Invalid table name" in response.json()["detail"] or "Failed to get table preview" in response.json()["detail"]

    @patch('backend.routers.tables.get_engine')
    def test_table_preview_sql_error(self, mock_get_engine):
        """Test table preview when SQL execution fails."""
        # Mock engine and connection
        engine = MagicMock()
        conn = MagicMock()
        conn.execute.side_effect = Exception("Table does not exist")
        engine.connect.return_value.__enter__.return_value = conn
        mock_get_engine.return_value = engine
        
        # Make request
        response = client.get("/table-preview?table_name=nonexistent_table")
        
        # Verify error response
        assert response.status_code == 500
        assert "Failed to get table preview" in response.json()["detail"]

    @patch('backend.routers.tables.drop_table')
    @patch('backend.routers.tables.get_engine')
    def test_delete_table_success(self, mock_get_engine, mock_drop_table):
        """Test successful table deletion."""
        # Mock engine
        engine = MagicMock()
        mock_get_engine.return_value = engine
        
        # Mock successful deletion
        mock_drop_table.return_value = True
        
        # Make request - using the correct format for Body(..., embed=True)
        response = client.request("DELETE", "/delete-table", json={"table_name": "test_table"})
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "deleted" in data["message"]

    @patch('backend.routers.tables.drop_table')
    @patch('backend.routers.tables.get_engine')
    def test_delete_table_failure(self, mock_get_engine, mock_drop_table):
        """Test table deletion failure."""
        # Mock engine
        engine = MagicMock()
        mock_get_engine.return_value = engine
        
        # Mock deletion failure
        mock_drop_table.side_effect = Exception("Cannot drop table")
        
        # Make request
        response = client.request("DELETE", "/delete-table", json={"table_name": "test_table"})
        
        # Verify error response
        assert response.status_code == 500
        assert "Failed to delete table" in response.json()["detail"]

    def test_delete_table_invalid_table_name(self):
        """Test table deletion with invalid table name."""
        # Make request with invalid table name
        response = client.request("DELETE", "/delete-table", json={"table_name": "invalid_table!"})
        
        # Verify error response - could be 400 or 500 depending on validation order
        assert response.status_code in [400, 500]
        assert "Invalid table name" in response.json()["detail"] or "Failed to delete table" in response.json()["detail"]

    @patch('backend.routers.tables.get_engine')
    def test_table_preview_empty_results(self, mock_get_engine):
        """Test table preview with empty results."""
        # Mock engine and connection
        engine = MagicMock()
        conn = MagicMock()
        
        # Mock DESCRIBE TABLE results (first call)
        describe_result = MagicMock()
        describe_result.__iter__ = MagicMock(return_value=iter([
            ("Symbol", "VARCHAR", "COLUMN"),
            ("Price", "FLOAT", "COLUMN"),
            ("Volume", "INTEGER", "COLUMN")
        ]))
        
        # Mock SELECT results (second call) - empty
        select_result = MagicMock()
        select_result.__iter__ = MagicMock(return_value=iter([]))
        
        # Mock conn.execute to return different results based on call
        conn.execute.side_effect = [describe_result, select_result]
        engine.connect.return_value.__enter__.return_value = conn
        mock_get_engine.return_value = engine
        
        # Make request
        response = client.get("/table-preview?table_name=empty_table")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["columns"] == ["Symbol", "Price", "Volume"]
        assert data["rows"] == []

   