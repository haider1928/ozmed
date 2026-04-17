from powershell_shell import run_powershell
output = run_powershell({"run_powershell":{"commands":["playwright install"]}})
print(output)