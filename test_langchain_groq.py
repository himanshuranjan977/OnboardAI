from llm.groq_client import llm


response = llm.invoke(
    "Explain KYC in one short sentence."
)


print(response.content)