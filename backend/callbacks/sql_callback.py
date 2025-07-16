import logging
from langchain.callbacks.base import BaseCallbackHandler
import queue

class StreamingSQLCaptureCallbackHandler(BaseCallbackHandler):
    """
    Callback handler to capture and stream reasoning steps and the final SQL query from the SQL agent.
    """
    def __init__(self, stream_queue: 'queue.Queue' = None):
        self.reasoning_steps = []
        self.sql_query = None
        self.logger = logging.getLogger(__name__)
        self.stream_queue = stream_queue
        self.logger.info(f"StreamingSQLCaptureCallbackHandler initialized with stream_queue: {stream_queue is not None}")
        
        # Test the queue immediately
        if stream_queue is not None:
            test_item = {"type": "test", "message": "Callback initialized"}
            self.logger.info(f"Testing queue with item: {test_item}")
            stream_queue.put(test_item)

    @property
    def ignore_chain(self) -> bool:
        return True

    @property
    def ignore_agent(self) -> bool:
        return False

    @property
    def ignore_llm(self) -> bool:
        return False

    @property
    def ignore_chat_model(self) -> bool:
        return False

    @property
    def ignore_tool(self) -> bool:
        return False

    @property
    def raise_error(self) -> bool:
        return False

    def _stream(self, item):
        if self.stream_queue is not None:
            self.logger.info(f"Streaming to queue: {item}")
            self.stream_queue.put(item)
        else:
            self.logger.info(f"No stream_queue provided, item not streamed: {item}")

    def on_text(self, text: str, **kwargs):
        """Stream meaningful thought steps only"""
        self.logger.info(f"on_text called with: {text!r}")
        # Filter out ANSI codes and empty strings
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_text = ansi_escape.sub('', text).strip()
        
        # Only stream non-empty, meaningful text as thoughts
        if clean_text and not clean_text.startswith('>') and not clean_text.startswith('Entering'):
            step = {
                "type": "thought",
                "content": clean_text
            }
            self.reasoning_steps.append(step)
            self.logger.info(f"Streaming thought step: {step}")
            self._stream({
                "type": "reasoning_step",
                "step": step
            })

    def on_agent_action(self, action, **kwargs):
        """Stream structured action information"""
        self.logger.info(f"on_agent_action called with: {action}")
        
        if hasattr(action, 'tool') and hasattr(action, 'tool_input'):
            # Create structured action step
            step = {
                "type": "action",
                "tool": action.tool,
                "input": str(action.tool_input)
            }
            self.reasoning_steps.append(step)
            self.logger.info(f"Streaming action step: {step}")
            self._stream({
                "type": "reasoning_step",
                "step": step
            })
            
            # Extract potential SQL query
            if isinstance(action.tool_input, str) and 'select' in action.tool_input.lower():
                self.logger.debug(f'Captured SQL query from action input: {action.tool_input}')
                self.sql_query = action.tool_input

    def on_tool_end(self, output, **kwargs):
        """Stream tool output as observation"""
        self.logger.info(f"on_tool_end called with: {output}")
        
        # Create structured observation step
        step = {
            "type": "observation",
            "content": str(output)
        }
        self.reasoning_steps.append(step)
        self.logger.info(f"Streaming observation step: {step}")
        self._stream({
            "type": "reasoning_step",
            "step": step
        })
