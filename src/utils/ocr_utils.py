import os

# Perform OCR on a PDF file
def perform_ocr_pdf(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.lower().endswith('.pdf'):
        raise ValueError(f"File {file_path} is not a PDF format")

    from markitdown import MarkItDown

    md = MarkItDown(enable_plugins=False) # Set to True to enable plugins
    result = md.convert(file_path)
    return result.text_content