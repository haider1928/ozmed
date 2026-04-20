from llm_core.key_manager import KeyManager
from llm_core.model_manager import ModelManager
from llm_core.chat import Chat
from runner.python_shell import PythonShell
import json
from ui import ui

def main():
    # 1. Initialize Managers
    key_manager = KeyManager()
    model_manager = ModelManager()

    # 2. Check Key
    if not key_manager.get_current_key():
        ui.print_error("Failed to start Ozmed AI. No valid Groq API key found.")
        return

    # 3. Initialize Chat and Env
    ozmed_chat = Chat(key_manager, model_manager)
    python_shell = PythonShell()

    ui.print_success("Ozmed AI successfully initialized.")
    ui.print_status("Type 'exit' or 'quit' to close.")
    
    input_text = ""
    response = {}

    while True:
        current_input = input_text

        if not current_input:
            try:
                import builtins

                ui.print_status("Ready:")
                user_input = builtins.input("You: ")
            except EOFError:
                ui.print_success("Goodbye!")
                break

            if user_input.lower() in ["exit", "quit"]:
                ui.print_success("Goodbye!")
                break

            current_input = user_input
        else:
            input_text = ""

        # 4. Generate AI response
        response = ozmed_chat.send_message(current_input)
        
        if not response:
            continue

        # Display actual AI response content
        if "response" in response:
            ui.print_ai(response["response"])

        # Display and Execute: python_shell
        if "python_shell" in response:
            code = "\n".join(response["python_shell"].get("code", []))
            ui.print_tool_start("python_shell", code)
            
            outputs = python_shell.run_from_json(response)
            
            output_text = "\n".join(outputs)
            
            ui.print_tool_output("python_shell", output_text)
            
            input_text = "SYSTEM EXECUTION RESULT:\n" + output_text
            continue

        # Display and Execute: run_powershell
        if "run_powershell" in response:
            from runner.powershell_shell import run_powershell
            commands = "\n".join(response["run_powershell"].get("commands", []))
            
            ui.print_tool_start("run_powershell", commands)
            outputs = run_powershell(response)
            output_text = "\n".join(outputs)
            ui.print_tool_output("run_powershell", output_text)

            input_text = "SYSTEM EXECUTION RESULT:\n" + output_text
            continue

        # Display and Execute: nested actions array
        if "actions" in response:
            all_outputs = []
            
            for action in response["actions"]:
                if "python_shell" in action:
                    code = "\n".join(action["python_shell"].get("code", []))
                    ui.print_tool_start("python_shell", code)
                    
                    # We need a function to just run action dictionary on python_shell
                    outputs = python_shell.run_from_json(action)
                    all_outputs.extend(outputs)
                    
                    output_text = "\n".join(outputs)
                    ui.print_tool_output("python_shell", output_text)

            input_text = "SYSTEM EXECUTION RESULT:\n" + "\n".join(all_outputs)
            continue

        # Display and Execute: search_internet
        if "search_internet" in response:
            from runner.search_internet import search_internet
            queries = response["search_internet"].get("queries", [])
            ui.print_tool_start("search_internet", ", ".join(queries))
            
            ddgs_results = search_internet(response)
            output_text = json.dumps(ddgs_results, indent=4)
            ui.print_tool_output("search_internet", output_text)
            
            input_text = "SYSTEM EXECUTION RESULT:\n" + output_text
            continue

        # reset shell
        if "reset_python_shell" in response:
            outputs = python_shell.reset()
            ui.print_tool_start("reset_python_shell", "")
            output_text = "\n".join(outputs)
            ui.print_tool_output("reset_python_shell", output_text)
            
            input_text = "SYSTEM EXECUTION RESULT:\n" + output_text
            continue

if __name__ == "__main__":
    # Ensure graceful exit on Ctrl+C
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
