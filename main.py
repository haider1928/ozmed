from llm_core.chat import Chat
from llm_core.config import GROQ_API_KEY
from runner.python_shell import PythonShell
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

            # send the tool output back immediately
            response = ozmed_chat.send_message(input_text)

        elif "run_powershell" in response:
            from runner.powershell_shell import run_powershell
            outputs = run_powershell(response)
            input_text = "SYSTEM EXECUTION RESULT:\n" + "\n".join(outputs)
            response = ozmed_chat.send_message(input_text)

        elif "actions" in response:
            from runner.python_shell import run_python_shell
            all_outputs = []
            for action in response["actions"]:
                if "python_shell" in action:
                    outputs = run_python_shell(action)
                    all_outputs.extend(outputs)

            input_text = "SYSTEM EXECUTION RESULT:\n" + "\n".join(all_outputs)
            response = ozmed_chat.send_message(input_text)