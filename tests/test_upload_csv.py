"""
Test cases for CSV upload functionality.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
import io

client = TestClient(app)

@patch('backend.routers.upload.insert_dataframe_with_date_parsing')
@patch('backend.routers.upload.create_table')
@patch('backend.routers.upload.get_engine')
@patch('backend.routers.upload.table_exists')
def test_upload_csv_success(mock_table_exists, mock_get_engine, mock_create_table, mock_insert_dataframe_with_date_parsing):
    """Test successful CSV upload."""
    # Mock engine
    engine = MagicMock()
    mock_get_engine.return_value = engine
    
    # Mock table doesn't exist
    mock_table_exists.return_value = False
    
    # Mock successful table creation and data insertion
    mock_create_table.return_value = True
    mock_insert_dataframe_with_date_parsing.return_value = 100  # Return row count
    
    # Create a test CSV file
    csv_content = "Name,Age,City\nJohn,25,NYC\nJane,30,LA"
    csv_file = io.StringIO(csv_content)
    
    # Make request
    response = client.post(
        "/upload-csv",
        files={"file": ("test.csv", csv_file.getvalue(), "text/csv")},
        data={"table_name": "test_table"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "qualified_table_name" in data
    assert "Successfully uploaded" in data["message"]

@patch('backend.routers.upload.get_engine')
def test_upload_csv_empty_file(mock_get_engine):
    """Test upload with empty CSV file."""
    # Mock engine
    engine = MagicMock()
    mock_get_engine.return_value = engine
    
    # Create empty CSV file
    csv_content = ""
    csv_file = io.StringIO(csv_content)
    
    # Make request
    response = client.post(
        "/upload-csv",
        files={"file": ("empty.csv", csv_file.getvalue(), "text/csv")},
        data={"table_name": "test_table"}
    )
    
    # Verify response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data

@patch('backend.routers.upload.get_engine')
def test_upload_csv_invalid_filetype(mock_get_engine):
    """Test upload with invalid file type."""
    # Mock engine
    engine = MagicMock()
    mock_get_engine.return_value = engine
    
    # Create a text file (not CSV)
    file_content = "This is not a CSV file"
    
    # Make request
    response = client.post(
        "/upload-csv",
        files={"file": ("test.txt", file_content, "text/plain")},
        data={"table_name": "test_table"}
    )
    
    # Verify response
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "CSV file" in data["detail"] 