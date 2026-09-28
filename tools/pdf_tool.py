import io
import fitz


def extract_pdf_text(pdf_source) -> str:
    if hasattr(pdf_source, 'read'):
        data = pdf_source.read()
    elif isinstance(pdf_source, (bytes, bytearray)):
        data = bytes(pdf_source)
    else:
        with open(pdf_source, 'rb') as f:
            data = f.read()
    doc = fitz.open(stream=data, filetype='pdf')
    pages = []
    for i, page in enumerate(doc):
        pages.append(f'\n--- PAGE {i+1} ---\n{page.get_text("text")}')
    return ''.join(pages).strip()
