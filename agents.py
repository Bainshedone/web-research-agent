from typing import List, Dict, Any, Optional
from crewai import Agent
from crewai_tools import BraveSearchTool, ScrapeWebsiteTool
from tools import ContentAnalyzerTool, RateLimitedToolWrapper, TavilySearchTool, SearchRotationTool

def create_researcher_agent(llm=None, verbose=True) -> Agent:
    """
    Creates a researcher agent responsible for query refinement and web search.
    
    Args:
        llm: Language model to use for the agent
        verbose: Whether to log agent activity
        
    Returns:
        Configured researcher agent
    """
    # Initialize search tools
    brave_search_tool = BraveSearchTool(
        n_results=5,
        save_file=False
    )
    
    # Initialize Tavily search tool
    # Requires a TAVILY_API_KEY in environment variables
    tavily_search_tool = TavilySearchTool(
        max_results=5,
        search_depth="basic",
        timeout=15  # Increase timeout for more reliable results
    )
    
    # Add minimal rate limiting to avoid API throttling
    # Set delay to 0 to disable rate limiting completely
    rate_limited_brave_search = RateLimitedToolWrapper(tool=brave_search_tool, delay=0)
    rate_limited_tavily_search = RateLimitedToolWrapper(tool=tavily_search_tool, delay=0)
    
    # Create the search rotation tool
    search_rotation_tool = SearchRotationTool(
        search_tools=[rate_limited_brave_search, rate_limited_tavily_search],
        max_searches_per_query=5  # Limit to 5 searches per query as requested
    )
    
    return Agent(
        role="Research Specialist",
        goal="Discover accurate and relevant information from the web",
        backstory=(
            "You are an expert web researcher with a talent for crafting effective search queries "
            "and finding high-quality information on any topic. Your goal is to find the most "
            "relevant and factual information to answer user questions. You have access to multiple "
            "search engines and know how to efficiently use them within the search limits."
        ),
        # Use the search rotation tool
        tools=[search_rotation_tool],
        verbose=verbose,
        allow_delegation=True,
        memory=True,
        llm=llm
    )

def create_analyst_agent(llm=None, verbose=True) -> Agent:
    """
    Creates an analyst agent responsible for content analysis and evaluation.
    
    Args:
        llm: Language model to use for the agent
        verbose: Whether to log agent activity
        
    Returns:
        Configured analyst agent
    """
    # Initialize tools
    scrape_tool = ScrapeWebsiteTool()
    content_analyzer = ContentAnalyzerTool()
    
    return Agent(
        role="Content Analyst",
        goal="Analyze web content for relevance, factuality, and quality",
        backstory=(
            "You are a discerning content analyst with a keen eye for detail and a strong "
            "commitment to factual accuracy. You excel at evaluating information and filtering "
            "out irrelevant or potentially misleading content. Your expertise helps ensure that "
            "only the most reliable information is presented."
        ),
        tools=[scrape_tool, content_analyzer],
        verbose=verbose,
        allow_delegation=True,
        memory=True,
        llm=llm
    )

def create_writer_agent(llm=None, verbose=True) -> Agent:
    """
    Creates a writer agent responsible for synthesizing information into coherent responses.
    
    Args:
        llm: Language model to use for the agent
        verbose: Whether to log agent activity
        
    Returns:
        Configured writer agent
    """    
    return Agent(
        role="Research Writer",
        goal="Create informative, factual, and well-cited responses to research queries",
        backstory=(
            "You are a skilled writer specializing in creating clear, concise, and informative "
            "responses based on research findings. You have a talent for synthesizing information "
            "from multiple sources and presenting it in a coherent and readable format, always with "
            "proper citations. You prioritize factual accuracy and clarity in your writing."
        ),
        verbose=verbose,
        allow_delegation=True,
        memory=True,
        llm=llm
    ) 