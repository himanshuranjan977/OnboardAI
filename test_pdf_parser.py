from services.document_parser import (
    extract_text_from_pdf
)


PDF_PATH = r"F:\New folder (3)\Himanshu_Ranjan_Resume_14-08-2023-09-26-21.pdf"


text = extract_text_from_pdf(
    PDF_PATH
)


print(text)