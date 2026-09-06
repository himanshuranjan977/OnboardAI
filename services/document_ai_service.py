from agents.document import (
    extract_document_information
)

from services.document_parser import (
    extract_text_from_pdf
)


def analyze_pdf_document(
    file_path: str
) -> dict:

    # Step 1: Extract text
    document_text = extract_text_from_pdf(
        file_path
    )

    if not document_text.strip():

        return {
            "success": False,
            "error": (
                "No text could be extracted "
                "from the document."
            ),
        }

    # Step 2: Send extracted text
    # to Document Intelligence Agent

    result = extract_document_information(
        document_text
    )

    return {
        "success": True,
        "result": result,
    }