import subprocess

def run_powershell(action_json):
    outputs = []

    if "run_powershell" not in action_json:
        return ["No run_powershell action found"]

    commands = action_json["run_powershell"].get("commands", [])

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

            if stdout:
                outputs.append(stdout)
            elif stderr:
                outputs.append(f"ERROR: {stderr}")
            else:
                outputs.append("OK")

        except Exception as e:
            outputs.append(f"ERROR: {str(e)}")

    return outputs