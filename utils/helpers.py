import re
import json
from typing import Dict, Any, List, Optional

def is_valid_query(query: str) -> bool:
    """
    Validates if a search query is legitimate.
    
    Args:
        query: The search query to validate
        
    Returns:
        Boolean indicating if the query is valid
    """
    # Reject empty queries
    if not query or query.strip() == "":
        return False
    
    # Reject single emoji queries
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+"
    )
    
    stripped_query = emoji_pattern.sub(r'', query).strip()
    if not stripped_query and len(query) <= 5:  # Single emoji or very short
        return False
    
    # Reject random numbers only (at least 5 digits with no context)
    if re.match(r'^\d{5,}$', query.strip()):
        return False
    
    # Reject gibberish (no vowels in long string suggests gibberish)
    if len(query) > 10 and not re.search(r'[aeiouAEIOU]', query):
        return False
        
    return True

def format_research_results(search_results: List[Dict[str, Any]], 
                           scraped_contents: Dict[str, str],
                           analyzed_contents: Dict[str, Dict[str, Any]]) -> str:
    """
    Formats research results into a readable response with citations.
    
    Args:
        search_results: The list of search result items
        scraped_contents: Dict mapping URLs to scraped content
        analyzed_contents: Dict mapping URLs to analysis results
        
    Returns:
        Formatted response with citations
    """
    response_parts = []
    citations = []
    
    # Filter to only include relevant content based on analysis
    relevant_urls = {
        url: data 
        for url, data in analyzed_contents.items() 
        if data.get("relevance_score", 0) >= 5
    }
    
    # No relevant results
    if not relevant_urls:
        return "I couldn't find relevant information for your query. Could you try rephrasing or providing more details?"
    
    # Compile the response with relevant information
    for i, (url, data) in enumerate(relevant_urls.items(), 1):
        citations.append(f"[{i}] {url}")
        filtered_content = data.get("filtered_content", "")
        
        # Add the content with citation
        if filtered_content:
            response_parts.append(f"{filtered_content} [{i}]")
    
    # Combine everything
    response = "\n\n".join(response_parts)
    citation_text = "\n".join(citations)
    
    return f"{response}\n\nSources:\n{citation_text}"

def extract_citations(text: str) -> List[Dict[str, str]]:
    """
    Extract citations from formatted text.
    
    Args:
        text: Text with citation markers like [1], [2], etc.
        
    Returns:
        List of citation objects with citation number and referenced text
    """
    citations = []
    citation_pattern = r'\[(\d+)\]'
    
    matches = re.finditer(citation_pattern, text)
    for match in matches:
        citation_num = match.group(1)
        # Get the preceding text (limited to reasonable length)
        start_pos = max(0, match.start() - 100)
        cited_text = text[start_pos:match.start()].strip()
        if len(cited_text) == 100:  # Truncated
            cited_text = "..." + cited_text
        
        citations.append({
            "number": citation_num,
            "text": cited_text
        })
    
    return citations 