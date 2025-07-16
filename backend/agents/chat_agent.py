"""
Chat Agent for handling general, non-dataset-related queries.
"""
import logging
from typing import Dict, Any, Generator
from langchain_openai import ChatOpenAI
import time

logger = logging.getLogger(__name__)

def run_chat_agent(query: str) -> Generator[Dict[str, Any], None, None]:
    """
    Streams a general chat response using a simple generator for streaming test.
    """
    logger.info(f"Running chat agent for query: {query}")
    yield {"type": "start_general_response"}
    llm = ChatOpenAI(temperature=0, streaming=True)
    full_text = ""
    for chunk in llm.stream(query):
        content = getattr(chunk, 'content', str(chunk))
        if content:
            logger.info(f"Streaming token: {content!r}")
            full_text += content
            yield {"type": "chat_token", "content": content}
    yield {"type": "chat_done"}
    logger.info(f"Yielding SSE: {{'type': 'chat_done'}}")
    yield {
        "type": "final_result",
        "summary": full_text
    }
    logger.info(f"Yielding SSE: {{'type': 'final_result', 'summary': {full_text!r}}}")