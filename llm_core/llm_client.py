import groq
from ui import ui
from .key_manager import KeyManager
from .model_manager import ModelManager

class LLMClient:
    def __init__(self, key_manager: KeyManager, model_manager: ModelManager):
        self.key_manager = key_manager
        self.model_manager = model_manager
        self.client = None
        self._init_client()

    def _init_client(self):
        # Initializes or re-initializes the groq client with the current key
        api_key = self.key_manager.get_current_key()
        if api_key:
            self.client = groq.Groq(api_key=api_key)
        else:
            ui.print_error("Cannot initialize Groq Client: No API Key provided.")

    def generate_response(self, messages):
        while True:
            if not self.client:
                self._init_client()
                if not self.client:
                    return "{}" # fail safe

            model = self.model_manager.get_current_model()
            ui.start_thinking(f"Thinking with {model}...")

            try:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=1,
                    max_completion_tokens=1000,
                    top_p=1,
                    stream=True,
                    stop=None
                )
                
                full_response = ""
                for chunk in completion:
                    delta = chunk.choices[0].delta.content or ""
                    full_response += delta
                
                ui.stop_thinking()
                return full_response

            except groq.RateLimitError as e:
                ui.stop_thinking()
                ui.print_error(f"RateLimitError: {str(e)}")
                # Try fallback key
                if self.key_manager.rotate_key():
                    self._init_client()
                    continue
                else:
                    return "{}"
            except groq.AuthenticationError as e:
                ui.stop_thinking()
                ui.print_error(f"AuthenticationError: API Key is invalid.")
                if self.key_manager.rotate_key():
                    self._init_client()
                    continue
                else:
                    return "{}"
            except Exception as e:
                ui.stop_thinking()
                raw_error = str(e)
                user_message = "The AI service could not complete the request right now. Please try again."

                if "model_not_found" in raw_error or "does not exist or you do not have access to it" in raw_error:
                    user_message = (
                        "The selected AI model is unavailable right now. "
                        "The app will try a fallback model automatically."
                    )
                elif "404" in raw_error:
                    user_message = (
                        "The AI service returned an invalid response. "
                        "Please try again in a moment."
                    )

                ui.print_error(f"{user_message}")
                # Keep the raw error out of the normal user message, but preserve fallback behavior.
                # Try fallback model
                if self.model_manager.rotate_model():
                    continue
                else:
                    return "{}"
