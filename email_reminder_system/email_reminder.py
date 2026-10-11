# import os
# import io
# import smtplib
# import mimetypes
# import markdown
# from email.message import EmailMessage
# from xhtml2pdf import pisa
# from email.utils import make_msgid
# from dotenv import load_dotenv
# from utils.format_pdf import format_pdf
#
# load_dotenv()
#
# GMAIL_USER = os.environ.get("GMAIL_USER")
# GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
#
# def send_news_reminder(email_content, subject, recipient, doc_content, cc_recipients=None):
#     """Send a reminder email to a recipient with proper envelope routing"""
#
#     plain_text_fallback = (
#         "AIC Intelligence Digest\n\n"
#         "Please view this email in an HTML-capable email client to read the full update.\n\n"
#         "---\nSent by APU AI Club"
#     )
#
#     try:
#         with smtplib.SMTP("smtp.gmail.com", 587) as server:
#             server.starttls()
#             server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
#
#             message = EmailMessage()
#             message["Subject"] = subject
#             message["From"] = f"AIC News System <{GMAIL_USER}>"
#             message["To"] = recipient
#
#             # Initialize the routing list with the primary recipient
#             all_recipients = [recipient]
#
#             # Add CC addresses to user headers
#             if cc_recipients and isinstance(cc_recipients, list):
#                 message["Cc"] = ", ".join(cc_recipients)
#                 all_recipients.extend(cc_recipients) # Appends cc items into the flat list
#
#             message["Message-ID"] = make_msgid(domain="gmail.com")
#
#             message.set_content(plain_text_fallback)
#             message.add_alternative(email_content, subtype="html")
#
#             # Attach the generated PDF bytes stream
#             if doc_content:
#                 message.add_attachment(
#                     doc_content,
#                     maintype="application",
#                     subtype="pdf",
#                     filename="AIC_Weekly_Report.pdf"
#                 )
#
#             # Add to_addrs for the SMTP server routes to CCs
#             server.send_message(message, to_addrs=all_recipients)
#             print(f"Sent email to {recipient} (CC: {', '.join(cc_recipients) if cc_recipients else 'None'})")
#
#     except smtplib.SMTPAuthenticationError as e:
#         print(f"Authentication failed: Check your email and 16-char App Password. Error: {e}")
#     except Exception as e:
#         print(f"SMTP Error: {e}")

import io
import mimetypes
import os
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path
from dotenv import load_dotenv
from datetime import date
from utils.format_pdf import format_pdf

load_dotenv()

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# Dynamically resolve the directory where this script lives
CURRENT_DIR = Path(__file__).resolve().parent


def find_asset(filename):
    """Locate the image file across possible directory structures (local or Cloud Run)."""
    candidates = [
        CURRENT_DIR.parent / filename,  # Project root (1 level up)
        CURRENT_DIR / filename,  # Same directory as script
        Path.cwd() / filename,  # Wherever python was executed
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def send_news_reminder(
        email_content,
        subject,
        recipient,
        doc_content,
        cc_recipients=None,
        logo_filename="aic_logo.png",
):
    """Send a reminder email to a recipient with inline AIC branding and PDF attachment."""

    plain_text_fallback = (
        "AIC Intelligence Digest\n\n"
        "Please view this email in an HTML-capable email client to read the full update.\n\n"
        "---\nSent by APU AI Club"
    )

    # Safely resolve the absolute path to the image
    logo_path = find_asset(logo_filename)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)

            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = f"AIC News System <{GMAIL_USER}>"
            message["To"] = recipient

            all_recipients = [recipient]

            if cc_recipients and isinstance(cc_recipients, list):
                message["Cc"] = ", ".join(cc_recipients)
                all_recipients.extend(cc_recipients)

            message["Message-ID"] = make_msgid(domain="gmail.com")

            # Base Plain Text & HTML Alternative
            message.set_content(plain_text_fallback)
            message.add_alternative(email_content, subtype="html")

            # Attach Inline AIC Logo to the HTML part
            if logo_path:
                mime_type, _ = mimetypes.guess_type(logo_path)
                if mime_type:
                    maintype, subtype = mime_type.split("/")
                else:
                    # Explicit fallback for Cloud Run slim containers
                    maintype, subtype = "image", "png"

                with open(logo_path, "rb") as img:
                    img_data = img.read()

                # message.get_payload()[1] targets the HTML alternative part
                message.get_payload()[1].add_related(
                    img_data,
                    maintype=maintype,
                    subtype=subtype,
                    cid="<aic_logo>",  # Matches src="cid:aic_logo" in HTML
                    filename=os.path.basename(logo_path),
                )
                print(f"Attached inline logo from: {logo_path}")
            else:
                print(f"Warning: '{logo_filename}' was not found. Sending email without inline logo.")

            # Attach the generated PDF
            if doc_content:
                message.add_attachment(
                    doc_content,
                    maintype="application",
                    subtype="pdf",
                    filename="AIC_Weekly_Report.pdf",
                )

            # Send through Gmail SMTP
            server.send_message(message, to_addrs=all_recipients)
            print(
                f"Sent email to {recipient} (CC: {', '.join(cc_recipients) if cc_recipients else 'None'})"
            )

    except smtplib.SMTPAuthenticationError as e:
        print(
            f"Authentication failed: Check your email and 16-char App Password. Error: {e}"
        )
    except Exception as e:
        print(f"SMTP Error: {e}")
