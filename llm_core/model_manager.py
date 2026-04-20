from ui import ui

class ModelManager:
    # Default list of Groq models, ordered by preference
    DEFAULT_MODELS = [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]

    def __init__(self, models=None):
        self.models = models if models else self.DEFAULT_MODELS
        self.current_index = 0

    def get_current_model(self):
        if not self.models:
            return "llama-3.3-70b-versatile"
        return self.models[self.current_index]

    def rotate_model(self):
        """Switches to the next fallback model. Returns False if exhausted."""
        if len(self.models) <= 1:
            ui.print_error(f"Model {self.get_current_model()} failed. No fallback models available.")
            return False
            
        self.current_index = (self.current_index + 1) % len(self.models)
        if self.current_index == 0:
            return False
            
        new_model = self.get_current_model()
        ui.print_status(f"Model error encountered. Switching to fallback context model: {new_model}...")
        return True
