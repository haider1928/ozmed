from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.theme import Theme
from rich.text import Text
from rich.live import Live

custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "ai": "green",
        "system": "magenta",
        "python": "blue",
        "success": "bold green",
    }
)

console = Console(theme=custom_theme)


class UI:
    def __init__(self):
        self.live = None

    def print_user(self, text):
        console.print(f"[cyan]You:[/cyan] {text}")

    def print_ai(self, text):
        panel = Panel(Text(text, style="ai"), title="[bold green]Ozmed AI", expand=False)
        console.print(panel)

    def print_tool_start(self, tool_name, command_or_code):
        color = "blue" if tool_name == "python_shell" else "yellow"
        label = "Running Python" if tool_name == "python_shell" else (
            "Running Command" if tool_name == "run_powershell" else f"Executing {tool_name}"
        )
        console.print(f"[{color}]! {label}...[/{color}]")
        if command_or_code:
            console.print(Panel(Text(command_or_code, style=f"dim {color}"), expand=False))

    def print_tool_output(self, tool_name, text):
        color = "blue" if tool_name == "python_shell" else "yellow"
        console.print(f"[{color}]Result:[/{color}]")
        console.print(text, style="dim white")

    def print_error(self, text):
        console.print(f"[error]x {text}[/error]")

    def print_warning(self, text):
        console.print(f"[warning]! {text}[/warning]")

    def print_success(self, text):
        console.print(f"[success]v {text}[/success]")

    def print_status(self, text):
        console.print(f"[dim white]i {text}[/dim white]")

    def start_thinking(self, message="Thinking..."):
        if self.live is None:
            spinner = Spinner("dots", text=f"[cyan]{message}")
            self.live = Live(spinner, refresh_per_second=10, console=console)
            self.live.start()

    def update_thinking(self, message):
        if self.live:
            spinner = Spinner("dots", text=f"[cyan]{message}")
            self.live.update(spinner)

    def stop_thinking(self):
        if self.live:
            self.live.stop()
            self.live = None

    def print_thinking(self, thinking):
        intent = thinking.get("intent", "Unknown")
        search_needed = thinking.get("search_needed", False)
        search_reason = thinking.get("search_reason", "")
        plan = thinking.get("plan", [])
        shell = thinking.get("shell_choice", "None")
        
        content = f"[bold cyan]Intent:[/bold cyan] {intent}\n"
        content += f"[bold cyan]Shell:[/bold cyan] {shell}\n"
        content += f"[bold cyan]Search:[/bold cyan] {'[green]Yes[/green]' if search_needed else '[red]No[/red]'}\n"
        if search_reason:
            content += f"[dim cyan]Reason:[/dim cyan] {search_reason}\n"
        
        if plan:
            content += "[bold cyan]Plan:[/bold cyan]\n"
            for step in plan:
                content += f"  [dim]- {step}[/dim]\n"

        panel = Panel(
            content.strip(),
            title="[bold magenta]OZMED Thinking",
            border_style="magenta",
            expand=False
        )
        console.print(panel)

    def print_improvement_report(self, report):
        issues = report.get("issues", [])
        if not issues:
            return
            
        content = ""
        for issue in issues:
            severity = issue.get("severity", "medium").upper()
            sev_color = "red" if "CRITICAL" in severity or "HIGH" in severity else ("yellow" if "MEDIUM" in severity else "blue")
            
            category = issue.get("category", "general").upper()
            desc = issue.get("description", "")
            fix = issue.get("fix", "")
            
            content += f"[{sev_color}][{severity}] [/{sev_color}] [bold white]{category}[/bold white]\n"
            content += f"  [dim]{desc}[/dim]\n"
            if fix:
                content += f"  [green]Fix:[/green] {fix}\n"
            content += "\n"
            
        panel = Panel(
            content.strip(),
            title="[bold yellow]OZMED-DEV Improvement Report",
            border_style="yellow",
            expand=False
        )
        console.print(panel)


ui = UI()
