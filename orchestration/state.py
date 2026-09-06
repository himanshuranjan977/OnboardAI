from typing import (
    TypedDict,
    Optional,
    Dict,
    Any,
)


class KYCState(TypedDict, total=False):

    # ==================================
    # Case
    # ==================================

    case_id: int

    customer_id: int

    # ==================================
    # Workflow
    # ==================================

    workflow_status: str

    current_agent: str

    # ==================================
    # Document
    # ==================================

    document_id: Optional[int]

    document_path: Optional[str]

    document_type: Optional[str]

    document_text: Optional[str]

    # ==================================
    # Document analysis
    # ==================================

    document_analysis: Optional[
        Dict[str, Any]
    ]

    # ==================================
    # Identity
    # ==================================

    identity_verification: Optional[
        Dict[str, Any]
    ]

    # ==================================
    # Risk
    # ==================================

    risk_assessment: Optional[
        Dict[str, Any]
    ]

    # ==================================
    # Automated decision
    # ==================================

    final_decision: Optional[
        Dict[str, Any]
    ]

    # ==================================
    # Human review
    # ==================================

    review_status: Optional[str]

    review_decision: Optional[str]

    reviewer_name: Optional[str]

    reviewer_comment: Optional[str]

    # ==================================
    # Error
    # ==================================

    error: Optional[str]

    # ==================================
    # Human review control
    # ==================================

    requires_human_review: bool

    human_review_reason: Optional[str]