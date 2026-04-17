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

        # 🔥 join all lines into ONE script
        code_block = "\n".join(code_lines)

        try:
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            exec(code_block, self.env)  # execute full block

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