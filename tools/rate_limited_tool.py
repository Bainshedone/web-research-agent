import time
from typing import Any, Dict, Optional, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, model_validator, create_model
import logging

logger = logging.getLogger(__name__)

class RateLimitedToolWrapper(BaseTool):
    """
    A wrapper tool that adds an optional time delay after executing another tool.
    Useful for enforcing rate limits on API calls or simply adding a pause.
    It also ensures that arguments are correctly passed to the wrapped tool.
    """
    name: str = Field(
        default="Rate Limited Tool Wrapper",
        description="A tool that wraps another tool to add a delay after execution"
    )
    description: str = Field(
        default="Wraps another tool to add a delay after execution, enforcing rate limits.",
        description="The tool's description that will be passed to the agent"
    )
    tool: BaseTool = Field(
        ...,
        description="The tool to be wrapped with rate limiting"
    )
    delay: float = Field(
        default=0.0,
        description="Delay in seconds to wait after tool execution (0 means no delay)",
        ge=0.0
    )

    # Create a simple args schema for fallback
    class RateLimitedToolArgs(BaseModel):
        query: str = Field(..., description="The search query to pass to the wrapped tool")

    def __init__(self, **data):
        # Store the original args_schema if available
        tool = data.get('tool')
        
        # Set args_schema directly in data before initialization
        if tool and hasattr(tool, 'args_schema') and tool.args_schema is not None:
            if isinstance(tool.args_schema, type) and issubclass(tool.args_schema, BaseModel):
                data['args_schema'] = tool.args_schema
            else:
                data['args_schema'] = self.RateLimitedToolArgs
        else:
            data['args_schema'] = self.RateLimitedToolArgs
        
        super().__init__(**data)
        
    def _run(self, query: str) -> str:
        """
        Run the wrapped tool with the query parameter and then pause for the specified delay.
        
        Args:
            query: The query string to pass to the wrapped tool.
            
        Returns:
            The result from the wrapped tool.
        """
        logger.debug(f"RateLimitedToolWrapper: Running tool '{self.tool.name}' with query: {query}")

        try:
            # Call the tool's run method with the query
            result = self.tool.run(query)
            
        except Exception as e:
            logger.error(f"Exception running wrapped tool '{self.tool.name}': {e}")
            # Fall back to trying the _run method directly if the run method fails
            try:
                if hasattr(self.tool, '_run'):
                    logger.warning(f"Falling back to direct _run call for tool '{self.tool.name}'")
                    result = self.tool._run(query)
                else:
                    raise e
            except Exception as inner_e:
                logger.error(f"Fallback also failed for tool '{self.tool.name}': {inner_e}")
                raise inner_e

        # Enforce the delay only if greater than 0
        if self.delay > 0:
            logger.info(f"Rate limit enforced: Waiting {self.delay:.2f} seconds after running {self.tool.name}.")
            time.sleep(self.delay)

        return result