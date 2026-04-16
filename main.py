from llm_core.chat import Chat
from llm_core.llm_client import OPENROUTER_API_KEY
chat_instance = Chat(api_key=OPENROUTER_API_KEY)
response = chat_instance.send_message("Hello, how are you?")
print(response)
sresponse = chat_instance.send_message("what was my previous message?")
print(sresponse)