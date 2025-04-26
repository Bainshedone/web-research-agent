import os
import requests
import time
import hashlib
from typing import Dict, Any, Optional, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class TavilySearchArgs(BaseModel):
    """Input schema for TavilySearchTool."""
    query: str = Field(..., description="The search query to look up")

class TavilySearchTool(BaseTool):
    """
    Tool for performing web searches using the Tavily Search API.
    
    This tool sends a search query to Tavily and returns relevant search results.
    """
    name: str = Field(
        default="Tavily Web Search",
        description="Search the internet using Tavily"
    )
    description: str = Field(
        default="Use this tool to search for information on the internet using Tavily Search API.",
        description="Description of the Tavily search tool"
    )
    
    api_key: Optional[str] = Field(
        default=None,
        description="Tavily API key. If not provided, will look for TAVILY_API_KEY environment variable"
    )
    search_depth: str = Field(
        default="basic",
        description="The depth of the search, 'basic' or 'advanced'"
    )
    max_results: int = Field(
        default=5,
        description="Maximum number of search results to return (1-10)"
    )
    include_answer: bool = Field(
        default=False,
        description="Whether to include an AI-generated answer in the response"
    )
    timeout: int = Field(
        default=10,
        description="Timeout for the API request in seconds"
    )
    
    args_schema: Type[BaseModel] = TavilySearchArgs
    
    def __init__(self, **data):
        super().__init__(**data)
        self.api_key = self.api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            print("WARNING: Tavily API key is missing. The tool will return an error message when used.")
        self._cache = {}  # Simple in-memory cache
    
    def _run(self, query: str) -> str:
        """
        Execute a web search using Tavily.
        
        Args:
            query: The search query to look up
            
        Returns:
            String containing the search results
        """
        # Check if API key is missing
        if not self.api_key:
            return (
                "ERROR: Tavily API key is missing. Please set the TAVILY_API_KEY environment variable. "
                "Search cannot be performed without a valid API key."
            )
            
        # Check cache first
        cache_key = self._get_cache_key(query)
        if cache_key in self._cache:
            timestamp, result = self._cache[cache_key]
            # Cache valid for 30 minutes
            if time.time() - timestamp < 1800:
                return f"{result}\n\n[Cached Tavily result]"
        
        url = "https://api.tavily.com/search"
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": self.search_depth,
            "max_results": min(self.max_results, 10),  # Ensure we don't exceed API limits
            "include_answer": self.include_answer
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            
            if "results" not in result:
                return f"Error in search: {result.get('error', 'Unknown error')}"
            
            # Format the results
            formatted_results = self._format_results(result)
            
            # Cache the result
            self._cache[cache_key] = (time.time(), formatted_results)
            
            return formatted_results
        
        except requests.exceptions.Timeout:
            return "Error: Tavily search request timed out. Please try again later."
        except requests.exceptions.RequestException as e:
            return f"Error during Tavily search: {str(e)}"
    
    def _format_results(self, result: Dict[str, Any]) -> str:
        """Format the search results into a readable string."""
        output = []
        
        # Add the answer if included
        if "answer" in result and result["answer"]:
            output.append(f"Answer: {result['answer']}\n")
        
        # Add search results
        output.append("Search Results:")
        
        for i, r in enumerate(result.get("results", []), 1):
            title = r.get("title", "No Title")
            url = r.get("url", "No URL")
            content = r.get("content", "No Content").strip()
            
            result_text = f"\n{i}. {title}\n   URL: {url}\n   Content: {content}\n"
            output.append(result_text)
        
        return "\n".join(output)
    
    def _get_cache_key(self, query: str) -> str:
        """Generate a cache key for the given query."""
        # Include search parameters in the key
        params_str = f"{query}|{self.search_depth}|{self.max_results}|{self.include_answer}"
        return hashlib.md5(params_str.encode()).hexdigest() 