from groq import Groq

from config.settings import settings


client = Groq(
    api_key=settings.groq_api_key
)


response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "user",
            "content": "Explain KYC in one sentence."
        }
    ],
)


print(response.choices[0].message.content)