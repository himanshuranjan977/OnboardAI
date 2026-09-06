
import streamlit as st
import requests

from api_client import upload_document


st.set_page_config(
    page_title="Document Analysis",
    page_icon="📄",
    layout="wide",
)


st.title("📄 Document Analysis")

st.write(
    "Upload a customer document and "
    "run the OnboardAI verification workflow."
)


st.divider()


# =========================================
# CASE INFORMATION
# =========================================

st.subheader("Case Information")


case_id = st.number_input(
    "Case ID",
    min_value=1,
    value=1,
    step=1,
)


# =========================================
# DOCUMENT UPLOAD
# =========================================

st.subheader("Upload Document")


# Document type
document_type = st.selectbox(
    "Document Type",
    [
        "passport",
        "national_id",
        "driving_license",
        "address_proof",
        "bank_statement",
    ],
)


uploaded_file = st.file_uploader(
    "Choose a document",
    type=[
        "pdf",
        "png",
        "jpg",
        "jpeg",
    ],
)


if uploaded_file:

    st.success(
        f"Selected: {uploaded_file.name}"
    )

    st.write(
        f"File size: "
        f"{uploaded_file.size / 1024:.2f} KB"
    )

    st.divider()


    # =====================================
    # RUN ANALYSIS
    # =====================================

    if st.button(
        "🚀 Run AI Analysis",
        use_container_width=True,
    ):

        with st.spinner(
            "Running OnboardAI analysis..."
        ):

            try:

                # =====================================
                # UPLOAD DOCUMENT USING API CLIENT
                # =====================================

                result = upload_document(

                    case_id=case_id,

                    document_type=document_type,

                    file_name=uploaded_file.name,

                    file_bytes=
                        uploaded_file.getvalue(),

                    content_type=
                        uploaded_file.type,
                )


                st.success(
                    "Document uploaded successfully."
                )


                st.session_state[
                    "analysis_result"
                ] = result


            except requests.exceptions.ConnectionError:

                st.error(
                    "Cannot connect to FastAPI. "
                    "Make sure the backend is running."
                )


            except requests.exceptions.Timeout:

                st.error(
                    "The analysis took too long. "
                    "Please try again."
                )


            except requests.exceptions.HTTPError as exc:

                st.error(
                    f"FastAPI returned an error: {exc}"
                )


            except Exception as exc:

                st.error(
                    f"Analysis failed: {exc}"
                )


# =========================================
# ANALYSIS RESULT
# =========================================

result = st.session_state.get(
    "analysis_result"
)


if result:

    st.divider()

    st.header("🔍 Analysis Result")


    # =====================================
    # SUMMARY
    # =====================================

    summary = result.get(
        "summary"
    )


    if summary:

        st.subheader(
            "Analysis Summary"
        )

        st.write(summary)


    # =====================================
    # DOCUMENT
    # =====================================

    document = result.get(
        "document"
    )


    if document:

        st.subheader(
            "📄 Document"
        )

        st.json(
            document
        )


    # =====================================
    # IDENTITY
    # =====================================

    identity = result.get(
        "identity"
    )


    if identity:

        st.subheader(
            "🪪 Identity Verification"
        )

        col1, col2 = st.columns(2)


        with col1:

            st.metric(
                "Result",

                identity.get(
                    "result",
                    "UNKNOWN",
                ),
            )


        with col2:

            st.metric(
                "Confidence",

                identity.get(
                    "confidence",
                    "N/A",
                ),
            )


        if identity.get(
            "explanation"
        ):

            st.write(
                identity["explanation"]
            )


    # =====================================
    # RISK
    # =====================================

    risk = result.get(
        "risk"
    )


    if risk:

        st.subheader(
            "⚠️ Risk Assessment"
        )

        col1, col2 = st.columns(2)


        with col1:

            st.metric(
                "Risk",

                risk.get(
                    "result",
                    "UNKNOWN",
                ),
            )


        with col2:

            st.metric(
                "Confidence",

                risk.get(
                    "confidence",
                    "N/A",
                ),
            )


        if risk.get(
            "explanation"
        ):

            st.write(
                risk["explanation"]
            )


    # =====================================
    # DECISION
    # =====================================

    decision = result.get(
        "decision"
    )


    if decision:

        st.subheader(
            "🤖 AI Decision"
        )


        decision_result = (
            decision.get(
                "result",
                "UNKNOWN",
            )
        )


        if decision_result == "APPROVE":

            st.success(
                "AI recommends APPROVE"
            )


        elif decision_result == "REJECT":

            st.error(
                "AI recommends REJECT"
            )


        else:

            st.warning(
                f"AI Decision: "
                f"{decision_result}"
            )


        if decision.get(
            "explanation"
        ):

            st.write(
                decision["explanation"]
            )


    # =====================================
    # HUMAN REVIEW
    # =====================================

    human_review = result.get(
        "human_review"
    )


    if human_review:

        st.subheader(
            "👤 Human Review"
        )


        st.warning(
            "This case requires human review."
        )


        st.json(
            human_review
        )

