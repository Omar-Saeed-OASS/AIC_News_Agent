import os
import asyncio
from langchain_core.messages import HumanMessage
from agents.graph import agent
from email_reminder_system.email_reminder import send_news_reminder
from email_reminder_system.email_grabber import get_email_from_sheet
from utils.format_pdf import format_pdf
from db.db_manager import DatabaseManager
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
EMAILS_SHEET = os.environ.get("EMAILS_SHEET")

db_manager = DatabaseManager()


async def main(search_message):
    try:
        # Run the search agent
        news = await agent.ainvoke({"messages": [search_message]})

        # Extract the final report
        raw_final_report = news.get("final_report")

        # Format the report markdown to pdf
        final_report = format_pdf(raw_final_report)

        # Dynamic Date
        today = date.today()
        issue_date = f"Week of {today.strftime('%B %d, %Y')}"

        # Subject Line with AIC branding
        newsletter_subject = f"⚡ AIC Weekly Intelligence Digest | {issue_date}"

        # AIC-Themed HTML Template
        sample_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f7f5ff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e1b4b; line-height: 1.6;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f7f5ff; padding: 32px 16px;">
            <tr>
              <td align="center">
                <!-- Main Container Card -->
                <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(88, 28, 135, 0.1), 0 8px 10px -6px rgba(88, 28, 135, 0.05); border: 1px solid #e9d5ff;">

                  <!-- AIC Signature Gradient Banner -->
                  <tr>
                    <td style="background: linear-gradient(135deg, #1e0836 0%, #4c1d95 55%, #7c3aed 100%); padding: 36px 30px; text-align: left;">
                      <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                        <tr>
                          <td>
                            <!-- Category Badge -->
                            <div style="display: inline-block; background-color: rgba(255, 255, 255, 0.12); border: 1px solid rgba(216, 180, 254, 0.4); border-radius: 20px; padding: 4px 12px; margin-bottom: 12px;">
                              <span style="font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #e9d5ff;">
                                ⚡ APU AI Club • Internal R&D
                              </span>
                            </div>
                            <!-- Main Header Title -->
                            <h1 style="margin: 0 0 6px 0; color: #ffffff; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; line-height: 1.25;">
                              Weekly Intelligence Digest
                            </h1>
                            <p style="margin: 0; color: #ddd6fe; font-size: 13px; font-weight: 500;">
                              {issue_date}
                            </p>
                          </td>
                          <!-- Logo / Mascot Column -->
                          <td align="right" valign="middle" style="width: 75px;">
                            <img src="cid:aic_logo" alt="AIC Logo" style="width: 70px; height: 70px; object-fit: contain; border-radius: 12px; display: block; border: 2px solid rgba(255,255,255,0.2);" onerror="this.style.display='none';">
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>

                  <!-- Body Content Area -->
                  <tr>
                    <td style="padding: 30px 30px 20px 30px;">
                      <p style="margin: 0 0 16px 0; font-size: 15px; color: #334155; font-weight: 500;">
                        Hey Team,
                      </p>
                      <p style="margin: 0 0 22px 0; font-size: 14px; color: #475569; line-height: 1.65;">
                        Here is our internal intelligence sweep for the week. We've filtered the past seven days of noise to isolate the highest-signal AI developments critical to our ongoing architectures, evaluations, and research.
                      </p>

                      <!-- Curated Highlights Box (Purple Accent) -->
                      <div style="background-color: #faf5ff; border-left: 4px solid #7c3aed; padding: 16px 20px; border-radius: 0 10px 10px 0; margin-bottom: 24px; border-top: 1px solid #f3e8ff; border-right: 1px solid #f3e8ff; border-bottom: 1px solid #f3e8ff;">
                        <p style="margin: 0 0 10px 0; font-size: 12px; font-weight: 700; color: #6b21a8; text-transform: uppercase; letter-spacing: 0.8px;">
                          Inside This Week's Sweep:
                        </p>
                        <ul style="margin: 0; padding-left: 18px; font-size: 14px; color: #4b5563; line-height: 1.7;">
                          <li style="margin-bottom: 6px;"><strong>Frontier & Open Models:</strong> Major SOTA releases, open-source drops, and architectural milestones.</li>
                          <li style="margin-bottom: 6px;"><strong>Foundational Research:</strong> Critical papers tackling reasoning behavior, test-time compute, and efficiency bottlenecks.</li>
                          <li style="margin-bottom: 6px;"><strong>High-Stakes Deployments:</strong> Unconventional implementations in physical systems and headless decision engines.</li>
                          <li style="margin-bottom: 0;"><strong>The Weird & World-Changing:</strong> Surprising breakthroughs, bizarre failures, and edge-case capabilities.</li>
                        </ul>
                      </div>

                      <!-- PDF Attachment Card -->
                      <div style="background: linear-gradient(180deg, #fdf4ff 0%, #faf5ff 100%); border: 1.5px dashed #c084fc; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px;">
                        <p style="margin: 0 0 6px 0; font-size: 15px; font-weight: 700; color: #6b21a8;">
                            Full Intelligence Report Attached
                        </p>
                        <p style="margin: 0; font-size: 13px; color: #6b7280; line-height: 1.5;">
                          Download <strong>AIC_Weekly_Report.pdf</strong> for complete deep dives, benchmarks, and citations.
                        </p>
                      </div>

                      <p style="margin: 0; font-size: 13px; color: #64748b; line-height: 1.6;">
                        Spot a model to prototype for an internal project, a vulnerability we should red-team, or a breakthrough we should turn into our next hands-on workshop? Drop your thoughts in the internal R&D channels.
                      </p>
                    </td>
                  </tr>

                  <!-- Signoff Section -->
                  <tr>
                    <td style="padding: 0 30px 28px 30px;">
                      <p style="margin: 0 0 4px 0; font-size: 14px; font-weight: 700; color: #1e1b4b;">
                        Best regards,
                      </p>
                      <p style="margin: 0; font-size: 13px; color: #6b21a8; font-weight: 600;">
                        AIC Research & Development Team
                      </p>
                      <p style="margin: 2px 0 0 0; font-size: 12px; color: #94a3b8;">
                        Asia Pacific University of Technology and Innovation
                      </p>
                    </td>
                  </tr>

                  <!-- Footer -->
                  <tr>
                    <td style="background-color: #f8fafc; padding: 14px 30px; text-align: center; border-top: 1px solid #f1f5f9;">
                      <p style="margin: 0; font-size: 11px; color: #94a3b8; letter-spacing: 0.3px;">
                        © 2026 APU AI Club (AIC) • Powered By AI Potential 
                      </p>
                    </td>
                  </tr>

                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """

        # Email recipients
        recipient, cc_recipients = get_email_from_sheet(spreadsheet_id=SPREADSHEET_ID, email_sheet_id=EMAILS_SHEET)

        # Convert the dict to single email list
        cc_emails = [cc_recipient.get("email") for cc_recipient in cc_recipients]

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
            recipient=recipient.get("email"),
            doc_content=final_report,
            cc_recipients=cc_emails
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