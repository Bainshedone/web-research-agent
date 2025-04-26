import os
import sys
from dotenv import load_dotenv
from crewai_tools import BraveSearchTool
from tools import TavilySearchTool, RateLimitedToolWrapper, SearchRotationTool

# Load environment variables
load_dotenv()

def validate_api_keys():
    """Checks if required API keys are set"""
    missing_keys = []
    
    if not os.getenv("BRAVE_API_KEY"):
        missing_keys.append("BRAVE_API_KEY")
        
    if not os.getenv("TAVILY_API_KEY"):
        missing_keys.append("TAVILY_API_KEY")
        
    return missing_keys

def main():
    # Check for API keys
    missing_keys = validate_api_keys()
    if missing_keys:
        print(f"Error: Missing required API keys: {', '.join(missing_keys)}")
        print("Please set these in your .env file.")
        sys.exit(1)
    
    # Initialize search tools
    brave_search_tool = BraveSearchTool(
        n_results=3,
        save_file=False
    )
    
    tavily_search_tool = TavilySearchTool(
        max_results=3,
        search_depth="basic"
    )
    
    # Add rate limiting to each search tool
    rate_limited_brave_search = RateLimitedToolWrapper(tool=brave_search_tool, delay=10)  # Reduced delay for testing
    rate_limited_tavily_search = RateLimitedToolWrapper(tool=tavily_search_tool, delay=10)  # Reduced delay for testing
    
    # Create the search rotation tool
    search_rotation_tool = SearchRotationTool(
        search_tools=[rate_limited_brave_search, rate_limited_tavily_search],
        max_searches_per_query=5
    )
    
    # Get user query
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your search query: ")
    
    # Perform searches
    print(f"Searching for: '{query}'")
    print("Will perform up to 5 searches using Brave and Tavily in rotation")
    print("-" * 50)
    
    # First search
    result1 = search_rotation_tool.run(query)
    print(result1)
    print("\n" + "-" * 50)
    
    # Modified query
    modified_query = f"{query} recent news"
    print(f"Searching for modified query: '{modified_query}'")
    
    # Second search
    result2 = search_rotation_tool.run(modified_query)
    print(result2)
    print("\n" + "-" * 50)
    
    # Try exceeding the limit with multiple searches for the same query
    print(f"Attempting additional searches for: '{query}'")
    
    for i in range(4):
        print(f"\nAttempt {i+1}:")
        result = search_rotation_tool.run(query)
        print(result)
        print("-" * 50)
    
    print("\nTest complete!")

if __name__ == "__main__":
    main() 