from services.document_ai_service import (
    analyze_pdf_document
)


PDF_PATH = r"F:\New folder (3)\Himanshu_Ranjan_Resume_29-07-2023-22-18-26.pdf"


result = analyze_pdf_document(
    PDF_PATH
)


print("\nDOCUMENT AI RESULT")
print("==================")

print(result)