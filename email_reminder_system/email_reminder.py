import os
import smtplib
from email.message import EmailMessage
import markdown
import io
from xhtml2pdf import pisa
from dotenv import load_dotenv
from email.utils import make_msgid
import mimetypes

load_dotenv()

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")  # APP password

def send_news_reminder(email_content, subject, recipient):
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

            # RFC-compliant unique Message-ID header
            message["Message-ID"] = make_msgid(domain="gmail.com")

            # Fallback plain text + HTML
            message.set_content(plain_text_fallback)
            message.add_alternative(email_content, subtype="html")

            # attachment
            file_name = "test.md"

            try:
                # Read the raw markdown
                with open(file_name, "r", encoding="utf-8") as file:
                    raw_md = file.read()

                # Convert markdown to basic HTML
                html_content = markdown.markdown(raw_md, extensions=["extra", "sane_lists"])

                # Apply Print/PDF-specific CSS styling
                styled_html = f"""
                            <html>
                            <head>
                                <style>
                                    /* Formats the document into standard A4 pages with margins */
                                    @page {{ size: A4; margin: 2.5cm; }}
                                    body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #333; }}
                                    h1 {{ color: #1a73e8; font-size: 20pt; border-bottom: 2px solid #1a73e8; padding-bottom: 5px; }}
                                    h2 {{ color: #202124; font-size: 16pt; margin-top: 20px; }}
                                    h3 {{ color: #444; font-size: 13pt; }}
                                    p {{ margin-bottom: 12px; }}
                                    li {{ margin-bottom: 6px; }}
                                    code {{ background-color: #f4f4f4; padding: 2px 4px; font-family: "Courier New", Courier, monospace; font-size: 10pt; }}
                                    blockquote {{ border-left: 3px solid #ccc; margin-left: 0; padding-left: 10px; color: #666; }}
                                </style>
                            </head>
                            <body>
                                <h1>AIC Weekly Intelligence Report</h1>
                                {html_content}
                            </body>
                            </html>
                            """

                # Generate the PDF entirely in memory (Cloud Run friendly)
                pdf_buffer = io.BytesIO()
                pisa_status = pisa.CreatePDF(styled_html, dest=pdf_buffer)

                if pisa_status.err:
                    print("Error generating PDF")
                else:
                    # Attach the generated PDF
                    message.add_attachment(
                        pdf_buffer.getvalue(),
                        maintype="application",
                        subtype="pdf",
                        filename="AIC_Weekly_Report.pdf"
                    )

            except FileNotFoundError:
                print(f"Warning: {file_name} not found. Sending without attachment.")

            server.send_message(message)
            print(f"Sent email to {recipient}")

    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: Check your email and 16-char App Password. Error: {e}")
    except Exception as e:
        print(f"SMTP Error: {e}")


