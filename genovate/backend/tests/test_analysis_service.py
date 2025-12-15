
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

# Import functions from the service
from services.analysis_service import _extract_property_details, _fetch_bigquery_context

# --- Tests for _extract_property_details ---

def test_extract_full_details():
    content = "This is an office building at 123 Main St, Anytown, CA 90210. It is 50,000 sqft."
    expected = {"state": "CA", "city": "Anytown", "zip": "90210", "property_type": "office", "sqft": 50000}
    assert _extract_property_details(content) == expected

def test_extract_minimal_details():
    content = "Property in TX. 1,200 sf retail space."
    expected = {"state": "TX", "city": None, "zip": None, "property_type": "retail", "sqft": 1200}
    assert _extract_property_details(content) == expected

def test_extract_no_details():
    content = "A piece of property."
    expected = {"state": None, "city": None, "zip": None, "property_type": None, "sqft": None}
    assert _extract_property_details(content) == expected

def test_extract_with_no_city():
    content = "A 25,000 sq. ft. industrial warehouse in FL 33101."
    expected = {"state": "FL", "city": None, "zip": "33101", "property_type": "industrial", "sqft": 25000}
    assert _extract_property_details(content) == expected

# --- Tests for _fetch_bigquery_context ---

@patch('services.analysis_service.bigquery.Client')
def test_fetch_bigquery_no_location(mock_client):
    """Test that it returns a specific message when no state is provided."""
    details = {"state": None}
    result = _fetch_bigquery_context(details)
    assert "No location information could be extracted" in result
    mock_client.assert_not_called()

@patch('services.analysis_service.bigquery.Client')
def test_fetch_bigquery_successful_fetch(mock_client):
    """Test a successful fetch from multiple tables."""
    # Mock the BigQuery client and its query method
    mock_query_job = MagicMock()
    mock_query_job.to_dataframe.return_value = pd.DataFrame([{'state': 'CA', 'price': 500000}])
    
    mock_instance = mock_client.return_value
    mock_instance.query.return_value = mock_query_job

    details = {"state": "CA", "city": "Anytown", "sqft": 1000, "property_type": "office"}
    result = _fetch_bigquery_context(details)

    # Assert that the client was called
    mock_client.assert_called_once()
    # Assert that query was called multiple times (for each query in the function)
    assert mock_instance.query.call_count > 1
    # Assert that the result contains parts of the mocked dataframe
    assert '"state": "CA"' in result
    assert '"price": 500000' in result

@patch('services.analysis_service.bigquery.Client')
def test_fetch_bigquery_no_data_found(mock_client):
    """Test that it returns a 'no data' message when queries return empty dataframes."""
    mock_query_job = MagicMock()
    mock_query_job.to_dataframe.return_value = pd.DataFrame() # Empty dataframe
    
    mock_instance = mock_client.return_value
    mock_instance.query.return_value = mock_query_job

    details = {"state": "WY"} # A state with potentially no data
    result = _fetch_bigquery_context(details)

    assert "No relevant data found in BigQuery" in result

@patch('services.analysis_service.bigquery.Client')
def test_fetch_bigquery_api_error(mock_client):
    """Test that it returns a graceful error message on BigQuery API failure."""
    from google.api_core.exceptions import GoogleAPICallError
    
    mock_instance = mock_client.return_value
    mock_instance.query.side_effect = GoogleAPICallError("Permission Denied")

    details = {"state": "CA"}
    result = _fetch_bigquery_context(details)

    assert "Error accessing BigQuery" in result
    assert "Permission Denied" in result
