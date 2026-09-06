from agents.identity import (
    verify_identity,
)


result = verify_identity(

    customer_id=1,

    document_analysis={

        "document_type":
            "passport",

        "full_name":
            "Rahul Sharma",

        "date_of_birth":
            "1995-08-15",

        "document_number":
            "P1234567",

        "address":
            "Patna, Bihar, India",

        "nationality":
            "Indian",

        "confidence":
            0.95,

        "missing_fields": [],

        "warnings": [],
    }
)


print("\nIDENTITY VERIFICATION")
print("======================")

print(
    f"Status: "
    f"{result['identity_status']}"
)

print(
    f"Score: "
    f"{result['match_score']}"
)

print("\nFields:")

for field in result[
    "field_results"
]:

    print(
        f"{field['field']}: "
        f"{field['status']}"
    )

print("\nWarnings:")

for warning in result[
    "warnings"
]:

    print(
        f"- {warning}"
    )