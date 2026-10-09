import os
import io
import smtplib
import mimetypes
import markdown
from email.message import EmailMessage
from xhtml2pdf import pisa
from email.utils import make_msgid
from dotenv import load_dotenv
from utils.format_pdf import format_pdf

load_dotenv()

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

def send_news_reminder(email_content, subject, recipient, doc_content, cc_recipients=None):
    """Send a reminder email to a recipient with proper envelope routing"""

    plain_text_fallback = (
        "AIC Intelligence Digest\n\n"
        "Please view this email in an HTML-capable email client to read the full update.\n\n"
        "---\nSent by APU AI Club"
    )

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)

            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = f"AIC News System <{GMAIL_USER}>"
            message["To"] = recipient

            # Initialize the routing list with the primary recipient
            all_recipients = [recipient]

            # Add CC addresses to user headers
            if cc_recipients and isinstance(cc_recipients, list):
                message["Cc"] = ", ".join(cc_recipients)
                all_recipients.extend(cc_recipients) # Appends cc items into the flat list

            message["Message-ID"] = make_msgid(domain="gmail.com")

            message.set_content(plain_text_fallback)
            message.add_alternative(email_content, subtype="html")

            # Attach the generated PDF bytes stream
            if doc_content:
                message.add_attachment(
                    doc_content,
                    maintype="application",
                    subtype="pdf",
                    filename="AIC_Weekly_Report.pdf"
                )

            # Add to_addrs for the SMTP server routes to CCs
            server.send_message(message, to_addrs=all_recipients)
            print(f"Sent email to {recipient} (CC: {', '.join(cc_recipients) if cc_recipients else 'None'})")

    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: Check your email and 16-char App Password. Error: {e}")
    except Exception as e:
        print(f"SMTP Error: {e}")
