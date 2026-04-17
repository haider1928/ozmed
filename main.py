from llm_core.chat import Chat
from llm_core.config import GROQ_API_KEY
from runner.python_shell import PythonShell
import json
#from runner.powershell_shell import run_powershell
ozmed_chat = Chat(api_key=GROQ_API_KEY)
python_shell = PythonShell()
#powershell_shell = PowershellShell()

if __name__ == "__main__":
    input_text = ""
    response = {}

    while True:
        awaiting = response.get("python_shell", {}).get("awaiting_output", False)

        if not awaiting:
            input_text = input("You: ")
            if input_text.lower() in ["exit", "quit"]:
                break

        try:
            response = ozmed_chat.send_message(input_text)
        except ValueError as e:
            print(f"[PARSE ERROR] {e}")
            response = {}
            continue

        if "python_shell" in response:
            
            outputs = python_shell.run_from_json(response)
            input_text = "SYSTEM EXECUTION RESULT:\n" + "\n".join(outputs)
            print(input_text)  # print before sending back to LLM

            # send the tool output back immediately
            response = ozmed_chat.send_message(input_text)

        if "run_powershell" in response:
            from runner.powershell_shell import run_powershell
            outputs = run_powershell(dict(response))
            input_text = "SYSTEM EXECUTION RESULT:\n" + "\n".join(outputs)
            response = ozmed_chat.send_message(input_text)

        if "actions" in response:
            from runner.python_shell import run_python_shell
            all_outputs = []
            for action in response["actions"]:
                if "python_shell" in action:
                    outputs = run_python_shell(action)
                    all_outputs.extend(outputs)
            input_text = "SYSTEM EXECUTION RESULT:\n" + "\n".join(all_outputs)
            response = ozmed_chat.send_message(input_text)



        if "search_internet" in response:
            from runner.search_internet import search_internet
            ddgs_results = search_internet(dict(response))

            input_text = "SYSTEM EXECUTION RESULT:\n" + "\n".join(json.dumps(ddgs_results, indent=4))
            response = ozmed_chat.send_message(input_text)

        if "reset_python_shell" in response:
            outputs = python_shell.reset()
            input_text = "SYSTEM EXECUTION RESULT:\n" + "\n".join(outputs)
            response = ozmed_chat.send_message(input_text)