import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union

from crewai import Crew
from crewai.agent import Agent
from crewai.task import Task

from agents import create_researcher_agent, create_analyst_agent, create_writer_agent
from tasks import (
    create_query_refinement_task, 
    create_search_task, 
    create_content_scraping_task, 
    create_content_analysis_task, 
    create_response_writing_task
)
from utils import is_valid_query, format_research_results, extract_citations

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResearchEngine:
    """
    Main engine for web research using CrewAI.
    Orchestrates agents and tasks to provide comprehensive research results.
    """
    
    def __init__(self, llm=None, verbose=False):
        """
        Initialize the research engine.
        
        Args:
            llm: The language model to use for agents
            verbose: Whether to log detailed information
        """
        self.llm = llm
        self.verbose = verbose
        
        # Initialize agents
        logger.info("Initializing agents...")
        self.researcher = create_researcher_agent(llm=llm, verbose=verbose)
        self.analyst = create_analyst_agent(llm=llm, verbose=verbose)
        self.writer = create_writer_agent(llm=llm, verbose=verbose)
        
        # Chat history for maintaining conversation context
        self.chat_history = []
        
        logger.info("Research engine initialized with agents")
    
    def _validate_api_keys(self):
        """Validates that required API keys are present"""
        missing_keys = []
        
        if not os.getenv("BRAVE_API_KEY"):
            missing_keys.append("BRAVE_API_KEY")
            
        if not os.getenv("TAVILY_API_KEY"):
            missing_keys.append("TAVILY_API_KEY")
            
        if not os.getenv("OPENAI_API_KEY") and not self.llm:
            missing_keys.append("OPENAI_API_KEY or custom LLM")
            
        if missing_keys:
            logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
            if "TAVILY_API_KEY" in missing_keys:
                logger.warning("Tavily API key is missing - search functionality may be limited")
            if "BRAVE_API_KEY" in missing_keys:
                logger.warning("Brave API key is missing - search functionality may be limited")
            
            # Only raise error if all search API keys are missing
            if "BRAVE_API_KEY" in missing_keys and "TAVILY_API_KEY" in missing_keys:
                raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
        else:
            logger.info("All required API keys are present")
    
    def research(self, query: str, output_file=None) -> Dict[str, Any]:
        """
        Perform research on the given query.
        
        Args:
            query: The research query
            output_file: Optional file to save the research results
            
        Returns:
            Research results
        """
        logger.info(f"Research initiated for query: {query}")
        start_time = time.time()  # Initialize the start_time for tracking processing time
        
        try:
            self._validate_api_keys()
            logger.info(f"Starting research for query: {query}")
            
            # Add the query to chat history
            self.chat_history.append({"role": "user", "content": query})
            
            # Step 1: Initialize the crew
            logger.info("Initializing research crew...")
            crew = Crew(
                agents=[self.researcher],
                tasks=[create_query_refinement_task(self.researcher, query)],
                verbose=self.verbose,  # Use the instance's verbose setting
                process="sequential"
            )
            
            # Step 2: Start the research process
            logger.info("Starting research process...")
            refinement_result = crew.kickoff(inputs={"query": query})
            logger.info(f"Query refinement completed with result type: {type(refinement_result)}")
            logger.debug(f"Refinement result: {refinement_result}")
            
            # Extract the refined query
            refined_query = None
            try:
                logger.info(f"Attempting to extract refined query from result type: {type(refinement_result)}")
                
                # Handle CrewOutput object (new CrewAI format)
                if hasattr(refinement_result, '__class__') and refinement_result.__class__.__name__ == 'CrewOutput':
                    logger.info("Processing CrewOutput format refinement result")
                    
                    # Try to access raw attribute first (contains the raw output)
                    if hasattr(refinement_result, 'raw'):
                        refined_query = self._extract_query_from_string(refinement_result.raw)
                        logger.info(f"Extracted from CrewOutput.raw: {refined_query}")
                    
                    # Try to access as dictionary
                    elif hasattr(refinement_result, 'to_dict'):
                        crew_dict = refinement_result.to_dict()
                        logger.info(f"CrewOutput converted to dict: {crew_dict}")
                        
                        if 'result' in crew_dict:
                            refined_query = self._extract_query_from_string(crew_dict['result'])
                            logger.info(f"Extracted from CrewOutput dict result: {refined_query}")
                    
                    # Try string representation as last resort
                    else:
                        crew_str = str(refinement_result)
                        refined_query = self._extract_query_from_string(crew_str)
                        logger.info(f"Extracted from CrewOutput string representation: {refined_query}")
                
                # First try to access it as a dictionary (new CrewAI format)
                elif isinstance(refinement_result, dict):
                    logger.info("Processing dictionary format refinement result")
                    if "query" in refinement_result:
                        refined_query = refinement_result["query"]
                    elif "refined_query" in refinement_result:
                        refined_query = refinement_result["refined_query"]
                    elif "result" in refinement_result and isinstance(refinement_result["result"], str):
                        # Try to extract from nested result field
                        json_str = refinement_result["result"]
                        refined_query = self._extract_query_from_string(json_str)
                
                # Then try to access it as a string (old CrewAI format)
                elif isinstance(refinement_result, str):
                    logger.info("Processing string format refinement result")
                    refined_query = self._extract_query_from_string(refinement_result)
                
                else:
                    logger.warning(f"Unexpected refinement result format: {type(refinement_result)}")
                    # Try to extract information by examining the structure
                    try:
                        # Try to access common attributes
                        if hasattr(refinement_result, "result"):
                            result_str = str(getattr(refinement_result, "result"))
                            refined_query = self._extract_query_from_string(result_str)
                            logger.info(f"Extracted from .result attribute: {refined_query}")
                        elif hasattr(refinement_result, "task_output"):
                            task_output = getattr(refinement_result, "task_output")
                            refined_query = self._extract_query_from_string(str(task_output))
                            logger.info(f"Extracted from .task_output attribute: {refined_query}")
                        else:
                            # Last resort: convert to string and extract
                            refined_query = self._extract_query_from_string(str(refinement_result))
                            logger.info(f"Extracted from string representation: {refined_query}")
                    except Exception as attr_error:
                        logger.exception(f"Error trying to extract attributes: {attr_error}")
                        refined_query = query  # Fall back to original query
                    
                    logger.debug(f"Refinement result: {refinement_result}")
            except Exception as e:
                logger.exception(f"Error extracting refined query: {e}")
                refined_query = query  # Fall back to original query on error
            
            if not refined_query or refined_query.strip() == "":
                logger.warning("Refined query is empty, using original query")
                refined_query = query
                
            logger.info(f"Refined query: {refined_query}")
            
            # Step 3: Create tasks for research process
            logger.info("Creating research tasks...")
            search_task = create_search_task(self.researcher, refined_query)
            
            scrape_task = create_content_scraping_task(self.analyst, search_task)
            
            analyze_task = create_content_analysis_task(self.analyst, refined_query, scrape_task)
            
            write_task = create_response_writing_task(self.writer, refined_query, analyze_task)
            
            # Step 4: Create a new crew for the research tasks
            logger.info("Initializing main research crew...")
            research_crew = Crew(
                agents=[self.researcher, self.analyst, self.writer],
                tasks=[search_task, scrape_task, analyze_task, write_task],
                verbose=self.verbose,  # Use the instance's verbose setting
                process="sequential"
            )
            
            # Step 5: Start the research process
            logger.info("Starting main research process...")
            result = research_crew.kickoff()
            logger.info(f"Research completed with result type: {type(result)}")
            logger.debug(f"Research result: {result}")
            
            # Extract the result
            final_result = {"query": query, "refined_query": refined_query}
            
            # Handle different result types
            if isinstance(result, dict) and "result" in result:
                final_result["result"] = result["result"]
            # Handle CrewOutput object (new CrewAI format)
            elif hasattr(result, '__class__') and result.__class__.__name__ == 'CrewOutput':
                logger.info("Processing CrewOutput format result")
                
                # Try to access raw attribute first (contains the raw output)
                if hasattr(result, 'raw'):
                    final_result["result"] = result.raw
                    logger.info("Extracted result from CrewOutput.raw")
                
                # Try to access as dictionary
                elif hasattr(result, 'to_dict'):
                    crew_dict = result.to_dict()
                    if 'result' in crew_dict:
                        final_result["result"] = crew_dict['result']
                        logger.info("Extracted result from CrewOutput dict")
                
                # Use string representation as last resort
                else:
                    final_result["result"] = str(result)
                    logger.info("Used string representation of CrewOutput")
            else:
                # For any other type, use the string representation
                final_result["result"] = str(result)
                logger.info(f"Used string representation for result type: {type(result)}")
                
            logger.info("Research process completed successfully")
            
            # Save to file if requested
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(final_result, f, ensure_ascii=False, indent=2)
                    
            # Extract citations for easy access (if possible from the final string)
            citations = extract_citations(final_result["result"])
            
            # Calculate total processing time
            processing_time = time.time() - start_time
            logger.info(f"Research completed successfully in {processing_time:.2f} seconds")
            
            return {
                "result": final_result["result"],
                "success": True,
                "refined_query": refined_query,
                "citations": citations,
                "processing_time": processing_time
            }
        except Exception as e:
            logger.exception(f"Error in research process: {e}")
            return {
                "result": f"I encountered an error while researching your query: {str(e)}",
                "success": False,
                "reason": "research_error",
                "error": str(e)
            }
    
    def chat(self, message: str) -> str:
        """
        Handle a chat message, which could be a research query or a follow-up question.
        
        Args:
            message: The user's message
            
        Returns:
            The assistant's response
        """
        # Treat all messages as new research queries for simplicity
        try:
            research_result = self.research(message)
            return research_result["result"]
        except Exception as e:
            logger.exception(f"Error during research for message: {message}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    def clear_history(self):
        """Clear the chat history"""
        self.chat_history = []

    def _extract_query_from_string(self, text: str) -> str:
        """
        Extract refined query from text string, handling various formats including JSON embedded in strings.
        
        Args:
            text: The text to extract the query from
            
        Returns:
            The extracted query or None if not found
        """
        if not text:
            return None
            
        # Log the input for debugging
        logger.debug(f"Extracting query from: {text[:200]}...")
            
        # Try to parse as JSON first
        try:
            # Check if the entire string is valid JSON
            json_data = json.loads(text)
            
            # Check for known keys in the parsed JSON
            if isinstance(json_data, dict):
                if "refined_query" in json_data:
                    return json_data["refined_query"]
                elif "query" in json_data:
                    return json_data["query"]
                elif "result" in json_data and isinstance(json_data["result"], str):
                    # Try to recursively extract from nested result
                    return self._extract_query_from_string(json_data["result"])
        except json.JSONDecodeError:
            # Not valid JSON, continue with string parsing
            pass
            
        # Look for JSON blocks in the string
        try:
            import re
            # Match both markdown JSON blocks and regular JSON objects
            json_pattern = r'```(?:json)?\s*({[^`]*})```|({[\s\S]*})'
            json_matches = re.findall(json_pattern, text, re.DOTALL)
            
            for json_match in json_matches:
                # Handle tuple result from findall with multiple capture groups
                json_str = next((s for s in json_match if s), '')
                try:
                    json_data = json.loads(json_str)
                    if isinstance(json_data, dict):
                        if "refined_query" in json_data:
                            return json_data["refined_query"]
                        elif "query" in json_data:
                            return json_data["query"]
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Error parsing JSON blocks: {e}")
            
        # Check for common patterns in CrewAI output format
        patterns = [
            r'refined query[:\s]+([^\n]+)',
            r'query[:\s]+([^\n]+)',
            r'search(?:ed)? for[:\s]+[\'"]([^\'"]+)[\'"]',
            r'search(?:ing)? for[:\s]+[\'"]([^\'"]+)[\'"]',
            r'research(?:ing)? (?:about|on)[:\s]+[\'"]([^\'"]+)[\'"]',
            r'query is[:\s]+[\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text.lower())
                if match:
                    return match.group(1).strip()
            except Exception as e:
                logger.debug(f"Error matching pattern {pattern}: {e}")
                
        # Fall back to string parsing methods
        if "refined query:" in text.lower():
            return text.split("refined query:", 1)[1].strip()
        elif "query:" in text.lower():
            return text.split("query:", 1)[1].strip()
            
        # If all else fails, return the whole string
        return text 