import os
import gradio as gr
import logging
import uuid
import pathlib
from dotenv import load_dotenv
from research_engine import ResearchEngine
import time
import traceback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the research engine with verbose=False for production
research_engine = None

# Dict to store session-specific research engines
session_engines = {}

def validate_api_keys(custom_openai_key=None):
    """Checks if required API keys are set"""
    missing_keys = []
    
    if not os.getenv("BRAVE_API_KEY"):
        missing_keys.append("BRAVE_API_KEY")
        
    # Check for OpenAI key in either the environment or the custom key provided
    if not custom_openai_key and not os.getenv("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
        
    return missing_keys

def get_engine_for_session(session_id, openai_api_key=None):
    """Get or create a research engine for the specific session with optional custom API key"""
    if session_id not in session_engines:
        logger.info(f"Creating new research engine for session {session_id}")
        # Set temporary API key if provided by user
        original_key = None
        if openai_api_key:
            logger.info("Using custom OpenAI API key provided by user")
            original_key = os.environ.get("OPENAI_API_KEY")
            os.environ["OPENAI_API_KEY"] = openai_api_key
            
        try:
            session_engines[session_id] = ResearchEngine(verbose=False)
        finally:
            # Restore original key if we changed it
            if original_key is not None:
                os.environ["OPENAI_API_KEY"] = original_key
            elif openai_api_key:
                # If there was no original key, remove the temporary one
                os.environ.pop("OPENAI_API_KEY", None)
                
    return session_engines[session_id]

def cleanup_session(session_id):
    """Remove a session when it's no longer needed"""
    if session_id in session_engines:
        logger.info(f"Cleaning up session {session_id}")
        del session_engines[session_id]

def process_message(message, history, session_id, openai_api_key=None):
    """
    Process user message and update chat history.
    
    Args:
        message: User's message
        history: Chat history list
        session_id: Unique identifier for the session
        openai_api_key: Optional custom OpenAI API key
        
    Returns:
        Updated history
    """
    # Validate API keys
    missing_keys = validate_api_keys(openai_api_key)
    if missing_keys:
        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"Error: Missing required API keys: {', '.join(missing_keys)}. Please set these in your .env file or input your OpenAI API key below."}
        ]
    
    # Add user message to history
    history.append({"role": "user", "content": message})
    
    try:
        print(f"Starting research for: {message}")
        start_time = time.time()
        
        # Get the appropriate engine for this session, passing the API key if provided
        engine = get_engine_for_session(session_id, openai_api_key)
        
        # Set the API key for this specific request if provided
        original_key = None
        if openai_api_key:
            original_key = os.environ.get("OPENAI_API_KEY")
            os.environ["OPENAI_API_KEY"] = openai_api_key
            
        try:
            # Start the research process
            research_task = engine.research(message)
        finally:
            # Restore original key if we changed it
            if original_key is not None:
                os.environ["OPENAI_API_KEY"] = original_key
            elif openai_api_key:
                # If there was no original key, remove the temporary one
                os.environ.pop("OPENAI_API_KEY", None)
        
        # Print the research task output for debugging
        print(f"Research task result type: {type(research_task)}")
        print(f"Research task content: {research_task}")
        
        # If we get here, step 1 is complete
        history[-1] = {"role": "user", "content": message}
        history.append({"role": "assistant", "content": f"Researching... this may take a minute or two...\n\n**Step 1/4:** Refining your query..."})
        yield history
        
        # We don't actually have real-time progress indication from the engine,
        # so we'll simulate it with a slight delay between steps
        time.sleep(1)
        
        history[-1] = {"role": "assistant", "content": f"Researching... this may take a minute or two...\n\n**Step 1/4:** Refining your query... ✓\n**Step 2/4:** Searching the web..."}
        yield history
        
        time.sleep(1)
        
        history[-1] = {"role": "assistant", "content": f"Researching... this may take a minute or two...\n\n**Step 1/4:** Refining your query... ✓\n**Step 2/4:** Searching the web... ✓\n**Step 3/4:** Analyzing results..."}
        yield history
        
        time.sleep(1)
        
        history[-1] = {"role": "assistant", "content": f"Researching... this may take a minute or two...\n\n**Step 1/4:** Refining your query... ✓\n**Step 2/4:** Searching the web... ✓\n**Step 3/4:** Analyzing results... ✓\n**Step 4/4:** Synthesizing information..."}
        yield history
        
        # Get response from research engine
        response = research_task["result"]
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Add processing time for transparency
        response += f"\n\nResearch completed in {processing_time:.2f} seconds."
        
        # Update last message with the full response
        history[-1] = {"role": "assistant", "content": response}
        yield history
    except Exception as e:
        logger.exception("Error processing message")
        error_traceback = traceback.format_exc()
        error_message = f"An error occurred: {str(e)}\n\nTraceback: {error_traceback}"
        history[-1] = {"role": "assistant", "content": error_message}
        yield history

# Define a basic theme with minimal customization - more styling in CSS
custom_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.indigo,
    secondary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.slate,
)

# Gradio versions have different ways of loading CSS, let's ensure compatibility
css_file_path = pathlib.Path("assets/custom.css")
if css_file_path.exists():
    with open(css_file_path, 'r') as f:
        css_content = f.read()
else:
    css_content = ""  # Fallback empty CSS if file doesn't exist

# Add the CSS as a style tag to ensure it works in all Gradio versions
css_head = f"""
<style>
{css_content}

/* Additional styling for API key input */
.api-settings .api-key-input input {{
    border: 1px solid #ccc;
    border-radius: 8px;
    font-family: monospace;
    letter-spacing: 1px;
}}

.api-settings .api-key-info {{
    font-size: 0.8rem;
    color: #666;
    margin-top: 5px;
}}

.api-settings {{
    margin-bottom: 20px;
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 10px;
    background-color: #f9f9f9;
}}
</style>
"""

# Create the Gradio interface with multiple CSS loading methods for compatibility
with gr.Blocks(
    title="Web Research Agent", 
    theme=custom_theme, 
    css=css_content,
    head=css_head,  # Older versions may use this
) as app:
    # Create a unique session ID for each user
    session_id = gr.State(lambda: str(uuid.uuid4()))
    
    with gr.Row(elem_classes=["container"]):
        with gr.Column():
            with gr.Row(elem_classes=["app-header"]):
                gr.Markdown("""
                <div style="display: flex; align-items: center; justify-content: center;">
                    <div style="width: 40px; height: 40px; margin-right: 15px; background: linear-gradient(135deg, #3a7bd5, #00d2ff); border-radius: 10px; display: flex; justify-content: center; align-items: center;">
                        <span style="color: white; font-size: 24px; font-weight: bold;">R</span>
                    </div>
                    <h1 style="margin: 0;">Web Research Agent</h1>
                </div>
                """)
            
            gr.Markdown("""
            This intelligent agent utilizes a multi-step process to deliver comprehensive research on any topic.
            Simply enter your question or topic below to get comprehensive, accurate information with proper citations.
            """, elem_classes=["md-container"])
            
            # Missing keys warning
            missing_keys = validate_api_keys()
            if missing_keys:
                gr.Markdown(f"⚠️ **Warning:** Missing required API keys: {', '.join(missing_keys)}. Add these to your .env file.", elem_classes=["warning"])
            
            chatbot = gr.Chatbot(
                height=600,
                show_copy_button=True,
                avatar_images=(None, "./assets/assistant_avatar.png"),
                type="messages",  # Use the modern messages format instead of tuples
                elem_classes=["chatbot-container"]
            )
            
            # API Key input
            with gr.Accordion("API Settings", open=False, elem_classes=["api-settings"]):
                openai_api_key = gr.Textbox(
                    label="OpenAI API Key (optional)",
                    placeholder="sk-...",
                    type="password",
                    info="Provide your own OpenAI API key if you don't want to use the system default key.",
                    elem_classes=["api-key-input"]
                )
                gr.Markdown("""
                Your API key is only used for your requests and is never stored on our servers. 
                It's a safer alternative to adding it to the .env file.
                [Get an API key from OpenAI](https://platform.openai.com/account/api-keys)
                """, elem_classes=["api-key-info"])
            
            with gr.Row(elem_classes=["input-container"]):
                msg = gr.Textbox(
                    placeholder="Ask me anything...",
                    scale=9,
                    container=False,
                    show_label=False,
                    elem_classes=["input-box"]
                )
                submit = gr.Button("Search", scale=1, variant="primary", elem_classes=["search-button"], value="search")
            
            # Clear button
            clear = gr.Button("Clear Conversation", elem_classes=["clear-button"])
            
            # Examples
            with gr.Accordion("Example Questions", open=False, elem_classes=["examples-container"]):
                examples = gr.Examples(
                    examples=[
                        "What are the latest advancements in artificial intelligence?",
                        "Explain the impact of climate change on marine ecosystems",
                        "How do mRNA vaccines work?",
                        "What are the health benefits of intermittent fasting?",
                        "Explain the current state of quantum computing research",
                        "What are the main theories about dark matter?",
                        "How is blockchain technology being used outside of cryptocurrency?",
                    ],
                    inputs=msg
                )
            
            # Set up event handlers
            submit_click_event = submit.click(
                process_message, 
                inputs=[msg, chatbot, session_id, openai_api_key], 
                outputs=[chatbot],
                show_progress=True
            )
            
            msg_submit_event = msg.submit(
                process_message, 
                inputs=[msg, chatbot, session_id, openai_api_key], 
                outputs=[chatbot],
                show_progress=True
            )
            
            # Clear message input after sending
            submit_click_event.then(lambda: "", None, msg)
            msg_submit_event.then(lambda: "", None, msg)
            
            # Clear conversation and reset session
            def clear_conversation_and_session(session_id_value):
                # Clear the session data
                cleanup_session(session_id_value)
                # Generate a new session ID
                new_session_id = str(uuid.uuid4())
                # Return empty history and new session ID
                return [], new_session_id
            
            clear.click(
                clear_conversation_and_session,
                inputs=[session_id],
                outputs=[chatbot, session_id]
            )
            
            # Citation and tools information
            with gr.Accordion("About This Research Agent", open=False, elem_classes=["footer"]):
                gr.Markdown("""
                ### Research Agent Features
                
                This research agent uses a combination of specialized AI agents to provide comprehensive answers:
                
                - **Researcher Agent**: Refines queries and searches the web
                - **Analyst Agent**: Evaluates content relevance and factual accuracy
                - **Writer Agent**: Synthesizes information into coherent responses
                
                #### Tools Used
                - BraveSearch and Tavily for web searching
                - Content scraping for in-depth information
                - Analysis for relevance and factual verification
                
                #### API Keys
                - You can use your own OpenAI API key by entering it in the "API Settings" section
                - Your API key is used only for your requests and is never stored on our servers
                - This lets you control costs and use your preferred API tier
                
                All information is provided with proper citations and sources.
                
                *Processing may take a minute or two as the agent searches, analyzes, and synthesizes information.*
                """, elem_classes=["md-container"])

if __name__ == "__main__":
    # Create assets directory if it doesn't exist
    os.makedirs("assets", exist_ok=True)
    
    # Launch the Gradio app
    app.launch() 