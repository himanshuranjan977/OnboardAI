from functools import lru_cache

from config.settings import settings


@lru_cache(maxsize=1)
def get_llm():
    if not settings.groq_api_key.strip():
        return None
    from langchain_groq import ChatGroq
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0,
    )


class LazyLLM:
    def invoke(self, prompt):
        llm = get_llm()
        if llm is None:
            raise RuntimeError("GROQ_API_KEY is not configured")
        return llm.invoke(prompt)


llm = LazyLLM()
