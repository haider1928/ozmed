import io
import sys
import traceback

class PythonShell:
    def __init__(self):
        self.env = {}  # persistent runtime

    def run_from_json(self, action_json: dict):
        outputs = []

        if "python_shell" not in action_json:
            return [{
                "command": "",
                "status": "error",
                "mode_used": "AUTO",
                "summary": "No python_shell action found.",
                "extracted_output": "",
                "errors": ["No python_shell action found"],
            }]

        code_lines = action_json["python_shell"].get("code", [])
        mode = action_json["python_shell"].get("output_mode", "AUTO")

        # 🔥 join all lines into ONE script
        code_block = "\n".join(code_lines)

        try:
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            exec(code_block, self.env)  # execute full block

            output = sys.stdout.getvalue().strip()
            outputs.append({
                "command": code_block,
                "status": "ok",
                "mode_used": mode if mode != "AUTO" else ("FULL" if len(output) <= 1200 else "TAIL"),
                "summary": "Python script completed." if output else "Python script completed with no stdout.",
                "extracted_output": output,
                "errors": [],
            })

        except Exception as e:
            error_text = str(e)
            friendly_error = f"Python script failed: {error_text}"

            if "unterminated string literal" in error_text or "SyntaxError" in type(e).__name__:
                friendly_error += (
                    " | Hint: Windows paths need escaped backslashes like 'C:\\\\' "
                    "or raw strings like r'C:\\'."
                )

            outputs.append({
                "command": code_block,
                "status": "error",
                "mode_used": mode,
                "summary": "Python script failed.",
                "extracted_output": "",
                "errors": [friendly_error, traceback.format_exc()],
            })

        finally:
            sys.stdout = old_stdout

        return outputs

    def reset(self):
        self.env.clear()
        return ["shell reset"]
if __name__ == "__main__":
    shell = PythonShell()

    test = {
        "python_shell": {
            "code": [
                "x = 5",
                "y = 10"
            ]
        }
    }
    test1 = {
        "python_shell": {
            "code": [
                
                "print(x + y)"
            ]
        }
    }


    print(shell.run_from_json(test))  # expect ['15']
    print(shell.run_from_json(test1))  # expect ['15']
