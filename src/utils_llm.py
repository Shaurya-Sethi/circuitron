"""OpenAI-based LLM utilities for Circuitron agent system."""
import os
from typing import Optional
from agents import Agent, ModelSettings
from dotenv import load_dotenv

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable not set")

MODEL_PLAN = os.getenv("MODEL_PLAN", "gpt-4o-mini")
MODEL_PART = os.getenv("MODEL_PART", "gpt-4o-mini") 
MODEL_CODE = os.getenv("MODEL_CODE", "gpt-4o")
MODEL_TEMP = float(os.getenv("MODEL_TEMP", "0.15"))

# Pre-configured agents for different pipeline stages
AGENT_PLAN = Agent(
    name="Planning Agent",
    instructions="You are a specialized planning agent for PCB design. Generate detailed, structured plans for circuit designs.",
    model=MODEL_PLAN,
    model_settings=ModelSettings(temperature=MODEL_TEMP)
)

AGENT_PART = Agent(
    name="Part Selection Agent", 
    instructions="You are a specialized agent for component part selection. Extract and clean search terms for electronic components.",
    model=MODEL_PART,
    model_settings=ModelSettings(temperature=MODEL_TEMP)
)

AGENT_CODE = Agent(
    name="Code Generation Agent",
    instructions="You are a specialized agent for generating SKiDL code. Create high-quality, production-ready circuit designs.",
    model=MODEL_CODE,
    model_settings=ModelSettings(temperature=MODEL_TEMP)
)
