import os
import io
import re
import base64
from datetime import date
import markdown
import xhtml2pdf
from xhtml2pdf import pisa


def get_logo_html() -> str:
    """Finds aic_logo.png and returns an inline base64 <img> tag in a dedicated table cell."""
    candidate_paths = [
        os.path.join(os.path.dirname(__file__), "..", "aic_logo.png"),
        os.path.join(os.getcwd(), "aic_logo.png"),
        os.path.join(os.path.dirname(__file__), "..", "assets", "aic_logo.png"),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                return f'<img src="data:image/png;base64,{encoded}" width="38" height="38" />'
            except Exception:
                pass
    return ""


def preprocess_markdown(md_text: str) -> str:
    """Cleans up markdown artifacts and formats the Sources section into a clean bulleted list."""

    md_text = re.sub(r'^[-*_]{3,}\s*$', '', md_text, flags=re.MULTILINE)

    # Isolate the Sources section from the rest of the text
    parts = re.split(r'(?i)(?:\n|^)(?:#+\s*)?(?:Sources|References)\s*(?:\n|$)', md_text)

    if len(parts) == 2:
        main_body, sources = parts[0], parts[1]

        # Force a double-newline and a bullet point before every [1], [2], etc.
        sources = re.sub(r'\[(\d+)\]', r'\n\n* **[\1]** ', sources)

        return main_body.strip() + "\n\n### Sources\n" + sources.strip()

    return md_text


def format_pdf(markdown_content: str):
    """Format markdown intelligence briefings into a clean, executive AIC PDF."""
    try:
        cleaned_markdown = preprocess_markdown(markdown_content)

        html_content = markdown.markdown(
            cleaned_markdown,
            extensions=["extra", "sane_lists", "tables"]
        )

        current_year = date.today().year
        report_date = date.today().strftime("%B %d, %Y")
        logo_html = get_logo_html()

        styled_html = f"""
        <html>
        <head>
            <style>
                @page {{
                    size: A4;
                    /* INCREASED MARGINS: Forces body text to clear the header/footer */
                    margin-top: 3.2cm;
                    margin-bottom: 2.5cm;
                    margin-left: 2cm;
                    margin-right: 2cm;

                    /* Header frame stops at 2.8cm (leaves 4mm gap before body text starts) */
                    @frame header_frame {{
                        -pdf-frame-content: header_content;
                        left: 2cm; right: 2cm; top: 1cm; height: 1.8cm;
                    }}

                    /* Footer frame stays safely inside the bottom margin */
                    @frame footer_frame {{
                        -pdf-frame-content: footer_content;
                        left: 2cm; right: 2cm; bottom: 0.8cm; height: 1.2cm;
                    }}
                }}

                body {{
                    font-family: Helvetica, Arial, sans-serif;
                    font-size: 10pt;
                    line-height: 1.6;
                    color: #1e1b4b;
                }}

                h1 {{
                    color: #4c1d95;
                    font-size: 16.5pt;
                    font-weight: bold;
                    margin-top: 0;
                    margin-bottom: 12px;
                    padding-bottom: 4px;
                    border-bottom: 1.5px solid #e9d5ff;
                }}

                h2 {{
                    color: #1e0836;
                    font-size: 12.5pt;
                    margin-top: 18px;
                    margin-bottom: 8px;
                    border-left: 4px solid #7c3aed;
                    padding-left: 8px;
                }}

                h3 {{ color: #6b21a8; font-size: 11pt; margin-top: 12px; margin-bottom: 6px; }}
                p {{ margin-top: 0; margin-bottom: 10px; }}

                /* Fallback for horizontal rules */
                hr {{ border: 0; border-top: 1px solid #e9d5ff; margin: 15px 0; }}

                ul, ol {{ margin-top: 6px; margin-bottom: 12px; padding-left: 20px; }}
                li {{ margin-bottom: 8px; line-height: 1.5; word-wrap: break-word; }}

                a {{ color: #6d28d9; text-decoration: underline; }}

                .header-table {{
                    width: 100%;
                    border-bottom: 2.5px solid #4c1d95; 
                    padding-bottom: 6px;
                }}
                .footer-table {{
                    width: 100%;
                    border-top: 1px solid #e9d5ff; 
                    padding-top: 6px;
                }}

                .header-brand {{ font-size: 13.5pt; font-weight: bold; color: #1e0836; }}
                .header-subline {{ font-size: 7.5pt; font-weight: bold; color: #7c3aed; letter-spacing: 1px; }}
                .footer-text, .footer-page {{ font-size: 8pt; color: #94a3b8; }}
                .footer-page {{ text-align: right; }}
            </style>
        </head>
        <body>
            <div id="header_content">
                <table class="header-table">
                    <tr>
                        <td style="width: 8%; vertical-align: middle;">
                            {logo_html}
                        </td>
                        <td style="width: 62%; vertical-align: middle;">
                            <span class="header-brand">Weekly Intelligence Digest</span><br/>
                            <span class="header-subline">APU AI CLUB &bull; INTERNAL R&amp;D</span>
                        </td>
                        <td style="width: 30%; vertical-align: bottom; text-align: right; font-size: 8.5pt; color: #64748b;">
                            <strong>{report_date}</strong>
                        </td>
                    </tr>
                </table>
            </div>

            <div id="footer_content">
                <table class="footer-table">
                    <tr>
                        <td class="footer-text">&copy; {current_year} APU AI Club (AIC) &bull; Powered By AI Potential</td>
                        <td class="footer-page">Page <pdf:pagenumber> of <pdf:pagecount></td>
                    </tr>
                </table>
            </div>

            <div class="content">
                {html_content}
            </div>
        </body>
        </html>
        """

        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(styled_html, dest=pdf_buffer)

        if pisa_status.err:
            print("Error generating PDF")
            return None

        return pdf_buffer.getvalue()

    except Exception as e:
        print(f"Error: {e}")
        return None