import streamlit as st

from api_client import (
    get_pending_reviews,
    get_case_summary,
    submit_review,
)


st.set_page_config(
    page_title="Human Review",
    page_icon="👤",
    layout="wide",
)


st.title("👤 Human Review")


try:

    reviews = get_pending_reviews()

except Exception as exc:

    st.error(
        f"Unable to connect to backend: {exc}"
    )

    st.stop()


if not reviews:

    st.success(
        "No pending human reviews."
    )

    st.stop()


st.write(
    f"Pending reviews: {len(reviews)}"
)


for review in reviews:

    review_id = review["id"]

    case_id = review["case_id"]


    with st.expander(
        f"Review #{review_id} — Case #{case_id}",
        expanded=True,
    ):

        st.write(
            f"**Review ID:** {review_id}"
        )

        st.write(
            f"**Case ID:** {case_id}"
        )

        st.write(
            f"**Status:** {review['status']}"
        )


        try:

            summary = get_case_summary(
                case_id
            )

        except Exception as exc:

            st.error(
                f"Unable to load case: {exc}"
            )

            continue


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "Case Status",
                summary["ui"]["status_label"],
            )


        with col2:

            risk = summary.get("risk")

            if risk:

                st.metric(
                    "Risk",
                    risk.get(
                        "result",
                        "Unknown",
                    ),
                )

            else:

                st.metric(
                    "Risk",
                    "Unknown",
                )


        with col3:

            decision = summary.get(
                "decision"
            )

            if decision:

                st.metric(
                    "AI Decision",
                    decision.get(
                        "result",
                        "Unknown",
                    ),
                )

            else:

                st.metric(
                    "AI Decision",
                    "Unknown",
                )


        st.divider()


        st.subheader(
            "Customer"
        )


        customer = summary.get(
            "customer"
        )


        if customer:

            st.json(
                customer
            )

        else:

            st.info(
                "Customer information unavailable."
            )


        st.subheader(
            "Documents"
        )


        documents = summary.get(
            "documents",
            [],
        )


        if documents:

            st.dataframe(
                documents,
                use_container_width=True,
            )

        else:

            st.info(
                "No documents found."
            )


        st.subheader(
            "Evidence"
        )


        evidence = summary.get(
            "evidence",
            [],
        )


        if evidence:

            st.dataframe(
                evidence,
                use_container_width=True,
            )

        else:

            st.info(
                "No evidence found."
            )


        st.divider()


        st.subheader(
            "Reviewer Decision"
        )


        reviewer_name = st.text_input(
            "Reviewer name",
            key=f"name_{review_id}",
        )


        decision = st.selectbox(

            "Decision",

            [
                "APPROVE",
                "REJECT",
            ],

            key=f"decision_{review_id}",
        )


        comment = st.text_area(

            "Review comment",

            key=f"comment_{review_id}",
        )


        if st.button(
            "Submit Decision",
            key=f"submit_{review_id}",
        ):

            if not reviewer_name.strip():

                st.warning(
                    "Please enter reviewer name."
                )

                continue


            try:

                result = submit_review(

                    review_id=review_id,

                    decision=decision,

                    reviewer_name=
                        reviewer_name,

                    reviewer_comment=
                        comment,
                )


                st.success(
                    "Review submitted successfully."
                )


                st.json(
                    result
                )


                st.rerun()


            except Exception as exc:

                st.error(
                    f"Unable to submit review: {exc}"
                )