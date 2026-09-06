from agents.document import (
    extract_document_information
)


sample_document = """
PASSPORT

Republic of India

Name:
Rahul Sharma

Date of Birth:
15 August 1995

Passport Number:
P1234567

Nationality:
Indian

Address:
Patna, Bihar, India
"""


result = extract_document_information(
    sample_document
)


print("\nDOCUMENT ANALYSIS RESULT")
print("========================")

for key, value in result.items():

    print(
        f"{key}: {value}"
    )