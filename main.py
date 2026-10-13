import os
import asyncio
import uuid
from langchain_core.messages import HumanMessage
from agents.graph import agent
from email_reminder_system.email_reminder import send_news_reminder
from email_reminder_system.email_grabber import get_email_from_sheet
from utils.format_pdf import format_pdf
from templates.news_html_template import news_content_html
from templates.error_html_template import error_html_content
from db.db_manager import DatabaseManager
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
EMAILS_SHEET = os.environ.get("EMAILS_SHEET")
DEBUG_EMAIL = os.environ.get("DEBUG_EMAIL")

db_manager = DatabaseManager()


async def main(search_message):
    try:

        # Dynamic Date
        today = date.today()
        issue_date = f"Week of {today.strftime('%B %d, %Y')}"

        # Run the search agent
        run_thread_id = f"weekly_run_{today.strftime('%Y_%m_%d')}"
        run_config = {"configurable": {"thread_id": run_thread_id}}

        news = await agent.ainvoke({"messages": [search_message]}, config=run_config)

        # Extract the final report
        raw_final_report = news.get("final_report")

        # Format the report markdown to pdf
        final_report = format_pdf(raw_final_report)

        # Subject Line with AIC branding
        newsletter_subject = f"⚡ AIC Weekly Intelligence Digest | {issue_date}"

        # News content
        news_content = news_content_html.format(issue_date=issue_date, current_year=datetime.now().year)

        # Email recipients
        recipient, cc_recipients = get_email_from_sheet(spreadsheet_id=SPREADSHEET_ID, email_sheet_id=EMAILS_SHEET)

        # Convert the dict to single email list
        cc_emails = [cc_recipient.get("email") for cc_recipient in cc_recipients]

        # Save to the database
        auto_id = uuid.uuid4().hex[:10]
        data = {
            "report_id": auto_id,
            "final_report": raw_final_report,
            "PIC": recipient,
            "Cc": cc_recipients,
            "date": datetime.now()
        }

        db_manager.set_document(collection="reports", data=data)

        # Send the email
        send_news_reminder(
            email_content=news_content,
            subject=newsletter_subject,
            recipient=recipient.get("email"),
            doc_content=final_report,
            cc_recipients=cc_emails
        )

        print("\n\n=== FINAL REPORT ===")
        print(raw_final_report)

    except Exception as e:

        # Error notification contents
        error_details = str(e)
        error_subject = f"System Failure: AIC Weekly Intelligence Digest | {date.today()}"
        error_content = error_html_content.format(error_details=error_details, current_year=datetime.now().year)

        # Save the error to the database
        auto_id = uuid.uuid4().hex[:15]
        data = {
            "error_id": auto_id,
            "error": error_details,
            "date": datetime.now()
        }

        db_manager.set_document(collection="errors", data=data)

        # Send to the debug email recipient
        send_news_reminder(
            email_content=error_content,
            subject=error_subject,
            recipient=DEBUG_EMAIL,
            include_logo=False
        )
        print(f"An error occurred: {error_details}")


if __name__ == "__main__":
    search_requirement = """
                Identify the five most compelling, high-signal AI developments from the past 7 days across three distinct pillars:
                1-Frontier & Open Foundation Models: The most significant model release, architectural shift, or capability milestone from major labs (OpenAI, DeepMind, Anthropic, Meta) or notable open-source drops.
                2-Foundational Research & Architectural Debates: The most critical research paper or theoretical insight published this week regarding model limitations, reasoning behavior, test-time compute, or efficiency bottlenecks.
                3-High-Stakes & Unconventional Deployments: The most notable real-world implementation of AI in physical systems, extreme infrastructure, high-consequence industries, or headless background decision engines.
                4-The Weird, Wild & World-Changing: Find surprising AI breakthroughs, unexpected capabilities, bizarre failures, and science-fiction-like developments that challenge conventional assumptions or could reshape our future. Prioritize verified, genuinely fascinating discoveries over hype and viral gimmicks.
                5-Agentic Frameworks & Developer Tooling: The most impactful new libraries, orchestration frameworks, or open-source infrastructure enabling multi-agent systems, advanced RAG, or autonomous workflows.
            """

    message = HumanMessage(content=search_requirement)
    asyncio.run(main(message))