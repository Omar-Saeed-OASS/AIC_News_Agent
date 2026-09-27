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
from state import ResearcherState, ResearcherOutputState
from prompts.prompts import research_system_prompt, compress_research_system_prompt, compress_research_simple_human_message

# Load environment
load_dotenv()

model = init_chat_model(
    model=os.getenv("RESEARCHER_MODEL"),
    model_provider="google_genai",
    api_key=os.getenv("GEMINI_API")
)

tools = [think_tool, tavily_search]
tools_by_name = {tool.name: tool for tool in tools}

model_with_tools = model.bind_tools(tools)



compress_model = init_chat_model(
    model=os.getenv("COMPRESS_RESEARCH_MODEL"),
    model_provider="google_genai",
    api_key=os.getenv("GEMINI_API")
)

async def llm_call(state: ResearcherState):
    """
    Analyze the current state and decide the next actions
    1-Call research tools to gather more information
    2-Provide final answer based on the gathered data
    """

    return {
        "researcher_messages": [
            await model_with_tools.ainvoke(
                [SystemMessage(research_system_prompt.format(date=get_today_str()))] + state["researcher_messages"]
            )
        ]
    }

async def tool_node(state: ResearcherState):
    """Execute tools from the previous LLM response"""
    tool_calls = state["researcher_messages"][-1].tool_calls

    # Execute all the tools
    observations = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observations.append(await tool.ainvoke(tool_call["args"]))

    # Tool Messages Output
    tool_outputs = [
        ToolMessage(
            content=observations,
            name=tool_call["name"],
            tool_call_id=tool_call["id"]
        ) for observation, tool_call in zip(observations, tool_calls)
    ]

    return {"researcher_messages": tool_outputs}


async def compress_research(state: ResearcherState):
    """Compress research finding into concise summary"""

    system_message = compress_research_system_prompt.format(date=get_today_str())
    messages = [SystemMessage(system_message)] + state.get("researcher_messages", []) + [HumanMessage(compress_research_simple_human_message)]
    response = await compress_model.ainvoke(messages)

    # Extract raw notes from the tools and AI
    raw_notes = [
        str(m.content) for m in filter_messages(
            state["researcher_messages"],
            include_types=["tool", "ai"]
        )
    ]


    return {
        "compressed_research": str(response.content),
        "raw_notes": ["\n".join(raw_notes)]
    }

# Routing logic
def should_continue(state: ResearcherState) -> Literal["tool_node", "compress_research"]:
    """Determine whether to continue executing tools or proceed to compression"""

    messages = state["researcher_messages"]
    last_message = messages[-1]

    # Check the final message
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_node"

    # If final answer
    return "compress_research"


# Compile the graph
agent_builder = StateGraph(ResearcherState, output_schema=ResearcherOutputState)

# Nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("compress_research", compress_research)

# Edges
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node",
        "compress_research": "compress_research"
    }
)

agent_builder.add_edge("tool_node", "llm_call")
agent_builder.add_edge("compress_research", END)

# Compile research agent
research_agent = agent_builder.compile()

