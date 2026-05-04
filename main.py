from llm_core.key_manager import KeyManager
from llm_core.model_manager import ModelManager
from llm_core.chat import Chat
from llm_core.tool_output import OutputProcessor
from runner.python_shell import PythonShell
import json
from ui import ui

class SessionState:
    def __init__(self):
        self.committed_shell = None
        self.last_failed = False
        self.search_performed = False

    def reset(self):
        self.committed_shell = None
        self.last_failed = False
        self.search_performed = False

def validate_response(response, state):
    if not response:
        return None
    
    # 1. Thinking Block Enforcement
    if "thinking" not in response:
        return "CRITICAL ERROR: No 'thinking' block found. You MUST output a structured thinking object before any action."
    
    thinking = response.get("thinking", {})
    shell_choice = thinking.get("shell_choice")
    
    # 2. Shell Discipline
    if shell_choice in ["python_shell", "run_powershell"]:
        if state.committed_shell and state.committed_shell != shell_choice:
            return f"SHELL VIOLATION: You committed to {state.committed_shell} for this task. Switching to {shell_choice} is forbidden."
        if not state.committed_shell:
            state.committed_shell = shell_choice

    # 3. Mandatory Search for Non-Trivial Tasks
    has_script = "python_shell" in response or "run_powershell" in response
    is_searching = "search_internet" in response
    
    if has_script and not state.search_performed and not is_searching:
        content = ""
        if "python_shell" in response:
            content = "\n".join(response["python_shell"].get("code", []))
        elif "run_powershell" in response:
            content = "\n".join(response["run_powershell"].get("commands", []))
            
        non_trivial_keywords = ["pip", "install", "requests", "selenium", "playwright", "api", "open", "subprocess", "os.system"]
        if any(k in content.lower() for k in non_trivial_keywords):
            return "SEARCH REQUIRED: The proposed script involves non-trivial operations (install, API, scraping, or system commands). You MUST call search_internet first."

    # 4. Error Handling Flow Automation
    if state.last_failed and not is_searching:
        return "ERROR RECOVERY VIOLATION: A previous action failed. You MUST call search_internet with the exact error message before retrying."

    return None

def main():
    # 1. Initialize Managers
    key_manager = KeyManager()
    model_manager = ModelManager()

    # 2. Check Key
    if not key_manager.get_current_key():
        ui.print_error("Failed to start Ozmed AI. No valid Groq API key found.")
        return

    # 3. Initialize Chat, Env and State
    ozmed_chat = Chat(key_manager, model_manager)
    python_shell = PythonShell()
    output_processor = OutputProcessor()
    state = SessionState()

    ui.print_success("Ozmed AI successfully initialized.")
    ui.print_status("Type 'exit' or 'quit' to close.")
    
    input_text = ""
    
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
            state.reset()  # New user input resets task state
        else:
            input_text = ""

        # 4. Generate AI response
        response = ozmed_chat.send_message(current_input)
        
        if not response:
            continue

        # UI: Thinking and Report
        if "thinking" in response:
            ui.print_thinking(response["thinking"])
        
        if "improvement_report" in response:
            ui.print_improvement_report(response["improvement_report"])

        # Validation
        validation_error = validate_response(response, state)
        if validation_error:
            ui.print_error(validation_error)
            input_text = f"SYSTEM VALIDATION ERROR: {validation_error}"
            continue

        # 5. Process Actions
        if "response" in response:
            ui.print_ai(response["response"])

        # Track search
        if "search_internet" in response:
            state.search_performed = True

        # Tool Execution Loop (Gated: Stop after execution tool if awaiting_output is true)
        all_outputs = []
        action_executed = False

        # Helper to process single tool
        def handle_tool(tool_name, tool_data, executor_func):
            nonlocal action_executed
            if action_executed: return None # One execution at a time

            # Determine commands/code for display
            display_cmd = ""
            if tool_name == "python_shell":
                display_cmd = "\n".join(tool_data.get("code", []))
            elif tool_name == "run_powershell":
                display_cmd = "\n".join(tool_data.get("commands", []))
            elif tool_name == "search_internet":
                display_cmd = ", ".join(tool_data.get("queries", []))

            ui.print_tool_start(tool_name, display_cmd)
            
            # Execute
            results = executor_func(response if tool_name != "python_shell" else {"python_shell": tool_data})
            
            # Process outputs
            mode = tool_data.get("output_mode", "AUTO")
            processed = []
            
            if tool_name == "python_shell":
                processed = [
                    output_processor.package_tool_result("python_shell", display_cmd, item, mode).get("result")
                    for item in results
                ]
            elif tool_name == "run_powershell":
                processed = [
                    output_processor.package_tool_result("run_powershell", cmd, item, mode).get("result")
                    for cmd, item in zip(tool_data.get("commands", []), results)
                ]
            elif tool_name == "search_internet":
                processed = [output_processor.process(command=display_cmd, output=results, mode=mode).as_dict()]

            output_text = json.dumps(processed, indent=2, ensure_ascii=False)
            ui.print_tool_output(tool_name, output_text)
            
            # Check for errors
            has_error = any(isinstance(r, dict) and r.get("status") == "error" for r in processed)
            if has_error:
                state.last_failed = True
            else:
                state.last_failed = False

            if tool_name in ["python_shell", "run_powershell"]:
                action_executed = True # Gated
            
            return processed

        # 1. Search Internet (Always first if present)
        if "search_internet" in response:
            from runner.search_internet import search_internet
            res = handle_tool("search_internet", response["search_internet"], search_internet)
            if res: all_outputs.extend(res)

        # 2. Shell Execution
        if "python_shell" in response and not action_executed:
            res = handle_tool("python_shell", response["python_shell"], python_shell.run_from_json)
            if res: all_outputs.extend(res)

        if "run_powershell" in response and not action_executed:
            from runner.powershell_shell import run_powershell
            res = handle_tool("run_powershell", response["run_powershell"], run_powershell)
            if res: all_outputs.extend(res)

        # 3. Actions array (Legacy support but still gated)
        if "actions" in response and not action_executed:
            for action in response["actions"]:
                if action_executed: break
                if "python_shell" in action:
                    res = handle_tool("python_shell", action["python_shell"], python_shell.run_from_json)
                    if res: all_outputs.extend(res)
                # ... other tools in actions if needed ...

        # 4. Reset shell
        if "reset_python_shell" in response:
            outputs = python_shell.reset()
            ui.print_tool_start("reset_python_shell", "")
            processed = output_processor.process(command="reset_python_shell", output=outputs, mode="SUMMARY").as_dict()
            ui.print_tool_output("reset_python_shell", json.dumps(processed))
            all_outputs.append(processed)

        if all_outputs:
            input_text = "SYSTEM EXECUTION RESULT:\n" + json.dumps(all_outputs, indent=2, ensure_ascii=False)
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
