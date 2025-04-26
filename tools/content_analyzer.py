from typing import Optional, Dict, Any, Type
from crewai.tools import BaseTool
from pydantic import Field, BaseModel

# Define the input schema as a separate class
class ContentAnalyzerArgs(BaseModel):
    query: str = Field(
        ..., 
        description="The search query to compare content against"
    )
    content: str = Field(
        ..., 
        description="The content to analyze for relevance and factuality"
    )

class ContentAnalyzerTool(BaseTool):
    """
    A tool for analyzing content relevance and factuality.
    This tool uses LLM to judge the relevance and factual accuracy of content
    in relation to a specific query.
    """
    
    name: str = Field(
        default="Content Analyzer", 
        description="Name of the content analysis tool"
    )
    description: str = Field(
        default=(
            "Use this tool to analyze the relevance and factuality of content "
            "in relation to a specific query. "
            "It helps filter out irrelevant or potentially non-factual information."
        ),
        description="Description of what the content analyzer does"
    )
    
    # Define args_schema as a class attribute
    args_schema: Type[BaseModel] = ContentAnalyzerArgs
    
    def _run(self, query: str, content: str) -> Dict[str, Any]:
        """
        Analyze the content for relevance and factuality.
        
        Args:
            query: The original search query
            content: The content to analyze
            
        Returns:
            Dict with analysis results including:
            - relevance_score: A score from 0-10 indicating relevance
            - factuality_score: A score from 0-10 indicating factual reliability
            - filtered_content: The processed content with irrelevant parts removed
            - analysis: Brief explanation of the judgment
        """
        # The actual implementation will use the agent's LLM
        # via CrewAI's mechanism, returning the placeholders
        # for now which will be replaced during execution
        prompt = f"""
        You are a strict content judge evaluating web search results.
        
        QUERY: {query}
        CONTENT: {content}
        
        Analyze the content above with these criteria:
        1. Relevance to the query (score 0-10)
        2. Factual accuracy and reliability (score 0-10)
        3. Information quality
        
        For content scoring below 5 on relevance, discard it entirely.
        For content with factuality concerns, flag these specifically.
        
        PROVIDE YOUR ANALYSIS IN THIS FORMAT:
        {{
            "relevance_score": [0-10],
            "factuality_score": [0-10],
            "filtered_content": "The filtered and cleaned content, removing irrelevant parts",
            "analysis": "Brief explanation of your judgment"
        }}
        
        ONLY RETURN THE JSON, nothing else.
        """
        
        # This method will be handled by CrewAI's internal mechanism
        # For placeholder purposes during direct testing, we return example data.
        # In a real CrewAI run, the agent's LLM would process the prompt.
        return {
            "relevance_score": 7,  # Placeholder 
            "factuality_score": 8,  # Placeholder
            "filtered_content": content,  # Placeholder
            "analysis": "This is a placeholder analysis. The real analysis will be performed during execution."
        }
    
    class Config:
        """Pydantic config for the tool"""
        arbitrary_types_allowed = True
    
    def run(self, query: str, content: str) -> Dict[str, Any]:
        """Public method to run content analysis"""
        return self._run(query, content) 