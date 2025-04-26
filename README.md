# Web Research Agent

A powerful AI research assistant built with CrewAI that conducts comprehensive web research on any topic, providing factual, cited responses through a multi-agent approach.

## Overview

This application uses specialized AI agents working together to:
1. Refine search queries for optimal results
2. Search the web across multiple search engines
3. Analyze and verify content
4. Produce well-structured, factual responses with proper citations

## Setup Instructions

### Prerequisites

- Python 3.9+ (recommended: Python 3.11)
- API keys for:
  - OpenAI (required)
  - Brave Search (recommended)
  - Tavily Search (optional)

### Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/yourusername/web-research-agent.git
   cd web-research-agent
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   BRAVE_API_KEY=your_brave_api_key
   TAVILY_API_KEY=your_tavily_api_key
   VERBOSE=False  # Set to True for detailed logging
   ```

### Running the Application

Start the web interface:
```bash
python app.py
```

The application will be available at http://localhost:7860

## Common Issues & Troubleshooting

### Pydantic/CrewAI Compatibility Issues

If you encounter errors like:
```
AttributeError: 'property' object has no attribute 'model_fields'
```

Try the following fixes:

1. Update to the latest CrewAI version:
   ```bash
   pip install -U crewai crewai-tools
   ```

2. If issues persist, temporarily modify the `tools/rate_limited_tool.py` file to fix compatibility with Pydantic.

### Search API Rate Limits

- Brave Search API has a free tier limit of 1 request per minute and 2,000 requests per month
- The application implements rate limiting to prevent API throttling
- Research queries may take several minutes to complete due to these limitations

### Gradio Interface Issues

If the interface fails to load or throws errors:

1. Try installing a specific Gradio version:
   ```bash
   pip install gradio==4.26.0
   ```

2. Clear your browser cache to remove cached JavaScript files

3. Run the headless test script as an alternative:
   ```bash
   python test.py "Your research question"
   ```

## Advanced Usage

### Command Line Operation

Test the research engine without the web interface:
```
python test.py "Your research query here"
```

### Environment Variables

- `OPENAI_API_KEY`: Required for language model access
- `BRAVE_API_KEY`: Recommended for web search functionality
- `TAVILY_API_KEY`: Optional alternative search engine
- `VERBOSE`: Set to True/False to control logging detail

## Deployment

This project can be deployed to Hugging Face Spaces for web access.

### Hugging Face Spaces Deployment

1. **Create a new Space on Hugging Face**
   - Go to [Hugging Face Spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose a name and select "Gradio" as the SDK
   - Set visibility as needed

2. **Configure Environment Variables**
   - In Space settings, add required API keys as secrets

3. **Deploy Code**
   ```bash
   git clone https://huggingface.co/spaces/your-username/your-space-name
   cd your-space-name
   cp -r /path/to/web-research-agent/* .
   git add .
   git commit -m "Initial deployment"
   git push
   ```

### Security Notes

- Never commit your `.env` file or expose API keys
- Use repository secrets in Hugging Face Spaces
- Keep sensitive deployments private

## Development Structure

- `app.py`: Web interface and session management
- `research_engine.py`: Core research orchestration logic
- `agents.py`: Agent definitions and configurations
- `tools/`: Search and analysis tools
- `test.py`: Command-line testing utility 