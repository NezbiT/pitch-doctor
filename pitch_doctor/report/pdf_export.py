"""Generate PDF from HTML report using WeasyPrint.

Converts the HTML report to a downloadable PDF with proper styling
and print-optimized layout.
"""

from __future__ import annotations

from pathlib import Path

try:
    from weasyprint import HTML, CSS
except ImportError:
    HTML = None
    CSS = None


def html_to_pdf(html_content: str, output_path: Path) -> bool:
    """Convert HTML string to PDF file.

    Args:
        html_content: The HTML report as a string
        output_path: Path where the PDF should be saved

    Returns:
        True if successful, False if weasyprint not installed or error occurred
    """
    if HTML is None:
        return False

    try:
        # Create HTML document from string
        doc = HTML(string=html_content, base_url="/")

        # Add CSS for print optimization
        print_css = CSS(string="""
            @page {
                size: A4;
                margin: 0.5in;
            }
            body {
                background: white;
                color: #000;
            }
            .report-footer {
                display: none;
            }
            @media print {
                a {
                    text-decoration: underline;
                    color: #000080;
                }
            }
        """)

        # Write to PDF
        doc.write_pdf(str(output_path), stylesheets=[print_css])
        return True

    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False
