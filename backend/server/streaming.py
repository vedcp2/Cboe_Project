"""
Handles routing between SQL and chat agents, managing queues
for live streaming of agent reasoning steps and results via Server-Sent Events (SSE).
"""
import logging
import time
from typing import Dict, Any, Generator
from backend.agents.router_agent import route_query
from backend.agents.sql_agent import run_sql_agent
from backend.agents.chat_agent import run_chat_agent
import queue
import threading
import json
import datetime

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

def format_sse(data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(data, cls=DateTimeEncoder)}\n\n"

def stream_query_response(query: str) -> Generator[str, None, None]:
    """
    Central streaming orchestrator. Routes the query and streams agent responses using a queue and background thread for live streaming.
    """
    logger.info(f"Streaming orchestrator received query: {query}")
    intent = route_query(query)
    if intent == "data":
        # Use queue/thread for SQL agent
        q = queue.Queue()
        def run_agent():
            try:
                for item in run_sql_agent(query, stream_queue=q):
                    logger.info(f"SQL agent yielded item: {item}")
                    q.put(item)
            except Exception as e:
                logger.error(f"Error in streaming orchestrator: {e}")
                q.put({"type": "error", "content": str(e)})
            finally:
                logger.info("SQL agent finished, putting sentinel")
                q.put(None)  # Sentinel to signal end
        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()
        logger.info("SQL agent thread started")
        start_time = time.time()
        while True:
            try:
                item = q.get(timeout=0.5)
                logger.info(f"Got item from queue: {item}")
            except queue.Empty:
                if not thread.is_alive():
                    logger.info("Thread is dead, breaking")
                    break
                if time.time() - start_time > 60:
                    logger.error("Query timed out after 60 seconds")
                    yield format_sse({"type": "error", "content": "Query timed out after 60 seconds"})
                    break
                continue
            if item is None:
                logger.info("Got sentinel, breaking")
                break
            logger.info(f"Yielding SSE for item: {item}")
            yield format_sse(item)
    else:
        logger.info(f"Intent: {intent}")
        # For chat agent, yield directly for true streaming
        try:
            for item in run_chat_agent(query):
                yield format_sse(item)
        except Exception as e:
            logger.error(f"Error in streaming orchestrator: {e}")
            yield format_sse({"type": "error", "content": str(e)}) 
        logger.info(f"Confirmation: {intent}")