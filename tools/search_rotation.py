import random
import time
from typing import List, Dict, Any, Optional, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class SearchRotationArgs(BaseModel):
    """Input schema for SearchRotationTool."""
    query: str = Field(..., description="The search query to look up")

class SearchRotationTool(BaseTool):
    """
    Tool for rotating between multiple search engines with a limit on searches per query.
    
    This tool alternates between different search engines and enforces a maximum
    number of searches per query to manage API usage and costs.
    """
    name: str = Field(
        default="Web Search Rotation",
        description="Search the internet using multiple search engines in rotation"
    )
    description: str = Field(
        default="Use this tool to search for information on the internet using different search engines in rotation.",
        description="Description of the search rotation tool"
    )
    
    search_tools: List[BaseTool] = Field(
        default=[],
        description="List of search tools to rotate between"
    )
    max_searches_per_query: int = Field(
        default=5,
        description="Maximum number of searches allowed per query"
    )
    cache_timeout: int = Field(
        default=300,  # 5 minutes
        description="How long to cache results for similar queries in seconds"
    )
    
    args_schema: Type[BaseModel] = SearchRotationArgs
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.search_tools:
            raise ValueError("At least one search tool must be provided")
        self._search_count = 0
        self._current_search_query = None
        self._last_used_tool = None
        self._cache = {}  # Simple cache for recent queries
        self._last_search_time = {}  # Track when each tool was last used
        
        # Log available search tools
        tool_names = [tool.name for tool in self.search_tools]
        print(f"SearchRotationTool initialized with tools: {', '.join(tool_names)}")
    
    def _run(self, query: str) -> str:
        """
        Execute a web search using a rotation of search engines.
        
        Args:
            query: The search query to look up
            
        Returns:
            String containing the search results
        """
        print(f"SearchRotationTool executing search for: '{query}'")
        
        # Check cache first for very similar queries
        for cached_query, (timestamp, result) in list(self._cache.items()):
            # Simple similarity check - if query is very similar to a cached query
            if self._is_similar_query(query, cached_query):
                # Check if cache is still valid
                if time.time() - timestamp < self.cache_timeout:
                    print(f"Using cached result for similar query: '{cached_query}'")
                    return f"{result}\n\n[Cached result from similar query: '{cached_query}']"
                else:
                    # Remove expired cache entries to prevent cache bloat
                    print(f"Cache expired for query: '{cached_query}'")
                    self._cache.pop(cached_query, None)
        
        # Reset counter if this is a new query
        if not self._is_similar_query(self._current_search_query, query):
            print(f"New search query detected. Resetting search count.")
            self._current_search_query = query
            self._search_count = 0
        
        # Check if we've reached the search limit
        if self._search_count >= self.max_searches_per_query:
            print(f"Search limit reached ({self._search_count}/{self.max_searches_per_query})")
            return (f"Search limit reached. You've performed {self._search_count} searches "
                    f"for this query. Maximum allowed is {self.max_searches_per_query}.")
        
        # Select the most appropriate search tool based on usage and delay
        search_tool = self._select_optimal_tool()
        print(f"Selected search tool: {search_tool.name}")
        
        # Keep track of which tools we've tried for this specific search attempt
        tried_tools = set()
        max_retry_attempts = min(3, len(self.search_tools))
        retry_count = 0
        
        while retry_count < max_retry_attempts:
            tried_tools.add(search_tool.name)
            
            try:
                # Execute the search
                print(f"Using Tool: {search_tool.name}")
                start_time = time.time()
                result = search_tool.run(query)
                search_time = time.time() - start_time
                
                # Basic validation of result - check if it's empty or error message
                if not result or "error" in result.lower() or len(result.strip()) < 20:
                    # Result might be invalid, try another tool if available
                    print(f"Invalid or error result from {search_tool.name}. Trying another tool.")
                    retry_count += 1
                    search_tool = self._select_next_tool(tried_tools)
                    if not search_tool:  # No more tools to try
                        print("All search tools failed. No more tools to try.")
                        return "All search tools failed to provide meaningful results for this query."
                    continue
                
                # Valid result obtained
                print(f"Valid result obtained from {search_tool.name} in {search_time:.2f}s")
                
                # Update tracking
                self._last_used_tool = search_tool
                self._last_search_time[search_tool.name] = time.time()
                
                # Cache the result
                self._cache[query] = (time.time(), result)
                
                # Increment the counter
                self._search_count += 1
                print(f"Search count incremented to {self._search_count}/{self.max_searches_per_query}")
                
                # Add usage information
                searches_left = self.max_searches_per_query - self._search_count
                usage_info = f"\n\nSearch performed using {search_tool.name} in {search_time:.2f}s. "
                usage_info += f"Searches used: {self._search_count}/{self.max_searches_per_query}. "
                usage_info += f"Searches remaining: {max(0, searches_left)}."
                
                return f"{result}\n{usage_info}"
            
            except Exception as e:
                # If this search tool fails, try another one
                print(f"Exception in {search_tool.name}: {str(e)}")
                retry_count += 1
                search_tool = self._select_next_tool(tried_tools)
                if not search_tool:  # No more tools to try
                    print("All search tools failed with exceptions. No more tools to try.")
                    return f"Error searching with all available search engines: {str(e)}"
        
        # If we've exhausted our retry attempts
        print(f"Failed after {retry_count} retry attempts")
        return "Failed to get search results after multiple attempts with different search engines."
    
    def _select_next_tool(self, tried_tools: set) -> Optional[BaseTool]:
        """Select the next tool that hasn't been tried yet."""
        available_tools = [t for t in self.search_tools if t.name not in tried_tools]
        if not available_tools:
            return None
        
        # Sort by last used time (oldest first) if we have that data
        if self._last_search_time:
            available_tools.sort(key=lambda t: self._last_search_time.get(t.name, 0))
        
        return available_tools[0] if available_tools else None
    
    def _select_optimal_tool(self) -> BaseTool:
        """Select the best tool based on recent usage patterns."""
        current_time = time.time()
        
        # If we have no history or all tools used recently, pick randomly with weights
        if not self._last_used_tool or not self._last_search_time:
            return random.choice(self.search_tools)
        
        # Try to avoid using the same tool twice in a row
        available_tools = [t for t in self.search_tools if t != self._last_used_tool]
        
        # If we have multiple tools available, choose the one used least recently
        if available_tools:
            # Sort by last used time (oldest first)
            available_tools.sort(key=lambda t: self._last_search_time.get(t.name, 0))
            return available_tools[0]
        
        # If only one tool available, use it
        return self.search_tools[0]
    
    def _is_similar_query(self, query1, query2):
        """Check if two queries are similar enough to use cached results."""
        if not query1 or not query2:
            return False
            
        # Convert to lowercase and remove common filler words
        q1 = query1.lower()
        q2 = query2.lower()
        
        # If the strings are identical
        if q1 == q2:
            return True
            
        # Remove common filler words to focus on meaningful terms
        filler_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                       'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'like',
                       'through', 'over', 'before', 'between', 'after', 'since', 'without',
                       'under', 'within', 'along', 'following', 'across', 'behind',
                       'beyond', 'plus', 'except', 'but', 'up', 'down', 'off', 'on', 'me', 'you'}
        
        # Clean and tokenize
        def clean_and_tokenize(q):
            # Remove punctuation
            q = ''.join(c for c in q if c.isalnum() or c.isspace())
            # Tokenize
            tokens = q.split()
            # Remove filler words
            return {word for word in tokens if word.lower() not in filler_words and len(word) > 1}
        
        words1 = clean_and_tokenize(q1)
        words2 = clean_and_tokenize(q2)
        
        # If either query has no significant words after cleaning, they're not similar
        if not words1 or not words2:
            return False
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        # If the queries are short, we require more overlap
        min_words = min(len(words1), len(words2))
        max_words = max(len(words1), len(words2))
        
        # For short queries, use strict similarity threshold
        if min_words <= 3:
            # For very short queries, require almost exact match
            return intersection / union > 0.8
        # For normal length queries
        elif min_words <= 6:
            return intersection / union > 0.7
        # For longer queries
        else:
            # Check both Jaccard similarity and absolute intersection size
            # For long queries, having many words in common is important
            absolute_overlap_threshold = min(5, min_words // 2)
            return (intersection / union > 0.6) or (intersection >= absolute_overlap_threshold) 