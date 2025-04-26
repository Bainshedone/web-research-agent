from typing import Dict, List, Any
from crewai import Task
from crewai import Agent
from datetime import datetime
def create_query_refinement_task(researcher_agent: Agent, query: str) -> Task:
    """
    Creates a task for refining the user's query to optimize search results.
    
    Args:
        researcher_agent: The researcher agent to perform the task
        query: The original user query
        
    Returns:
        Task for query refinement
    """
    return Task(
        description=(
            f"Given the user query: '{query}', refine it to create an effective search query.Today is {datetime.now().strftime('%Y-%m-%d')}"
            f"Consider adding specificity, removing ambiguity, and using precise terms. But don't add anything that's not relevant to the query. i.e if you don't know the meaning of abbriviations then don't try to complete it. "
            f"If the query is invalid (just emojis, random numbers, gibberish, etc.), "
            f"flag it as invalid. Otherwise, return both the original query and your refined version."
            f"Don't add any extra information to the query. Just refine it."
            f"For Technical queries , don't try to make it a question. Just refine it."
            f"I want you to understand the user's query and refine it to be more specific and accurate do not add any extra information to the query which will change the meaning of the query."
        ),
        expected_output=(
            "Return your response in a structured format like this:\n"
            "```json\n"
            "{\n"
            '  "original_query": "original query here",\n'
            '  "refined_query": "improved query here",\n'
            '  "reasoning": "brief explanation of your refinements"\n'
            "}\n"
            "```\n\n"
            "Or if the query is invalid, return:\n"
            "```json\n"
            "{\n"
            '  "is_valid": false,\n'
            '  "reason": "explanation why the query is invalid"\n'
            "}\n"
            "```"
        ),
        agent=researcher_agent
    )

def create_search_task(researcher_agent: Agent, query: str) -> Task:
    """
    Creates a task for performing web search with the refined query.
    
    Args:
        researcher_agent: The researcher agent to perform the task
        query: The refined query to search
        
    Returns:
        Task for web search
    """
    return Task(
        description=(
            f"Using the refined query: '{query}', search the web to find the most relevant "
            f"and reliable information. Return a comprehensive list of search results, "
            f"including titles, snippets, and URLs. Focus on finding high-quality sources."
        ),
        expected_output=(
            "A JSON list of search results containing: "
            "1. Title of the page "
            "2. URL "
            "3. Snippet or description "
        ),
        agent=researcher_agent
    )

def create_content_scraping_task(analyst_agent: Agent, search_results: List[Dict[str, Any]]) -> Task:
    """
    Creates a task for scraping content from search result URLs.
    
    Args:
        analyst_agent: The analyst agent to perform the task
        search_results: The search results to scrape
        
    Returns:
        Task for content scraping
    """
    urls = [result.get("link", "") for result in search_results if "link" in result]
    urls_str = "\n".join(urls)
    
    return Task(
        description=(
            f"Scrape the content from these URLs:\n{urls_str}\n\n"
            f"For each URL, extract the main content, focusing on text relevant to the search query. "
            f"Ignore navigation elements, ads, and other irrelevant page components."
        ),
        expected_output=(
            "A JSON dictionary mapping each URL to its scraped content. For each URL, provide: "
            "1. The URL as the key "
            "2. The extracted content as the value"
        ),
        agent=analyst_agent
    )

def create_content_analysis_task(analyst_agent: Agent, query: str, scraped_contents: Dict[str, str]) -> Task:
    """
    Creates a task for analyzing and evaluating scraped content.
    
    Args:
        analyst_agent: The analyst agent to perform the task
        query: The original or refined query
        scraped_contents: Dict mapping URLs to scraped content
        
    Returns:
        Task for content analysis
    """
    return Task(
        description=(
            f"Analyze the relevance and factuality of the scraped content in relation to the query: '{query}'\n\n"
            f"For each piece of content, evaluate: "
            f"1. Relevance to the query (score 0-10) "
            f"2. Factual accuracy (score 0-10) "
            f"3. Filter out low-quality or irrelevant information"
        ),
        expected_output=(
            "A JSON dictionary with analysis for each URL containing: "
            "1. Relevance score (0-10) "
            "2. Factuality score (0-10) "
            "3. Filtered content (removing irrelevant parts) "
            "4. Brief analysis explaining your judgment"
        ),
        agent=analyst_agent
    )

def create_response_writing_task(writer_agent: Agent, query: str, analyzed_contents: Dict[str, Dict[str, Any]]) -> Task:
    """
    Creates a task for writing a comprehensive response based on analyzed content.
    
    Args:
        writer_agent: The writer agent to perform the task
        query: The original query
        analyzed_contents: Dict mapping URLs to analysis results
        
    Returns:
        Task for response writing
    """
    return Task(
        description=(
            f"Write a comprehensive response to the query: '{query}'\n\n"
            f"Use the analyzed content to craft a well-structured, informative response that directly "
            f"answers the user's query. Include proper citations for all information using [1], [2] format. "
            f"Focus on clarity, factual accuracy, and addressing all aspects of the query."
        ),
        expected_output=(
            "A comprehensive response that: "
            "1. Directly answers the user's query "
            "2. Uses information from the provided sources "
            "3. Includes citations in [1], [2] format for all factual information "
            "4. Provides a list of sources at the end"
        ),
        agent=writer_agent
    ) 