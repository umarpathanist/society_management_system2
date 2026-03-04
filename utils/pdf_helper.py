from io import BytesIO
from flask import render_template
from xhtml2pdf import pisa

def generate_pdf_blob(template_path, data):
    """Generates a PDF and returns it as a bytes object."""
    html = render_template(template_path, **data)
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    
    if pisa_status.err:
        return None
    return result.getvalue()