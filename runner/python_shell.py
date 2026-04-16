import io
import sys

class PythonShell:
    def __init__(self):
        self.env = {}  # persistent runtime

    def run_from_json(self, action_json: dict):
        outputs = []

        if "python_shell" not in action_json:
            return ["No python_shell action found"]

        code_lines = action_json["python_shell"].get("code", [])

        for line in code_lines:
            try:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()

                exec(line, self.env)  # persistent execution

                output = sys.stdout.getvalue().strip()
                outputs.append(output if output else "OK")

            except Exception as e:
                outputs.append(f"ERROR: {str(e)}")

            finally:
                sys.stdout = old_stdout

        return outputs

    def reset(self):
        self.env.clear()
        return ["shell reset"]