
import groq

from .config import GROQ_API_KEY
#print(f"OPENROUTER_API_KEY: {OPENROUTER_API_KEY}")
import groq
from .config import GROQ_API_KEY

class LLMClient:
    def __init__(self, api_key, model="openai/gpt-oss-120b"):
        self.api_key = api_key
        self.model = model
        self.client = groq.Groq(api_key=self.api_key)

    def generate_response(self, messages, model="openai/gpt-oss-120b"):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            max_completion_tokens=1000,
            top_p=1,
            reasoning_effort="medium",
            stream=True,
            stop=None
        )
        full_response = ""
        for chunk in completion:
            delta = chunk.choices[0].delta.content or ""
            print(delta, end="", flush=True)
            full_response += delta
        print()
        return full_response
    
    
if __name__ == "__main__":
    llm_client = LLMClient(api_key=GROQ_API_KEY, model="openai/gpt-oss-120b")
    response = llm_client.generate_response(
        messages=[
            {
                "role": "user",
                "content": "What is the meaning of life?"
            }
        ]
    )
    print(response)

