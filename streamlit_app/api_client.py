
import requests


BASE_URL = "http://127.0.0.1:8000"


def get_case_summary(case_id: int):

    response = requests.get(

        f"{BASE_URL}/api/cases/{case_id}/summary",

        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def get_pending_reviews():

    response = requests.get(

        f"{BASE_URL}/api/reviews/pending",

        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def submit_review(
    review_id: int,
    decision: str,
    reviewer_name: str,
    reviewer_comment: str,
):

    response = requests.post(

        f"{BASE_URL}/api/reviews/"
        f"{review_id}/decision",

        json={

            "decision": decision,

            "reviewer_name":
                reviewer_name,

            "reviewer_comment":
                reviewer_comment,
        },

        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def upload_document(
    case_id: int,
    document_type: str,
    file_name: str,
    file_bytes: bytes,
    content_type: str,
):

    files = {

        "file": (

            file_name,

            file_bytes,

            content_type,
        )

    }


    data = {

        "case_id":
            str(case_id),

        "document_type":
            document_type,
    }


    response = requests.post(

        f"{BASE_URL}/api/documents/upload",

        files=files,

        data=data,

        timeout=120,
    )


    response.raise_for_status()


    return response.json()

