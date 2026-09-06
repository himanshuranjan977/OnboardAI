"""OCR intake service.

The original customer document is always kept on disk. OCR reads a copy of the
content and stores the extracted text in the document record; the original file
is never replaced by OCR output.
"""

from pathlib import Path
from io import BytesIO

from services.document_parser import extract_text_from_pdf

import pytesseract

# Windows Tesseract OCR executable
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text(file_path: str, mime_type: str | None = None) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(file_path)

    ext = path.suffix.lower()

    # ---------------------------------------------------------
    # PDF
    # ---------------------------------------------------------
    if ext == ".pdf":
        text = extract_text_from_pdf(str(path)) or ""

        # If PDF already contains selectable text, use it.
        if text.strip():
            return text

        # Scanned PDF -> render pages -> Tesseract OCR
        try:
            import fitz
            from PIL import Image

            doc = fitz.open(str(path))
            pages = []

            for page in doc:
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2),
                    alpha=False
                )

                image = Image.open(
                    BytesIO(pix.tobytes("png"))
                )

                page_text = pytesseract.image_to_string(image)
                pages.append(page_text)

            doc.close()

            return "\n\n".join(pages)

        except ImportError:
            raise RuntimeError(
                "Scanned PDF OCR requires PyMuPDF, Pillow and "
                "pytesseract. Install requirements and Tesseract OCR "
                "on Windows."
            )

        except Exception as exc:
            raise RuntimeError(
                f"Scanned PDF OCR failed: {exc}"
            )

    # ---------------------------------------------------------
    # IMAGE
    # ---------------------------------------------------------
    if ext in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".tif",
        ".tiff",
    }:
        try:
            from PIL import Image

            image = Image.open(path)

            return pytesseract.image_to_string(image)

        except ImportError:
            raise RuntimeError(
                "Image OCR requires Pillow and pytesseract. "
                "Install requirements and Tesseract OCR on Windows."
            )

        except Exception as exc:
            raise RuntimeError(
                f"Image OCR failed: {exc}"
            )

    # ---------------------------------------------------------
    # UNSUPPORTED FILE
    # ---------------------------------------------------------
    raise ValueError(
        "Unsupported document format for OCR."
    )