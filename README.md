# OzMed AI

OzMed AI is a terminal-based system management assistant powered by large-scale language models accessed through broker APIs. It is designed to combine AI reasoning with direct system interaction, enabling automation, scripting, and workflow management from a single interface.

---

## Overview

OzMed AI connects to high-parameter AI models (100B+ class) and extends them with real execution capabilities. It is built for developers, security engineers, and advanced users who want an AI that does more than generate text.

The system focuses on:
- Automating repetitive tasks
- Managing local environments
- Executing scripts intelligently
- Maintaining structured memory
- Operating entirely from the command line

---

## Features

### AI Integration
- Access to large-scale models via broker APIs
- Context-aware responses and task handling
- Extensible for multiple providers

### System Execution
- Execute PowerShell commands
- Run Python scripts dynamically
- Perform controlled system-level operations

### Internet Access
- Fetch real-time information
- Perform web searches
- Summarize and process external data

### Persistent Memory
- Stores context in JSON format
- Maintains task history and system state
- Lightweight and easy to extend

### Modular Tooling
- Tool-based architecture
- Built-in tools:
  - Python execution
  - PowerShell execution
  - Web search
- Supports custom tool extensions

### CLI Interface
- Fully terminal-based
- Argparse-powered command handling
- Scriptable and automation-friendly

---

## Installation

git clone https://github.com/yourusername/ozmed-ai.git  
cd ozmed-ai  
pip install -r requirements.txt  

---

## Usage

### Interactive Mode

python main.py  

### CLI Mode

python main.py --task "Scan system and clean temp files"  

### Examples

# Run a Python script
python main.py --run-python script.py  

# Execute a PowerShell command
python main.py --powershell "Get-Process"  

# Perform a web search
python main.py --search "latest cybersecurity vulnerabilities"  

---

## Architecture

OzMed AI

Core Engine
- AI broker integration
- Prompt processing
- Task planning

Tools Layer
- Python executor
- PowerShell runner
- Web search module
- Custom tools

Memory System
- JSON-based context storage

Interface
- CLI (argparse)

---

## Memory Format

Example structure:

{
  "tasks": [],
  "history": [],
  "system_state": {}
}

---

## Security Considerations

OzMed AI can execute system-level commands. Use carefully.

- Avoid running untrusted inputs
- Prefer sandboxed environments
- Limit permissions where possible

Future improvements may include:
- Permission control layers
- Sandboxed execution
- Command validation

---

## Roadmap

- GUI interface
- Plugin system
- Secure execution environment
- Voice command support
- Multi-agent workflows
- Advanced memory indexing

---

## Contributing

Fork the repository and create a feature branch:

git checkout -b feature/new-feature  

Commit and push changes:

git commit -m "Add new feature"  
git push origin feature/new-feature  

Open a pull request.

---

## License

MIT License

---

## Philosophy

AI should not only generate responses, but also execute tasks and interact with real systems.