import os
from .state import AgentState, AgentInputState
from .research_agent import research_agent
from .supervisor_agent import supervisor_agent
from .report_briefing import write_research_brief
from langgraph.graph import StateGraph, START, END
from typing import Literal
from langgraph.types import Command
from langchain.chat_models import init_chat_model
from prompts.prompts import lead_researcher_prompt
from google.cloud import firestore
from langgraph_checkpoint_firestore import FirestoreSaver
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    filter_messages,
    get_buffer_string
)
from integrations.tools import think_tool, ResearchComplete, ConductResearch, get_today_str, conduct_research, get_notes_from_tool_calls
from .writer_llm import final_report_generation

# Workflow builder
deep_research_builder = StateGraph(AgentState, input_schema=AgentInputState)

# Nodes
deep_research_builder.add_node("write_research_brief", write_research_brief)
deep_research_builder.add_node("supervisor_subgraph", supervisor_agent)
deep_research_builder.add_node("final_report_generation", final_report_generation)

# Edges
deep_research_builder.add_edge(START, "write_research_brief")
deep_research_builder.add_edge("write_research_brief", "supervisor_subgraph")

deep_research_builder.add_edge("supervisor_subgraph", "final_report_generation")
deep_research_builder.add_edge("final_report_generation", END)


# ==== Testing === locally
# This looks up one folder from agents/ and into email_reminder_system/
current_dir = os.path.dirname(__file__)
firebase_json_path = os.path.abspath(
    os.path.join(current_dir, "..", "db", "aic-news-storage-key.json")
)

# Tell the underlying Google library to use your Firebase file for authentication
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = firebase_json_path


# Checkpointer
project_id_str = str(os.environ.get("CHECKPOINTER_PROJECT_ID"))
checkpointer = FirestoreSaver(project_id_str)

# Compile the full workflow with checkpointer
agent = deep_research_builder.compile(checkpointer=checkpointer)