import asyncio
from langchain_core.messages import HumanMessage
from agents.graph import agent
from email_reminder_system.email_reminder import send_news_reminder
from utils.format_pdf import format_pdf
from db.db_manager import DatabaseManager
from datetime import datetime


db_manager = DatabaseManager()

async def main(search_message):
    try:
        # Run the search agent
        news = await agent.ainvoke({"messages": [search_message]})

        # Extract the final report
        raw_final_report = news.get("final_report")

        # Format the report markdown to pdf
        final_report = format_pdf(raw_final_report)

        # Send the email
        sample_html = "<h2>AIC Digest</h2><p>Here is your scheduled news update.</p>"
        newsletter_subject = "AIC Weekly Intelligence Digest | Issue #1"

        # Email recipients
        recipient = "omarabdulrahmansaeed@gmail.com"
        cc_recipients = ["omar.csai21@gmail.com"]

        # Save to the database
        data = {
            "final_report": raw_final_report,
            "PIC": recipient,
            "Cc": cc_recipients,
            "date": datetime.now()
        }

        db_manager.set_document(collection="reports", data=data)

        # Send the email
        send_news_reminder(
            email_content=sample_html,
            subject=newsletter_subject,
            recipient=recipient,
            doc_content=final_report,
            cc_recipients=cc_recipients
        )

        print("\n\n=== FINAL REPORT ===")
        print(raw_final_report)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    search_requirement = """
                Identify the three most compelling, high-signal AI developments from the past 7 days across three distinct pillars:
                1-Frontier & Open Foundation Models: The most significant model release, architectural shift, or capability milestone from major labs (OpenAI, DeepMind, Anthropic, Meta) or notable open-source drops.
                2-Foundational Research & Architectural Debates: The most critical research paper or theoretical insight published this week regarding model limitations, reasoning behavior, test-time compute, or efficiency bottlenecks.
                3-High-Stakes & Unconventional Deployments: The most notable real-world implementation of AI in physical systems, extreme infrastructure, high-consequence industries, or headless background decision engines.
                4-The Weird, Wild & World-Changing: Find surprising AI breakthroughs, unexpected capabilities, bizarre failures, and science-fiction-like developments that challenge conventional assumptions or could reshape our future. Prioritize verified, genuinely fascinating discoveries over hype and viral gimmicks.
            """

    message = HumanMessage(content=search_requirement)
    asyncio.run(main(message))