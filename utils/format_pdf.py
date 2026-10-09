import markdown
import xhtml2pdf
from xhtml2pdf import pisa
import io



def format_pdf(markdown_content):
    """Format markdown content to PDF file"""

    try:
        # Raw markdown
        html_content = markdown.markdown(markdown_content, extensions=["extra", "sane_lists"])

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
                        {html_content}
                    </body>
                    </html>
                    """

        # Generate PDF on the memory
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(styled_html, dest=pdf_buffer)

        if pisa_status.err:
            print("Error generating PDF")
        else:
            return pdf_buffer.getvalue()

    except Exception as e:
        print(f"Error: {e}")