import os
import json
from .llm_client import LLMClient
from .memory import Memory
from .config import GROQ_API_KEY, SYSTEM_PROMPT


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
memory_file = os.path.join(BASE_DIR, "memory.json")


class Chat:
    def __init__(self, api_key):
        self.llm_client = LLMClient(api_key, model="openai/gpt-oss-120b")
        self.memory = Memory(memory_file)

    def send_message(self, message, system_prompt=SYSTEM_PROMPT):
        response = self.llm_client.generate_response(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                }
            ] + self.memory.get_memory() + [
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        # ← extract only the last valid JSON (ignores reasoning draft blocks)
       

        # ← save clean serialized JSON to memory, not the raw stream
        
        json_response = json.loads(response)
        self.memory.add_to_memory(message, response)

        return json_response


if __name__ == "__main__":
    chat = Chat(api_key=GROQ_API_KEY, )
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = chat.send_message(user_input)
        print(response)