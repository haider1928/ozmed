from .llm_client import LLMClient
from .memory import Memory
from .config import GROQ_API_KEY, SYSTEM_PROMPT
class Chat:
    def __init__(self, api_key):
        self.llm_client = LLMClient(api_key)
        self.memory = Memory("memory.json")

    def send_message(self, message, system_prompt=SYSTEM_PROMPT):
        #print(f"Memory before sending message: {self.memory.get_memory()}")
        #print(self.memory.get_memory() + [
        #    {
        #        "role": "user",
        #        "content": message
        #    }
        #])
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
        #print(f"LLM response: {response}")
        return response
if __name__ == "__main__":
    chat = Chat(api_key=GROQ_API_KEY)
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break       
        response = chat.send_message(user_input)
        print(f"LLM: {response}")