"""
SQL Agent for natural language to SQL query conversion and execution.

Executes SQL queries against Snowflake,
formats results as markdown tables, and generates conversational summaries using LLM.
Supports streaming of reasoning steps and results via callback handlers.
"""
import logging
from typing import Dict, Any, Generator, List, Optional
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import SQLDatabaseToolkit, create_sql_agent
from langchain_community.utilities import SQLDatabase
from sqlalchemy import text
from backend.tools.sql_wrapper import get_snowflake_engine
from backend.callbacks.sql_callback import StreamingSQLCaptureCallbackHandler
import queue



llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
logger = logging.getLogger(__name__)

def format_results_markdown_table(query_results: List[List[Any]], columns: List[str]) -> str:
    if not query_results:
        return "No results."
    if not columns:
        columns = [f"Result {i+1}" for i in range(len(query_results[0]))]
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in query_results]
    return "\n".join([header, sep] + rows)

def run_sql_agent(query: str, stream_queue: Optional['queue.Queue'] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Runs the SQL agent, yields reasoning steps and final result. If stream_queue is provided, reasoning steps and final result are streamed live via the callback handler and queue.
    """
    logger.info(f"SQL agent starting with stream_queue: {stream_queue is not None}")
    callback = StreamingSQLCaptureCallbackHandler(stream_queue) if stream_queue is not None else StreamingSQLCaptureCallbackHandler()
    logger.info(f"Callback initialized: {callback}")
    engine = get_snowflake_engine()
    db = SQLDatabase(engine)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        handle_parsing_errors=True,
        agent_executor_kwargs={"callbacks": [callback]}
    )
    logger.info(f"Agent executor created with callbacks: {agent_executor.callbacks}")
    logger.info(f"Running SQL agent for query: {query}")
    
    agent_result = None
    error_message = None
    
    try:
        logger.info(f"About to run agent with enhanced query: {query}")
        agent_result = agent_executor.run(query, callbacks=[callback])
        logger.info(f"Agent finished with result: {agent_result}")
    except Exception as e:
        logger.error(f"SQL agent error: {e}")
        error_message = str(e)
        # Check if this is a parsing error indicating the agent couldn't find the data
        if "Could not parse LLM output" in error_message and "I don't know" in error_message:
            agent_result = "I apologize, but I could not find the requested data in the available database tables. The database does not appear to contain the information you're looking for."
        else:
            agent_result = f"An error occurred while processing your query: {error_message}"
    
    if stream_queue is None:
        for step in callback.reasoning_steps:
            yield {"type": "reasoning_step", "step": step}
    
    sql_query = callback.sql_query
    query_results = []
    columns = []
    
    if sql_query:
        try:
            with engine.connect() as conn:
                conn.execute(text("SET STATEMENT_TIMEOUT_IN_SECONDS = 30"))
                result = conn.execute(text(sql_query))
                rows = result.fetchall()
                columns = list(result.keys()) if hasattr(result, 'keys') else []
                query_results = [list(row) for row in rows]
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
    
    logger.info(f"SQL columns: {columns}")
    logger.info(f"SQL query_results: {query_results}")
    
    # Generate summary based on whether we have results or encountered an error
    if query_results and columns:
        table_md = format_results_markdown_table(query_results, columns)
        summary_prompt = f"""
You are a helpful data assistant. Here is the result of the SQL query you generated.

User question: {query}

SQL query: {sql_query}

SQL result:
{table_md}

Please summarize the result clearly and conversationally for the user.
"""
        logger.info(f"Markdown table sent to LLM:\n{table_md}")
        try:
            logger.info(f"Markdown table sent to LLM:\n{table_md}")
            summary = llm.invoke(summary_prompt)
            if hasattr(summary, 'content'):
                summary = summary.content
        except Exception as e:
            logger.error(f"LLM summarization error: {e}")
            summary = "Could not summarize the result."
    else:
        # No results or error occurred
        if error_message and "Could not parse LLM output" in error_message and "I don't know" in error_message:
            summary = "I apologize, but I could not find the requested data in the available database. The database does not appear to contain the information you're looking for."
        elif error_message:
            summary = f"I encountered an error while processing your query: {error_message}"
        elif sql_query and not query_results:
            # SQL query was executed but returned no results - override any agent fabrication
            summary = "I couldn't find any data matching your query. The database doesn't contain the information you're looking for, or the date range/criteria you specified may be outside the available data."
            agent_result = summary  # Override the agent's potentially fabricated response
        else:
            summary = agent_result or "No results found for your query."
    
    logger.info(f"Summary:\n{summary}")
    
    final_result = {
        "type": "final_result",
        "answer": agent_result,
        "summary": summary,
        "sql_query": sql_query,
        "query_results": query_results,
        "columns": columns
    }
    
    if stream_queue is not None:
        stream_queue.put(final_result)
    else:
        yield final_result 