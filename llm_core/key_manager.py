import os
from ui import ui

class KeyManager:
    def __init__(self):
        self.keys = []
        self.current_index = 0
        self.load_keys_from_env()

    def load_keys_from_env(self):
        for k, v in os.environ.items():
            if k.startswith("GROQ_API_KEY") and v.strip():
                if v.strip() not in self.keys:
                    self.keys.append(v.strip())

    def get_current_key(self):
        if not self.keys:
            # Fallback - Ask user
            ui.print_warning("No Groq API keys found in environment.")
            key = input("Please enter a Groq API Key: ").strip()
            if key:
                self.add_key(key)
                return key
            else:
                return None
        return self.keys[self.current_index]

    def add_key(self, key):
        if key not in self.keys:
            self.keys.append(key)

    def rotate_key(self):
        """Switches to the next available key and returns False if we looped back."""
        if len(self.keys) <= 1:
            ui.print_error("No other fallback keys available.")
            return False
            
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.keys)
        # If we looped around to the start, return False (exhausted all keys)
        if self.current_index == 0:
            return False
            
        ui.print_status("Rate limit or error encountered. Switching to fallback API key...")
        return True
