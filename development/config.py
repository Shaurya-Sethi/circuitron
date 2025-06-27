"""
Configuration and setup for the Circuitron system.
Handles environment variables, logging, and tracing configuration.
"""

import logfire
from dotenv import load_dotenv

def setup_environment():
    """Initialize environment variables and configure logging/tracing."""
    load_dotenv()
    logfire.configure()
    logfire.instrument_openai_agents()

# Initialize when module is imported
setup_environment()
