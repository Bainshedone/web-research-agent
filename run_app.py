"""
Run script for the Web Research Agent with error handling
"""
import os
import sys
import traceback

# Ensure assets directory exists
os.makedirs("assets", exist_ok=True)

try:
    # Try importing gradio first to check version and availability
    import gradio as gr
    print(f"Using Gradio version: {gr.__version__}")
    
    # Then run the main app
    from app import app
    
    # Launch the app with debugging enabled
    app.launch(share=False, debug=True)  # Enable debug mode to see error traces
    
except ImportError as e:
    print("Error: Missing required packages.")
    print(f"Details: {e}")
    print("\nPlease install the required packages:")
    print("pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"Error: {e}")
    print("\nTraceback:")
    traceback.print_exc()
    
    # Special handling for common Gradio errors
    if "got an unexpected keyword argument" in str(e):
        print("\nThis appears to be an issue with Gradio version compatibility.")
        print("The app is trying to use features not available in your installed Gradio version.")
        print("\nTry updating Gradio:")
        print("pip install --upgrade gradio")
    elif "CrewOutput" in str(e) or "dict object" in str(e):
        print("\nThis appears to be an issue with CrewAI output format.")
        print("The app is having trouble processing CrewAI outputs.")
        print("\nTry updating CrewAI:")
        print("pip install --upgrade crewai crewai-tools")
    
    sys.exit(1) 