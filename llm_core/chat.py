import os
import json
from .llm_client import LLMClient
from .memory import Memory
from .config import SYSTEM_PROMPT
from .key_manager import KeyManager
from .model_manager import ModelManager
from utils.parser import Parser
from ui import ui


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
memory_file = os.path.join(BASE_DIR, "memory.json")


class Chat:
    def __init__(self, key_manager: KeyManager, model_manager: ModelManager):
        self.llm_client = LLMClient(key_manager, model_manager)
        self.memory = Memory(memory_file)
        self.parser = Parser()

    def send_message(self, message, system_prompt=SYSTEM_PROMPT):
        # 1. Ask the LLM to generate response
        response_text = self.llm_client.generate_response(
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

        # 2. Extract JSON safely
        try:
            json_response = self.parser.extract_json(response_text)
            
            # save memory only if parse successful
            self.memory.add_to_memory(message, json.dumps(json_response))
            return json_response
            
        except ValueError as e:
            ui.print_error(f"Parsing Failed: {str(e)}")
            # Even if it crashed, return empty dict safely
            return {}