import os
import asyncio
from dotenv import load_dotenv
import warnings
from typing import Literal
from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    filter_messages,
    get_buffer_string
)
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.graph import Graph
from langgraph.graph import StateGraph, START, END
from integrations.tools import think_tool, tavily_search, ResearchComplete, ConductResearch, get_today_str
from .state import ResearcherState, ResearcherOutputState, AgentState
from prompts.prompts import final_report_generation_prompt

# Load environment
load_dotenv()

writer_model = init_chat_model(
    model=os.getenv("WRITER_MODEL"),
    model_provider="google_genai",
    api_key=os.getenv("GEMINI_API")
)


async def final_report_generation(state: AgentState):
    """Final report generation node"""

    notes = state.get("notes", [])
    findings = "\n".join(notes)

    final_report_prompt = final_report_generation_prompt.format(
        research_brief=state.get("research_brief", ""),
        findings=findings,
        date=get_today_str()
    )

    final_report = await writer_model.ainvoke([HumanMessage(content=final_report_prompt)])

    # Type checking to avoid casting errors
    content = final_report.content

    if isinstance(content, list):
        content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    else:
        content = str(content)

    return {
        "final_report": content,
        "messages": ["Here is the final report: " + content]
    }