from research_agent import research_agent
from supervisor_agent import supervisor_agent
from report_briefing import write_research_brief
from langgraph.graph import StateGraph, START, END
from typing import Literal
from langgraph.types import Command
from langchain.chat_models import init_chat_model
from prompts.prompts import lead_researcher_prompt
from state import AgentState, AgentInputState

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    filter_messages,
    get_buffer_string
)
from integrations.tools import think_tool, ResearchComplete, ConductResearch, get_today_str, conduct_research, get_notes_from_tool_calls
from writer_llm import final_report_generation

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

# Compile the full workflow
agent = deep_research_builder.compile()