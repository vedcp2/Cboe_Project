"""
Defines the /ask-data-agent-streaming endpoint for streaming AI-powered data query responses. Integrates with the data agent to provide real-time reasoning and results.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import logging
from backend.models.schemas import Query
from backend.server.streaming import stream_query_response

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ask-data-agent-streaming")
def run_data_agent_streaming(q: Query):
    """
    Stream AI-powered data query responses and reasoning steps to the client.
    Args:
        q (Query): Query model containing the user's question.
    Returns:
        StreamingResponse: Server-sent events (SSE) stream of reasoning steps and results.
    """
    return StreamingResponse(
        stream_query_response(q.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    ) 