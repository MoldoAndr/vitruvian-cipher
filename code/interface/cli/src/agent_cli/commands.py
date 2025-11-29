"""
Command parser and handler for the CLI.
Handles all /commands and dispatches to appropriate handlers.
"""

from typing import Tuple, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum, auto


class CommandType(Enum):
    """Types of commands."""
    HELP = auto()
    AGENT = auto()
    STATUS = auto()
    CONFIG = auto()
    HISTORY = auto()
    CLEAR = auto()
    RESET = auto()
    MODE = auto()
    COMPONENTS = auto()
    QUIT = auto()
    TYPE = auto()
    NEWCHAT = auto()
    UNKNOWN = auto()
    INPUT = auto()  # Regular input, not a command


@dataclass
class ParsedCommand:
    """Parsed command result."""
    type: CommandType
    args: List[str]
    raw: str


# Command aliases
COMMAND_ALIASES = {
    # Help
    "/help": CommandType.HELP,
    "/h": CommandType.HELP,
    "/?": CommandType.HELP,
    
    # Agent
    "/agent": CommandType.AGENT,
    "/a": CommandType.AGENT,
    "/switch": CommandType.AGENT,
    
    # Status
    "/status": CommandType.STATUS,
    "/s": CommandType.STATUS,
    "/health": CommandType.STATUS,
    
    # Config
    "/config": CommandType.CONFIG,
    "/cfg": CommandType.CONFIG,
    "/settings": CommandType.CONFIG,
    
    # History
    "/history": CommandType.HISTORY,
    "/hist": CommandType.HISTORY,
    
    # Clear
    "/clear": CommandType.CLEAR,
    "/cls": CommandType.CLEAR,
    
    # Reset
    "/reset": CommandType.RESET,
    "/restart": CommandType.RESET,
    
    # Mode
    "/mode": CommandType.MODE,
    "/m": CommandType.MODE,
    
    # Components
    "/components": CommandType.COMPONENTS,
    "/comp": CommandType.COMPONENTS,
    "/c": CommandType.COMPONENTS,
    
    # Document type
    "/type": CommandType.TYPE,
    "/t": CommandType.TYPE,
    
    # New chat
    "/newchat": CommandType.NEWCHAT,
    "/new": CommandType.NEWCHAT,
    
    # Quit
    "/quit": CommandType.QUIT,
    "/q": CommandType.QUIT,
    "/exit": CommandType.QUIT,
    "/bye": CommandType.QUIT,
}


def parse_input(user_input: str) -> ParsedCommand:
    """Parse user input into a command."""
    stripped = user_input.strip()
    
    if not stripped:
        return ParsedCommand(type=CommandType.INPUT, args=[], raw=stripped)
    
    # Check if it's a command
    if stripped.startswith("/"):
        parts = stripped.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1].split() if len(parts) > 1 else []
        
        command_type = COMMAND_ALIASES.get(command, CommandType.UNKNOWN)
        return ParsedCommand(type=command_type, args=args, raw=stripped)
    
    # Regular input
    return ParsedCommand(type=CommandType.INPUT, args=[], raw=stripped)


def get_command_help() -> str:
    """Get help text for all commands."""
    help_lines = [
        "Available Commands:",
        "",
        "General:",
        "  /help, /h        Show this help message",
        "  /status, /s      Check service health",
        "  /config          Show configuration",
        "  /clear           Clear screen",
        "  /quit, /q        Exit CLI",
        "",
        "Navigation:",
        "  /agent <name>    Switch agent (password, crypto, choice, document)",
        "  /reset           Reset current session",
        "  /history         Show conversation history",
        "",
        "Agent-specific:",
        "  /components      Password: manage analysis components",
        "  /mode            Choice: set extraction mode",
        "  /type            Document: set document type",
        "  /newchat         Crypto: start new conversation",
    ]
    return "\n".join(help_lines)
