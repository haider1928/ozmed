import os
import json


class Memory:
    def __init__(self, memory_file):
        self.memory_file = memory_file
        self.memory_limit = 10  # Max number of message pairs to keep in memory
        self._init_file()

    # ----------------------------
    # Initialize file safely
    # ----------------------------
    def _init_file(self):
        if not os.path.exists(self.memory_file) or os.path.getsize(self.memory_file) == 0:
            with open(self.memory_file, "w") as f:
                json.dump({"messages": []}, f, indent=4)

    # ----------------------------
    # Load full memory
    # ----------------------------
    def get_memory(self):
        with open(self.memory_file, "r") as f:
            data = json.load(f)

        if "messages" not in data or not isinstance(data["messages"], list):
            data["messages"] = []

        # Limit the number of message pairs
        data["messages"] = data["messages"][-self.memory_limit * 2:]  # Each pair consists of two messages

        return data["messages"]

        

    # ----------------------------
    # Add a message pair
    # ----------------------------
    def add_to_memory(self, user_message, llm_response):
        data = self.get_full_data()

        data["messages"].append({
            "role": "user",
            "content": user_message
        })

        data["messages"].append({
            "role": "assistant",
            "content": llm_response
        })

        with open(self.memory_file, "w") as f:
            json.dump(data, f, indent=4)

    # ----------------------------
    # Internal: load full JSON
    # ----------------------------
    def get_full_data(self):
        with open(self.memory_file, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"messages": []}

        if "messages" not in data:
            data["messages"] = []

        return data