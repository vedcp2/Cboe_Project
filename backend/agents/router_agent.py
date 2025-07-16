"""
Router Agent for intelligent query classification and routing. The agent distinguishes between:
- Data queries: Questions requiring database access, SQL operations, or structured data analysis
- General queries: Conversational, philosophical, or non-data-related questions
"""
import logging
from typing import Literal
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# Load your LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

SYSTEM_PROMPT = """
You are a helpful assistant that classifies user questions as either 'data' or 'general'.

- Return 'data' if the question relates to database queries, structured information, SQL, or involves retrieving, summarizing, or comparing stored numerical/textual data.
- Return 'general' if the question is conversational, philosophical, hypothetical, or not related to structured data retrieval.

Only return one of the two values: 'data' or 'general'. No explanations.
"""

def route_query(query: str) -> Literal["general", "data"]:
    """
    Uses an LLM to classify the query as 'general' or 'data'.
    """
    logger.info(f"Routing query via LLM: {query}")
    try:
        response = llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": query.strip()}
        ])
        classification = response.content.strip().lower()
        if classification not in {"data", "general"}:
            logger.warning(f"Unexpected classification: {classification}")
            return "general"
        return classification
    except Exception as e:
        logger.error(f"LLM routing failed: {e}")
        return "general"
