import streamlit as st


st.set_page_config(
    page_title="OnboardAI",
    page_icon="🤖",
    layout="wide",
)


st.title("🤖 OnboardAI")

st.subheader(
    "AI-Powered KYC & Customer Onboarding"
)


st.markdown(
    """
    Welcome to the OnboardAI AI Operations Console.

    Use the sidebar to:

    - Analyze documents
    - Review KYC cases
    - Perform human review
    - Inspect agent activity
    """
)


st.divider()


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "AI Agents",
        "4",
    )


with col2:

    st.metric(
        "Human Review",
        "Enabled",
    )


with col3:

    st.metric(
        "LLM",
        "Groq",
    )