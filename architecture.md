# Web Research Agent Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                               Gradio Interface                                │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Research Engine                                  │
│                                                                               │
│   ┌───────────────────────────────────────────────────────────────────────┐  │
│   │                        Conversation History                            │  │
│   └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│   ┌─────────────┐              ┌─────────────┐              ┌─────────────┐  │
│   │  Researcher │◄────────────►│   Analyst   │◄────────────►│    Writer   │  │
│   │    Agent    │              │    Agent    │              │    Agent    │  │
│   └──────┬──────┘              └──────┬──────┘              └──────┬──────┘  │
│          │                            │                            │          │
│          ▼                            ▼                            ▼          │
│   ┌─────────────┐              ┌─────────────┐              ┌─────────────┐  │
│   │ Search      │              │   Scrape    │              │ Information │  │
│   │ Rotation    │              │ Website Tool│              │ Synthesis   │  │
│   │ Tool        │              └──────┬──────┘              └─────────────┘  │
│   └─────────────┘                     │                                       │
│                                       ▼                                       │
│                                ┌─────────────┐                                │
│                                │   Content   │                                │
│                                │  Analyzer   │                                │
│                                └─────────────┘                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Research Flow

1. **User Input**
   - User enters a query in the Gradio interface
   - Query is validated for legitimacy and processed by the system

2. **Query Refinement** (Researcher Agent)
   - Original query is analyzed and refined for optimal search results
   - Ambiguous terms are clarified and search intent is identified
   - Refined query is prepared for web search with improved keywords

3. **Web Search** (Researcher Agent + Search Rotation Tool)
   - Search Rotation Tool executes search using multiple search engines
   - Rate limiting is implemented to avoid API throttling
   - Search is performed with a maximum of 5 searches per query
   - Results are cached for similar queries to improve efficiency
   - Search results are collected with URLs and snippets

4. **Content Scraping** (Analyst Agent + ScrapeWebsiteTool)
   - ScrapeWebsiteTool extracts content from search result URLs
   - HTML content is parsed to extract meaningful text
   - Raw content is prepared for analysis and evaluation

5. **Content Analysis** (Analyst Agent + ContentAnalyzerTool)
   - Content is analyzed for relevance to the query (scores 0-10)
   - Factuality and quality are evaluated (scores 0-10)
   - Irrelevant or low-quality content is filtered out
   - Content is organized by relevance and information value

6. **Response Creation** (Writer Agent)
   - Analyzed content is synthesized into a comprehensive response
   - Information is organized logically with a clear structure
   - Contradictory information is reconciled when present
   - Citations are added in [1], [2] format with proper attribution
   - Source URLs are included for reference and verification

7. **Result Presentation**
   - Final response with citations is displayed to the user
   - Conversation history is updated and maintained per session
   - Results can be saved to file if requested

## System Architecture

- **Multi-Agent System**: Three specialized agents work together with distinct roles
- **Stateless Design**: Each research request is processed independently
- **Session Management**: User sessions maintain separate conversation contexts
- **API Integration**: Multiple search APIs with fallback mechanisms
- **Memory**: All agents maintain context throughout the research process
- **Tool Abstraction**: Search and analysis tools are modular and interchangeable
- **Error Handling**: Comprehensive error handling at each processing stage
- **Rate Limiting**: API calls are rate-limited to prevent throttling

## Technical Implementation

- **Frontend**: Gradio web interface with real-time feedback
- **Backend**: Python-based research engine with modular components
- **Tools**: 
  - Search Rotation Tool (supports multiple search engines)
  - Rate Limited Tool Wrapper (prevents API throttling)
  - Content Analyzer Tool (evaluates relevance and factuality)
  - Scrape Website Tool (extracts content from URLs)
- **Deployment**: Compatible with Hugging Face Spaces for online access
- **Caching**: Results are cached to improve performance and reduce API calls 