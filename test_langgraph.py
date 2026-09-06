from orchestration.graph import (
    build_kyc_graph,
)


graph = build_kyc_graph()


sample_document = """
REPUBLIC OF INDIA

PASSPORT

Name:
Rahul Kumar

Date of Birth:
1995-08-15

Passport Number:
P1234567

Nationality:
Indian

Address:
Patna, Bihar, India
"""


initial_state = {

    "case_id": 1,

    "customer_id": 1,

    "workflow_status":
        "READY_FOR_DOCUMENT_ANALYSIS",

    "current_agent":
        "supervisor",

    "document_id": 1,

    "document_type":
        "passport",

    "document_text":
        sample_document,

    "document_analysis":
        None,

    "identity_verification":
        None,

    "risk_assessment":
        None,

    "final_decision": 
        None,

    "error":
        None,

    "requires_human_review":
        False,

    "human_review_reason":
        None,
}


print("\n==============================")
print(" ONBOARDAI KYC WORKFLOW")
print("==============================\n")


result = graph.invoke(
    initial_state
)


print("\n==============================")
print(" FINAL STATE")
print("==============================\n")


for key, value in result.items():

    print(
        f"{key}: {value}"
    )