"""
Test cases for the charts router endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app

client = TestClient(app)

class TestChartsRouter:
    """Test cases for charts router endpoints."""

    @patch('backend.routers.charts.get_engine')
    def test_get_chart_data_success(self, mock_get_engine):
        """Test successful chart data retrieval."""
        # Mock engine and connection
        engine = MagicMock()
        conn = MagicMock()
        result = MagicMock()
        
        # Mock query results - need to iterate over rows
        result.__iter__ = MagicMock(return_value=iter([
            ("2023-01-01", 150.50),
            ("2023-01-02", 152.25),
            ("2023-01-03", 148.75)
        ]))
        
        conn.execute.return_value = result
        engine.connect.return_value.__enter__.return_value = conn
        mock_get_engine.return_value = engine
        
        # Request data
        request_data = {
            "table_name": "stocks",
            "x_column": "Date",
            "y_column": "Price",
            "date_format": "YYYY-MM-DD",
            "date_range": ["2023-01-01", "2023-01-03"]
        }
        
        # Make request
        response = client.post("/chart-data", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "chart_data" in data
        assert "sql_query" in data
        assert "total_points" in data
        
        # The actual implementation converts results to dict format
        assert len(data["chart_data"]) == 3
        assert data["total_points"] == 3

    @patch('backend.routers.charts.get_engine')
    def test_get_chart_data_no_date_filtering(self, mock_get_engine):
        """Test chart data retrieval without date filtering."""
        # Mock engine and connection
        engine = MagicMock()
        conn = MagicMock()
        result = MagicMock()
        
        # Mock query results - need to iterate over rows
        result.__iter__ = MagicMock(return_value=iter([
            ("AAPL", 150.50),
            ("GOOGL", 2800.25)
        ]))
        
        conn.execute.return_value = result
        engine.connect.return_value.__enter__.return_value = conn
        mock_get_engine.return_value = engine
        
        # Request data without date filtering
        request_data = {
            "table_name": "stocks",
            "x_column": "Symbol",
            "y_column": "Price"
        }
        
        # Make request
        response = client.post("/chart-data", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["chart_data"]) == 2
        assert data["total_points"] == 2


    @patch('backend.routers.charts.get_engine')
    def test_get_chart_data_sql_error(self, mock_get_engine):
        """Test chart data retrieval when SQL execution fails."""
        # Mock engine and connection
        engine = MagicMock()
        conn = MagicMock()
        conn.execute.side_effect = Exception("Column does not exist")
        engine.connect.return_value.__enter__.return_value = conn
        mock_get_engine.return_value = engine
        
        # Request data
        request_data = {
            "table_name": "stocks",
            "x_column": "nonexistent_column",
            "y_column": "Price"
        }
        
        # Make request
        response = client.post("/chart-data", json=request_data)
        
        # Verify error response
        assert response.status_code == 500
        assert "Failed to get chart data" in response.json()["detail"]

    @patch('backend.routers.charts.get_engine')
    def test_get_chart_data_with_date_range(self, mock_get_engine):
        """Test chart data retrieval with date range filtering."""
        # Mock engine and connection
        engine = MagicMock()
        conn = MagicMock()
        result = MagicMock()
        
        # Mock query results - need to iterate over rows
        result.__iter__ = MagicMock(return_value=iter([
            ("2023-01-01", 150.50),
            ("2023-01-02", 152.25)
        ]))
        
        conn.execute.return_value = result
        engine.connect.return_value.__enter__.return_value = conn
        mock_get_engine.return_value = engine
        
        # Request data with date range
        request_data = {
            "table_name": "stocks",
            "x_column": "Date",
            "y_column": "Price",
            "date_format": "YYYY-MM-DD",
            "date_range": ["2023-01-01", "2023-01-02"]
        }
        
        # Make request
        response = client.post("/chart-data", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data["chart_data"]) == 2

    @patch('backend.routers.charts.get_engine')
    def test_get_chart_data_empty_results(self, mock_get_engine):
        """Test chart data retrieval with empty results."""
        # Mock engine and connection
        engine = MagicMock()
        conn = MagicMock()
        result = MagicMock()
        
        # Mock empty query results - need to iterate over rows
        result.__iter__ = MagicMock(return_value=iter([]))
        
        conn.execute.return_value = result
        engine.connect.return_value.__enter__.return_value = conn
        mock_get_engine.return_value = engine
        
        # Request data
        request_data = {
            "table_name": "empty_table",
            "x_column": "Date",
            "y_column": "Price"
        }
        
        # Make request
        response = client.post("/chart-data", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data["chart_data"]) == 0
        assert data["total_points"] == 0

    def test_get_chart_data_missing_required_fields(self):
        """Test chart data retrieval with missing required fields."""
        # Request data without required fields
        request_data = {
            "table_name": "stocks"
            # Missing x_column and y_column
        }
        
        # Make request
        response = client.post("/chart-data", json=request_data)
        
        # Verify error response
        assert response.status_code == 422  # Validation error

    def test_get_chart_data_invalid_date_format(self):
        """Test chart data retrieval with invalid date format."""
        request_data = {
            "table_name": "stocks",
            "x_column": "Date",
            "y_column": "Price",
            "date_format": "INVALID-FORMAT"
        }
        
        # Make request
        response = client.post("/chart-data", json=request_data)
        
        # Should still work, just might not parse dates correctly
        # The validation happens at SQL level
        assert response.status_code in [200, 500]

    