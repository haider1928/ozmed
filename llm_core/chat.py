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
        relevant_memory = self.memory.get_relevant_deep_memory(message, limit=8)
        memory_context = ""
        if relevant_memory:
            memory_context = "\n\nRELEVANT DEEP MEMORY:\n" + json.dumps(relevant_memory, indent=2, ensure_ascii=False)

        # 1. Ask the LLM to generate response
        response_text = self.llm_client.generate_response(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt + memory_context
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
            self._maybe_save_deep_memory(message, json_response)
            return json_response
            
        except ValueError as e:
            ui.print_error(f"Parsing Failed: {str(e)}")
            # Even if it crashed, return empty dict safely
            return {}

    def _maybe_save_deep_memory(self, user_message, json_response):
        if not isinstance(json_response, dict):
            return

        candidates = []
        if "response" in json_response and isinstance(json_response["response"], str):
            candidates.append(json_response["response"])

        if any(key in json_response for key in ["preferences", "goals", "tasks", "memory", "notes"]):
            candidates.append(json.dumps(json_response, ensure_ascii=False))

        for candidate in candidates:
            self.memory.add_memory(
                {
                    "type": "assistant_summary",
                    "summary": self._summarize_for_memory(candidate),
                    "importance": "medium",
                    "confidence": 0.65,
                    "source": "chat",
                    "scope": "long_term",
                },
                memory_type="deep",
            )

        self.memory.add_memory(
            {
                "type": "user_intent",
                "summary": self._summarize_for_memory(user_message),
                "importance": "high",
                "confidence": 0.8,
                "source": "chat",
                "scope": "long_term",
            },
            memory_type="deep",
        )

    def _summarize_for_memory(self, text: str, limit: int = 240) -> str:
        text = " ".join(str(text).split())
        if len(text) <= limit:
            return text
        return text[: limit - 20] + " ..."
