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
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")  # APP password

def send_news_reminder(email_content, subject, recipient, doc_content, cc_recipients=None):
    """Send a reminder email to a recipient"""

    # Plain-text version for email clients that do not render HTML
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

            # CC recipients if included
            if cc_recipients and isinstance(cc_recipients, list):
                message["Cc"] = ", ".join(cc_recipients)

            # RFC-compliant unique Message-ID header
            message["Message-ID"] = make_msgid(domain="gmail.com")

            # Fallback plain text + HTML
            message.set_content(plain_text_fallback)
            message.add_alternative(email_content, subtype="html")

            try:
                # Attach the generated PDF
                message.add_attachment(
                    doc_content,
                    maintype="application",
                    subtype="pdf",
                    filename="AIC_Weekly_Report.pdf"
                )

            except FileNotFoundError:
                print(f"Warning: {file_name} not found. Sending without attachment.")

            # Send the message
            server.send_message(message)
            print(f"Sent email to {recipient}")

    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: Check your email and 16-char App Password. Error: {e}")
    except Exception as e:
        print(f"SMTP Error: {e}")




