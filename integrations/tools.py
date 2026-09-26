import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, BaseMessage, filter_messages
from tavily import AsyncTavilyClient
from langchain_core.tools import tool
from prompts.prompts import summarize_webpage_prompt
from schema.schemas import Summary
import warnings



# Suppress the Google SDK's automatic function calling warning
warnings.filterwarnings("ignore", category=UserWarning, module="google_genai")


TAVILY_SEARCH_DESCRIPTION = (
    "A search engine optimized for comprehensive, accurate, and trusted results. "
    "Useful for when you need to answer questions about current events."
)
@tool(description=TAVILY_SEARCH_DESCRIPTION)
async def tavily_search(
    queries: List[str],
    max_results: int=2,
    topic: Literal["general", "news", "finance"] = "news",
    time_range: Literal["day", "week", "month", "year"] = "week",
    # config: RunnableConfig = None
) -> str:
    """Fetch and summarize search results from Tavily search API."""

    search_results = await tavily_search_async(
        queries,
        max_results=max_results,
        topic=topic,
        time_range=time_range,
        include_raw_content=False
        # config=config
    )

    # Deduplicate the URLs to avoid processing same content
    unique_results = {}
    for response in search_results:
        for result in response["results"]:
            url = result["url"]
            if url not in unique_results:
                unique_results[url] = {**result, "query": response["query"]}

    # Summarize and return the search result
    summarized_content = await summarization_task(unique_results)
    return summarized_content


async def tavily_search_async(
    search_queries,
    max_results: int = 2,
    topic: Literal["general", "news", "finance"] = "news",
    time_range: Literal["day", "week", "month", "year"] = "week",
    include_raw_content: bool = False
):
    """Execute multiple Tavily search queries asynchronously."""

    # Initiate tavily client
    tavily_client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API"))

    # Create search task using parallel execution
    search_tasks = [
        tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            time_range=time_range,
            topic=topic
        )
        for query in search_queries
    ]

    # Execute the search queries and return the results in parallel
    search_results = await asyncio.gather(*search_tasks)
    return search_results


async def summarization_task(
    unique_results
    # config: RunnableConfig = None
):
    """Summarize the unique content returned by the tavily search method"""

    # Set up the configuration
    # configurable = TO DO
    model_api_key = os.getenv("GEMINI_API")
    model = os.getenv("GEMINI_MODEL")
    summarization_model = init_chat_model(
        model=model,
        model_provider="google_genai",
        api_key=model_api_key,
    ).with_structured_output(Summary).with_retry(stop_after_attempt=2)

    # Create summarization tasks
    summarization_tasks = []

    for result in unique_results.values():
        if not result.get("content"):
            continue
        else:
            summarization_tasks.append(
                summarize_webpage(summarization_model, result.get("content"))
            )

    summaries = await asyncio.gather(*summarization_tasks)

    # Combine the results with their summary
    summarized_results = {
        url: {
            "title": result["title"],
            "content": result["content"] if summary is None else summary
        }
        for url, result, summary in zip(
            unique_results.keys(),
            unique_results.values(),
            summaries
        )
    }

    # Formate the final output
    if not summarized_results:
        return "No valid search results found. Please try different search queries or use a different search API."

    formatted_output = "Search results: \n\n"
    for i, (url, result) in enumerate(summarized_results.items()):
        formatted_output += f"\n\n--- SOURCE {i + 1}: {result['title']} ---\n"
        formatted_output += f"URL: {url}\n\n"
        formatted_output += f"SUMMARY:\n{result['content']}\n\n"
        formatted_output += "\n\n" + "-" * 80 + "\n"

    return formatted_output


async def summarize_webpage(model, webpage_content):
    """Summarize webpage content using AI model with timeout protection"""
    try:
        # Create the prompt
        prompt_content = summarize_webpage_prompt.format(
            webpage_content=webpage_content,
            date=get_today_str()
        )

        # Execute the summarization with timeout to prevent hanging
        summary = await asyncio.wait_for(
            model.ainvoke([HumanMessage(content=prompt_content)]),
            timeout=120.0 # 120.0 second timeout
        )

        # Format the summary with structured sections
        formatted_summary = (
            f"<summary>\n{summary.summary}\n</summary>\n\n"
            f"<key_excerpts>\n{summary.key_excerpts}\n</key_excerpts>"
        )

        return formatted_summary

    except asyncio.TimeoutError:
        # Timeout during summarization - return original content
        logging.warning("Summarization timed out after 60 seconds, returning original content")
        return webpage_content

    except Exception as e:
        # Other errors during summarization - log and return original content
        logging.warning(f"Summarization failed with error: {str(e)}, returning original content")
        return webpage_content

# === Reflection tool ===

@tool(description="Strategic reflection tool for research planning")
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"


def get_today_str() -> str:
    """Get current date formatted for display in prompts and outputs.

    Returns:
        Human-readable date string in format like 'Mon Jan 15, 2024'
    """
    now = datetime.now()
    return f"{now:%a} {now:%b} {now.day}, {now:%Y}"

# ===== Orchestration signaling tools =====
@tool
def conduct_research(research_topic: str) -> str:
    """Call this tool to delegate and conduct research on a specific sub-topic.

    Use this tool when a complex research goal needs to be broken down into individual,
    deep-dive subjects, or when a new topic area requires independent investigation.
    This creates an isolated tracking space for this specific objective.

    Args:
        research_topic: The topic to research. Should be a single topic, and should
                        be described in high detail (at least a paragraph) specifying
                        goals, targets, and context.
    """
    return f"Signal: Sub-graph research task triggered for topic: {research_topic}"

def get_notes_from_tool_calls(messages: list[BaseMessage]) -> list[str]:
    """Extract research notes from ToolMessage objects in supervisor message history.
    Args:
        messages: List of messages from supervisor's conversation history

    Returns:
        List of research note strings extracted from ToolMessage objects
    """
    return [tool_msg.content for tool_msg in filter_messages(messages, include_types="tool")]


@tool
class ConductResearch(BaseModel):
    """Tool to delegate a specific sub-topic to a specialized sub-agent"""

    research_topic: str = Field(
        description="The topic to research. Should be a single topic, and should be described in high detail (at least a paragraph)"
    )

@tool
class ResearchComplete(BaseModel):
    """Call this tool to indicate that all research goals have been fully met."""
    pass