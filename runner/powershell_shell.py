import subprocess

def run_powershell(action_json:dict):
    outputs = []

    if "run_powershell" not in action_json:
        return ["No run_powershell action found"]

    commands = action_json["run_powershell"].get("commands", [])
    mode = action_json["run_powershell"].get("output_mode", "AUTO")

    for cmd in commands:
        try:
            # run PowerShell command
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                text=True
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            outputs.append({
                "command": cmd,
                "status": "error" if result.returncode != 0 or stderr else "ok",
                "mode_used": mode if mode != "AUTO" else ("FULL" if len(stdout) <= 1200 else "TAIL"),
                "summary": "Command completed." if not stderr else "Command returned an error.",
                "extracted_output": stdout[-1200:] if stdout else "",
                "errors": [stderr] if stderr else [],
            })

        except Exception as e:
            outputs.append({
                "command": cmd,
                "status": "error",
                "mode_used": "AUTO",
                "summary": "Command execution failed.",
                "extracted_output": "",
                "errors": [str(e)],
            })

    return outputs
