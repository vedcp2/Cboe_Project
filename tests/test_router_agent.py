"""
Test cases for the router agent query routing logic.
"""
import pytest
from backend.agents.router_agent import route_query

class TestRouterAgent:
    """Test cases for router agent query routing."""

    def test_route_query_data_keywords(self):
        """Test routing queries with data-related keywords."""
        data_queries = [
            "Show me the stock price",
            "What is the average volume?",
            "List all tables",
            "Query the database",
            "Show financial data",
            "Get the sum of sales",
            "What's the minimum price?",
            "Count the records",
            "Show me trends",
            "Compare the values"
        ]
        
        correct_count = 0
        for query in data_queries:
            result = route_query(query)
            if result == "data":
                correct_count += 1
            else:
                print(f"Query '{query}' routed to '{result}' instead of 'data'")
        
        # Allow 80% success rate
        success_rate = correct_count / len(data_queries)
        assert success_rate >= 0.8, f"Data keyword routing success rate {success_rate:.2%} is below 80%. {correct_count}/{len(data_queries)} correct."

    def test_route_query_general_keywords(self):
        """Test routing queries with general keywords."""
        general_queries = [
            "Hello, how are you?",
            "What is your name?",
            "Tell me a joke",
            "How do I cook pasta?",
            "What is the weather like?",
            "Explain machine learning",
            "Help me with my homework",
            "What time is it?"
        ]
        
        correct_count = 0
        for query in general_queries:
            result = route_query(query)
            if result == "general":
                correct_count += 1
            else:
                print(f"Query '{query}' routed to '{result}' instead of 'general'")
        
        # Allow 80% success rate
        success_rate = correct_count / len(general_queries)
        assert success_rate >= 0.8, f"General keyword routing success rate {success_rate:.2%} is below 80%. {correct_count}/{len(general_queries)} correct."

    def test_route_query_mixed_keywords(self):
        """Test routing queries with mixed keywords."""
        mixed_queries = [
            ("Show me the price data", "data"),
            ("I need help with the stock table", "data"),
            ("What is the average price in the database?", "data"),
            ("Can you help me understand this financial report?", "data"),
            ("Hello, can you show me the volume data?", "data"),
            ("Thank you for the price information", "general")
        ]
        
        correct_count = 0
        for query, expected in mixed_queries:
            result = route_query(query)
            if result == expected:
                correct_count += 1
            else:
                print(f"Query '{query}' routed to '{result}' instead of '{expected}'")
        
        # Allow 80% success rate
        success_rate = correct_count / len(mixed_queries)
        assert success_rate >= 0.8, f"Mixed keyword routing success rate {success_rate:.2%} is below 80%. {correct_count}/{len(mixed_queries)} correct."



    def test_route_query_none_input(self):
        """Test routing with None input."""
        result = route_query(None)
        assert result == "general"

    def test_route_query_sql_keywords(self):
        """Test routing queries with SQL-related keywords."""
        sql_queries = [
            "SELECT * FROM table",
            "Show me the query results",
            "What's in this table?",
            "List all columns",
            "Count the rows",
            "Sum the values",
            "Get the maximum value",
            "Find the minimum price"
        ]
        
        correct_count = 0
        for query in sql_queries:
            result = route_query(query)
            if result == "data":
                correct_count += 1
            else:
                print(f"Query '{query}' routed to '{result}' instead of 'data'")
        
        # Allow 80% success rate
        success_rate = correct_count / len(sql_queries)
        assert success_rate >= 0.8, f"SQL keyword routing success rate {success_rate:.2%} is below 80%. {correct_count}/{len(sql_queries)} correct."

    def test_route_query_financial_keywords(self):
        """Test routing queries with financial keywords."""
        financial_queries = [
            "What's the stock price?",
            "Show me the trading volume",
            "Get financial data",
            "What's the average price?",
            "Show price trends",
            "Compare stock prices"
        ]
        
        correct_count = 0
        for query in financial_queries:
            result = route_query(query)
            if result == "data":
                correct_count += 1
            else:
                print(f"Query '{query}' routed to '{result}' instead of 'data'")
        
        # Allow 80% success rate
        success_rate = correct_count / len(financial_queries)
        assert success_rate >= 0.8, f"Financial keyword routing success rate {success_rate:.2%} is below 80%. {correct_count}/{len(financial_queries)} correct."

    def test_route_query_comparison_keywords(self):
        """Test routing queries with comparison keywords."""
        comparison_queries = [
            "Show values greater than 100",
            "Find prices less than 50",
            "Get data between dates",
            "Show top 10 results",
            "Find bottom performers",
            "Compare these values"
        ]
        
        correct_count = 0
        for query in comparison_queries:
            result = route_query(query)
            if result == "data":
                correct_count += 1
            else:
                print(f"Query '{query}' routed to '{result}' instead of 'data'")
        
        # Allow 80% success rate
        success_rate = correct_count / len(comparison_queries)
        assert success_rate >= 0.8, f"Comparison keyword routing success rate {success_rate:.2%} is below 80%. {correct_count}/{len(comparison_queries)} correct."

    def test_route_query_multiple_keywords(self):
        """Test routing queries with multiple data keywords."""
        multi_keyword_queries = [
            "Show me the price and volume data",
            "Query the table for financial information",
            "Get the sum and average of stock prices",
            "List all tables with their row counts",
            "Compare the minimum and maximum values"
        ]
        
        correct_count = 0
        for query in multi_keyword_queries:
            result = route_query(query)
            if result == "data":
                correct_count += 1
            else:
                print(f"Query '{query}' routed to '{result}' instead of 'data'")
        
        # Allow 80% success rate
        success_rate = correct_count / len(multi_keyword_queries)
        assert success_rate >= 0.8, f"Multiple keyword routing success rate {success_rate:.2%} is below 80%. {correct_count}/{len(multi_keyword_queries)} correct."

