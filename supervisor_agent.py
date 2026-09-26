import os
import asyncio
from state import SupervisorState
from research_agent import research_agent
from langgraph.graph import StateGraph, START, END
from typing import Literal
from langgraph.types import Command
from langchain.chat_models import init_chat_model
from prompts.prompts import lead_researcher_prompt

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    filter_messages,
    get_buffer_string
)
from integrations.tools import think_tool, ResearchComplete, ConductResearch, get_today_str, conduct_research, get_notes_from_tool_calls

supervisor_tools = [ConductResearch, ResearchComplete, think_tool]
supervisor_model = init_chat_model(
    model=os.getenv("SUPERVISOR_MODEL"),
    model_provider="google_genai",
    api_key=os.getenv("GEMINI_API")
)

supervisor_model_with_tools = supervisor_model.bind_tools(supervisor_tools)

# Max iterations
max_researcher_iterations = 6 # Calls to think_tool + ConductResearch

# This is passed to the lead_researcher_prompt to limit parallel research tasks
max_concurrent_researchers = 2


async def supervisor(state: SupervisorState) -> Command[Literal["supervisor_tools"]]:
    """Coordinate research activities"""

    supervisor_messages = state.get("supervisor_messages", [])

    # System message
    system_message = lead_researcher_prompt.format(
        date=get_today_str(),
        max_researcher_iterations=max_researcher_iterations,
        max_concurrent_research_units=max_concurrent_researchers
    )

    messages = [SystemMessage(content=system_message)] + supervisor_messages

    # Make decision about the next research step
    response = await supervisor_model_with_tools.ainvoke(messages)

    return Command(
        goto="supervisor_tools",
        update={
            "supervisor_messages": [response],
            "research_iterations": state.get("research_iterations", 0) + 1
        }
    )


async def supervisor_tools(state: SupervisorState) -> Command[Literal["supervisor", "__end__"]]:
    """Execute supervisor decision, either execute a tool or end research"""

    supervisor_messages = state.get("supervisor_messages", [])
    research_iterations = state.get("research_iterations", 0)
    most_recent_message = supervisor_messages[-1]

    # Single return variables
    tool_messages = []
    all_raw_notes = []
    next_step = "supervisor" # Default next step
    should_end = False

    # Check exit criteria first
    exceeded_iterations = research_iterations >= max_researcher_iterations
    no_tool_calls = not most_recent_message.tool_calls
    research_complete = any(
        tool_call["name"] == "ResearchComplete"
        for tool_call in most_recent_message.tool_calls
    )

    if exceeded_iterations or no_tool_calls or research_complete:
        should_end = True
        next_step = END

    else:
        # Execute all the tool calls
        try:
            # Separate thinking tools from ConductResearch tool
            think_tool_calls = [
                tool_call for tool_call in most_recent_message.tool_calls
                if tool_call["name"] == "think_tool"
            ]

            conduct_research_calls = [
                tool_call for tool_call in most_recent_message.tool_calls
                if tool_call["name"] == "ConductResearch"
            ]

            # Handle think_tool calls (synchronous)
            for tool_call in think_tool_calls:
                observation = think_tool.invoke(tool_call["args"])
                tool_messages.append(
                    ToolMessage(
                        content=observation,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    )
                )

            # Handle ConductResearch calls (asynchronous)
            if conduct_research_calls:
                # Execute parallel research agents
                coros = [
                    research_agent.ainvoke({
                        "researcher_messages": [HumanMessage(content=tool_call["args"]["research_topic"])],
                        "research_topic": tool_call["args"]["research_topic"]
                    })
                    for tool_call in conduct_research_calls
                ]

                # Wait for all research to complete
                tool_results = await asyncio.gather(*coros)

                # Format research result as tool messages
                research_tool_messages = [
                    ToolMessage(
                        content=result.get("compressed_research", "Error synthesizing research report"),
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    ) for result, tool_call in zip(tool_results, conduct_research_calls)
                ]

                tool_messages.extend(research_tool_messages)

                # Aggregate all raw_notes
                all_raw_notes = [
                    "\n".join(result.get("raw_notes", []))
                    for result in tool_results
                ]

        except Exception as e:
            print(f"Error: {e}")
            should_end=True
            next_step=END

    if should_end:
        return Command(
            goto=next_step,
            update={
                "notes": get_notes_from_tool_calls(supervisor_messages),
                "research_brief": state.get("research_brief", "")
            }
        )
    else:
        return Command(
            goto=next_step,
            update={
                "supervisor_messages": tool_messages,
                "raw_notes": all_raw_notes
            }
        )


# Graph construction
supervisor_builder = StateGraph(SupervisorState)
supervisor_builder.add_node("supervisor", supervisor)
supervisor_builder.add_node("supervisor_tools", supervisor_tools)
supervisor_builder.add_edge(START, "supervisor")

supervisor_agent = supervisor_builder.compile()




