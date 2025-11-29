"""
Tab completion and auto-suggestions for the CLI.
Provides intelligent completions for commands and arguments.
"""

from prompt_toolkit.completion import Completer, Completion
from typing import Iterable, List

from .agents import AGENTS
from .config import PASSWORD_COMPONENTS, CHOICE_MODES, DOCUMENT_TYPES


class AgentCLICompleter(Completer):
    """Custom completer for Agent CLI commands."""
    
    def __init__(self, cli_instance=None):
        self.cli = cli_instance
        
        # Base commands
        self.commands = {
            "/help": "Show help message",
            "/h": "Show help (alias)",
            "/agent": "Switch to an agent",
            "/status": "Check service status",
            "/s": "Status (alias)",
            "/config": "Show configuration",
            "/history": "Show conversation history",
            "/clear": "Clear screen",
            "/reset": "Reset session",
            "/quit": "Exit CLI",
            "/q": "Quit (alias)",
            "/exit": "Exit CLI",
            "/mode": "Set agent mode",
            "/components": "Manage components",
            "/type": "Set document type",
            "/newchat": "Start new conversation",
        }
        
        # Agent names for /agent command
        self.agent_names = list(AGENTS.keys())
        
        # Component IDs for /components command
        self.component_ids = list(PASSWORD_COMPONENTS.keys())
        
        # Modes for /mode command
        self.mode_names = list(CHOICE_MODES.keys())
        
        # Document types for /type command
        self.type_names = list(DOCUMENT_TYPES.keys())
    
    def get_completions(self, document, complete_event) -> Iterable[Completion]:
        """Generate completions for the current input."""
        text = document.text_before_cursor.lstrip()
        
        # Empty or starting with /
        if not text or text.startswith("/"):
            # Complete commands
            for cmd, desc in self.commands.items():
                if cmd.startswith(text):
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display_meta=desc
                    )
        
        # Check for specific command completions
        parts = text.split()
        if len(parts) >= 1:
            cmd = parts[0].lower()
            
            # /agent completion
            if cmd in ("/agent", "/a", "/switch"):
                prefix = parts[1] if len(parts) > 1 else ""
                for agent in self.agent_names:
                    if agent.startswith(prefix):
                        yield Completion(
                            agent,
                            start_position=-len(prefix) if prefix else 0,
                            display_meta=f"Switch to {agent} agent"
                        )
            
            # /components completion
            elif cmd in ("/components", "/comp", "/c"):
                if len(parts) == 1:
                    yield Completion(
                        "toggle",
                        start_position=0,
                        display_meta="Toggle a component on/off"
                    )
                elif len(parts) >= 2 and parts[1] == "toggle":
                    prefix = parts[2] if len(parts) > 2 else ""
                    for comp_id in self.component_ids:
                        if comp_id.startswith(prefix):
                            name = PASSWORD_COMPONENTS[comp_id]["name"]
                            yield Completion(
                                comp_id,
                                start_position=-len(prefix) if prefix else 0,
                                display_meta=name
                            )
            
            # /mode completion
            elif cmd in ("/mode", "/m"):
                prefix = parts[1] if len(parts) > 1 else ""
                for mode in self.mode_names:
                    if mode.startswith(prefix):
                        yield Completion(
                            mode,
                            start_position=-len(prefix) if prefix else 0,
                            display_meta=CHOICE_MODES[mode]
                        )
            
            # /type completion
            elif cmd in ("/type", "/t"):
                prefix = parts[1] if len(parts) > 1 else ""
                for dtype in self.type_names:
                    if dtype.startswith(prefix):
                        yield Completion(
                            dtype,
                            start_position=-len(prefix) if prefix else 0,
                            display_meta=DOCUMENT_TYPES[dtype]
                        )


def create_completer(cli_instance=None) -> AgentCLICompleter:
    """Create a completer instance."""
    return AgentCLICompleter(cli_instance)
