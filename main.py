from graph import agent
import asyncio
from langchain_core.messages import HumanMessage


async def main(search_message):
    try:
        # Run the agent
        news = await agent.ainvoke({"messages": [search_message]})

        # Extract the final report
        final_report = news.get("final_report")

        print("\n\n=== FINAL REPORT ===")
        print(final_report)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    search_requirement = """
                Identify the three most compelling, high-signal AI developments from the past 7 days across three distinct pillars:
                Frontier & Open Foundation Models: The most significant model release, architectural shift, or capability milestone from major labs (OpenAI, DeepMind, Anthropic, Meta) or notable open-source drops.
                Foundational Research & Architectural Debates: The most critical research paper or theoretical insight published this week regarding model limitations, reasoning behavior, test-time compute, or efficiency bottlenecks.
                High-Stakes & Unconventional Deployments: The most notable real-world implementation of AI in physical systems, extreme infrastructure, high-consequence industries, or headless background decision engines.
            """

    message = HumanMessage(content=search_requirement)
    asyncio.run(main(message))