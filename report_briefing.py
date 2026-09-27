import os
import asyncio
from dotenv import load_dotenv
from schema.schemas import ResearchQuestion
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
from state import ResearcherState, ResearcherOutputState, AgentState
from prompts.prompts import transform_messages_into_research_topic_prompt

# Load environment
load_dotenv()

briefing_model = init_chat_model(
    model=os.getenv("WRITER_MODEL"),
    model_provider="google_genai",
    api_key=os.getenv("GEMINI_API")
)


def write_research_brief(state: AgentState):
    """Transform the conversation into a comprehensive research brief"""

    # Structured model output
    structured_model_output = briefing_model.with_structured_output(ResearchQuestion)

    # Generate the research brief
    response = structured_model_output.invoke(
        [
            HumanMessage(content=transform_messages_into_research_topic_prompt.format(
                messages=get_buffer_string(state.get("messages", [])),
                date=get_today_str()
            ))
        ]
    )

    # Update the state with the research brief and send it to the supervisor
    return {
        "research_brief": response.research_brief,
        "supervisor_messages": [HumanMessage(content=f"{response.research_brief}.")]
    }