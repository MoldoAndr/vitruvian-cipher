"""
Rich UI components for Agent CLI.
Provides beautiful terminal output with colors, spinners, and formatted tables.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.box import ROUNDED, DOUBLE, MINIMAL, SIMPLE
from rich.align import Align
from rich.columns import Columns
from rich.live import Live
from rich.status import Status
from rich import box
from typing import Optional, List, Dict, Any
import asyncio
import os
import sys
import time
import random
import shutil

# Initialize console
console = Console()

# Color scheme matching React interface
COLORS = {
    "neon": "#13FF00",
    "neon_dim": "#003322",
    "error": "#ff4444",
    "warning": "#ffaa00",
    "info": "#4488ff",
    "muted": "#666666",
    "white": "#ffffff",
    "success": "#00ff88",
}

# ========== ANSI CONSTANTS FOR INTRO ==========
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
DARK_GREEN = "\033[32m"
BRIGHT_GREEN = "\033[38;5;46m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"


def get_terminal_size():
    """Get terminal dimensions."""
    try:
        columns, rows = os.get_terminal_size()
        return columns, rows
    except:
        return 80, 24


def center_multiline(text: str, width: int) -> str:
    """Center each line of a multiline string."""
    lines = text.split('\n')
    centered_lines = []
    for line in lines:
        line_len = len(line)
        if line_len < width:
            padding = (width - line_len) // 2
            centered_lines.append(' ' * padding + line)
        else:
            centered_lines.append(line)
    return '\n'.join(centered_lines)


# ========== INTRO SEQUENCE FUNCTIONS ==========
def clear_screen_raw():
    """Clear screen using system command."""
    os.system("cls" if os.name == "nt" else "clear")


def static_noise(width: int = 70, density: float = 0.10) -> str:
    """Generate static TV noise."""
    chars = [' ', '░', '▒', '▓', '█']
    return "".join(
        random.choice(chars) if random.random() < density else " "
        for _ in range(width)
    )


def glitchy_print(text: str, delay: float = 0.015):
    """Print text with glitch effect."""
    for ch in text:
        if ch != " " and random.random() < 0.06:
            sys.stdout.write(random.choice([" ", "░", "▒", ch.lower(), ch.upper()]))
        else:
            sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def boot_sequence():
    """Run the boot sequence with static and glitchy messages."""
    clear_screen_raw()
    cols, _ = get_terminal_size()
    width = min(cols - 2, 100)

    messages = [
        "[BOOT] Waking vitruvian-cipher neural lattice...",
        "[CORE] Locking rotational symmetry of keyspace...",
        "[RAG ] Splicing cryptographic corpus into memory...",
        "[LINK] Binding terminal to cipher daemon channel..."
    ]

    # STATIC TV NOISE
    for _ in range(12):
        print(DIM + GREEN + static_noise(width) + RESET)
        time.sleep(0.035)

    time.sleep(0.15)

    # GLITCHED STATUS LINES
    print()
    for msg in messages:
        sys.stdout.write(BRIGHT_GREEN)
        glitchy_print(msg)
        sys.stdout.write(RESET)
        time.sleep(0.12)

    time.sleep(0.4)


def matrix_rain(duration: float = 5.0, speed: float = 0.03):
    """Run matrix rain animation."""
    clear_screen_raw()
    cols, rows = get_terminal_size()
    cols = max(60, cols)
    rows = max(20, rows)

    rain_chars = list("01{}[]<>|/=+*#&$")
    num_cols = cols // 2
    drops = [random.randint(-rows, 0) for _ in range(num_cols)]

    start = time.time()
    while time.time() - start < duration:
        lines = []
        for row in range(rows):
            line_parts = []
            for i in range(num_cols):
                head = drops[i]

                if row == head:
                    ch = random.choice(rain_chars)
                    style = BRIGHT_GREEN + BOLD
                elif head - 3 <= row < head:
                    ch = random.choice(rain_chars)
                    style = GREEN
                elif head - 7 <= row < head - 3:
                    ch = random.choice(rain_chars)
                    style = DARK_GREEN + DIM
                else:
                    ch = " "
                    style = ""

                line_parts.append(style + ch + " " + RESET)
            lines.append("".join(line_parts))

        frame = "\n".join(lines)
        clear_screen_raw()
        sys.stdout.write(frame)

        # Occasionally inject a "shockwave" line
        if random.random() < 0.12:
            shock_row = random.randint(0, rows - 1)
            sys.stdout.write(
                "\033[%d;1H" % (shock_row + 1) +
                MAGENTA + DIM +
                ("-" * (cols // 2)) +
                RESET
            )

        sys.stdout.flush()

        for i in range(num_cols):
            drops[i] += 1 if random.random() < 0.9 else 0
            if drops[i] > rows + random.randint(3, 15):
                drops[i] = random.randint(-rows, -1)

        time.sleep(speed)


def corrupt_banner(text: str, corruption: float = 0.15) -> str:
    """Corrupt banner text with random glitch characters."""
    noise_chars = ["░", "▒", "▓", "█", "Ø", "Ψ", "Δ", "Ξ"]
    out_lines = []
    for line in text.splitlines():
        new_line = []
        for ch in line:
            if ch != " " and random.random() < corruption:
                new_line.append(random.choice(noise_chars))
            else:
                new_line.append(ch)
        out_lines.append("".join(new_line))
    return "\n".join(out_lines)


def pulse_banner_frames(banner: str, pulses: int = 5):
    """Pulse the banner with decreasing corruption."""
    for i in range(pulses):
        clear_screen_raw()
        corruption = max(0.02, 0.4 - i * 0.07)  # gradually stabilizes
        corrupted = corrupt_banner(banner, corruption=corruption)
        color = BRIGHT_GREEN if i % 2 == 0 else CYAN
        print(color + BOLD + corrupted + RESET)
        time.sleep(0.25)


def run_intro_sequence():
    """Run the full godlevel intro sequence, wait for Enter, then continue."""
    boot_sequence()
    matrix_rain(duration=6.0, speed=0.028)
    pulse_banner_frames(BANNER_LARGE, pulses=6)
    
    # Final clean banner before prompt
    clear_screen_raw()
    print(BRIGHT_GREEN + BOLD + BANNER_LARGE + RESET)
    print(
        DIM + CYAN +
        "   vitruvian-cipher • AI-augmented cryptographic operations console" +
        RESET
    )
    print(
        DIM + GREEN +
        "   commands: '/help' to list incantations • 'Ctrl+C' to exit agent" +
        RESET
    )
    print()
    
    # Wait for Enter
    input(BRIGHT_GREEN + ">>> press enter to awaken the agent... " + RESET)
    clear_screen_raw()


# Large banner for wide terminals (100+ cols)
BANNER_LARGE = r"""
▄▄ ▄▄   ▄▄░▒ ▄▄▄▄▄▄░▒ ▄▄▄▄░▒  ▄▄ ▄▄░▒ ▄▄ ▄▄░▒ ▄▄░▒  ▄▄▄░▒  ▄▄░▒▄▄░▒      ▄▄▄▄░▒ ▄▄░▒ ▄▄▄▄░▒  ▄▄ ▄▄░▒ ▄▄▄▄▄░▒ ▄▄▄▄░▒
██▄██   ██░▒   ██░▒   ██▄█▄░▒ ██ ██░▒ ██▄██░▒ ██░▒ ██▀██░▒ ███▄██░▒ ▄▄▄ ██▀▀▀░▒ ██░▒ ██▄█▀░▒ ██▄██░▒ ██▄▄░▒  ██▄█▄░▒
 ▀█▀░▒  ██░▒   ██░▒   ██ ██░▒ ▀███▀░▒  ▀█▀░▒  ██░▒ ██▀██░▒ ██ ▀██░▒     ▀████░▒ ██░▒ ██░▒    ██ ██░▒ ██▄▄▄░▒ ██ ██░▒
"""

# Medium banner for medium terminals (60-99 cols)
BANNER_MEDIUM = """
█ █ █ ▀█▀ █▀▄ █ █ █ █ █ █▀█ █▄ █   █▀▀ █ █▀▄ █ █ █▀▀ █▀▄
▀▄▀ █  █  █▀▄ █ █ ▀▄▀ █ █▀█ █ ▀█ ▄ █   █ █▀  █▀█ █▀▀ █▀▄
 ▀  █  █  █ █ ▀▀▀  ▀  █ █ █ █  █   ▀▀▀ █ █   █ █ ▀▀▀ █ █
"""

# Small banner for narrow terminals (<60 cols)
BANNER_SMALL = """
╔═══════════════════════════════╗
║   VITRUVIAN-CIPHER v2.0       ║
║   [ Cryptographic Agent ]     ║
╚═══════════════════════════════╝
"""

# Minimal banner for very narrow terminals (<40 cols)
BANNER_MINIMAL = """
┌─────────────────────┐
│  VITRUVIAN-CIPHER   │
│    [ 0xC1PH3R ]     │
└─────────────────────┘
"""


def print_banner():
    """Print the startup banner - responsive and centered."""
    term_width, term_height = get_terminal_size()
    
    # Select appropriate banner based on terminal width
    if term_width >= 100:
        banner = BANNER_LARGE
        subtitle = "▉▓▒░ CRYPTOGRAPHIC SECURITY ANALYSIS FRAMEWORK ░▒▓▉"
        tagline = "[ sys.init ] • Type /help for commands • [ 0xC1PH3R ]"
    elif term_width >= 60:
        banner = BANNER_MEDIUM
        subtitle = "░▒▓ CRYPTO SECURITY FRAMEWORK ▓▒░"
        tagline = "[ /help for commands ]"
    elif term_width >= 40:
        banner = BANNER_SMALL
        subtitle = None
        tagline = "Type /help for commands"
    else:
        banner = BANNER_MINIMAL
        subtitle = None
        tagline = "/help"
    
    # Center the banner
    centered_banner = center_multiline(banner.strip(), term_width)
    
    # Print with styling
    console.print()
    console.print(Text(centered_banner, style=f"bold {COLORS['neon']}"))
    console.print()
    
    if subtitle:
        console.print(Align.center(Text(subtitle, style="bold white")))
    
    console.print(Align.center(Text(tagline, style=COLORS['muted'])))
    console.print()


def print_welcome():
    """Print welcome message with available commands."""
    welcome_panel = Panel(
        Text.from_markup(
            "[bold white]Welcome to Agent CLI![/]\n\n"
            f"[{COLORS['neon']}]Available Agents:[/]\n"
            "  🔐 [white]/agent password[/]  - Analyze password security\n"
            "  🧠 [white]/agent crypto[/]    - Ask cryptography questions\n"
            "  🎯 [white]/agent choice[/]    - Extract intents & entities\n"
            "  📄 [white]/agent document[/]  - Ingest documents\n\n"
            f"[{COLORS['muted']}]Quick Start:[/]\n"
            "  Select an agent to begin, e.g. [bold]/agent password[/]\n"
            "  Type [bold]/status[/] to check service health\n"
            "  Type [bold]/help[/] for all commands\n"
            "  Press [bold]Ctrl+C twice[/] to exit"
        ),
        title=f"[bold {COLORS['neon']}]● Agent CLI[/]",
        border_style=COLORS['neon'],
        box=ROUNDED,
        padding=(1, 2)
    )
    console.print(welcome_panel)
    console.print()


def print_help():
    """Print help with all available commands."""
    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['neon']}",
        box=ROUNDED,
        border_style=COLORS['muted'],
        title="[bold white]Available Commands[/]",
        title_justify="left"
    )
    
    table.add_column("Command", style="bold white", width=25)
    table.add_column("Description", style="white")
    
    commands = [
        ("/help, /h", "Show this help message"),
        ("/agent <name>", "Switch to an agent (password, crypto, choice, document)"),
        ("/status, /s", "Check all service health status"),
        ("/config", "Show current configuration"),
        ("/history", "Show conversation history"),
        ("/clear", "Clear the screen"),
        ("/reset", "Reset current session"),
        ("/mode <mode>", "Set agent-specific mode"),
        ("/components", "List/toggle components (password agent)"),
        ("/quit, /q, /exit", "Exit the CLI"),
        ("", ""),
        ("[dim]<text>[/dim]", "[dim]Send input to current agent[/dim]"),
    ]
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
    
    console.print(table)
    console.print()


def print_status_table(statuses: Dict[str, Dict[str, Any]]):
    """Print service status table."""
    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['neon']}",
        box=ROUNDED,
        border_style=COLORS['muted'],
        title="[bold white]Service Status[/]"
    )
    
    table.add_column("Service", style="white", width=20)
    table.add_column("Status", justify="center", width=12)
    table.add_column("URL", style=COLORS['muted'], width=30)
    table.add_column("Latency", justify="right", width=10)
    
    for service, status in statuses.items():
        if status["online"]:
            status_text = Text("● ONLINE", style=f"bold {COLORS['success']}")
            latency = f"{status.get('latency', 0):.0f}ms"
        else:
            status_text = Text("● OFFLINE", style=f"bold {COLORS['error']}")
            latency = "-"
        
        table.add_row(
            status["name"],
            status_text,
            status["url"],
            latency
        )
    
    console.print(table)
    console.print()


def print_agent_switch(agent_name: str, agent_info: Dict):
    """Print agent switch confirmation."""
    panel = Panel(
        Text.from_markup(
            f"[bold white]{agent_info['name']}[/]\n"
            f"[{COLORS['muted']}]{agent_info['description']}[/]"
        ),
        title=f"[bold {COLORS['neon']}]{agent_info['icon']} Switched to Agent[/]",
        border_style=COLORS['neon'],
        box=ROUNDED,
        padding=(0, 2)
    )
    console.print(panel)
    console.print()


def print_password_result(result: Dict[str, Any]):
    """Print password analysis result."""
    score = result.get("normalized_score", 0)
    
    # Determine score color
    if score >= 80:
        score_color = COLORS['success']
        strength = "STRONG"
    elif score >= 60:
        score_color = "#88ff00"
        strength = "GOOD"
    elif score >= 40:
        score_color = COLORS['warning']
        strength = "MODERATE"
    else:
        score_color = COLORS['error']
        strength = "WEAK"
    
    # Score display
    score_text = Text()
    score_text.append(f"\n  {score}", style=f"bold {score_color}")
    score_text.append("/100  ", style=COLORS['muted'])
    score_text.append(strength, style=f"bold {score_color}")
    
    # Components table
    table = Table(box=SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Status", width=3)
    table.add_column("Component", width=20)
    table.add_column("Score", justify="right", width=10)
    
    for comp in result.get("components", []):
        if comp.get("success"):
            status = Text("✓", style=COLORS['success'])
        else:
            status = Text("✗", style=COLORS['error'])
        
        comp_score = comp.get("normalized_score", "N/A")
        if isinstance(comp_score, (int, float)):
            comp_score = f"{comp_score:.0f}"
        
        table.add_row(status, comp.get("label", "Unknown"), comp_score)
        
        if comp.get("error"):
            table.add_row("", Text(comp["error"], style=f"dim {COLORS['error']}"), "")
    
    panel = Panel(
        Columns([score_text, table], padding=2),
        title=f"[bold {COLORS['neon']}]🔐 Password Analysis Complete[/]",
        border_style=COLORS['neon'],
        box=ROUNDED,
        padding=(1, 2)
    )
    console.print(panel)
    console.print()


def print_crypto_response(response: str, sources: Optional[List[Dict]] = None):
    """Print cryptography expert response."""
    content = Text(response, style="white")
    
    panel = Panel(
        content,
        title=f"[bold {COLORS['neon']}]🧠 Crypto Expert[/]",
        border_style=COLORS['neon'],
        box=ROUNDED,
        padding=(1, 2)
    )
    console.print(panel)
    
    if sources:
        source_table = Table(box=MINIMAL, show_header=False, padding=(0, 1))
        source_table.add_column("Source", style=COLORS['neon'])
        source_table.add_column("Details", style=COLORS['muted'])
        
        for source in sources[:5]:  # Limit to 5 sources
            metadata = source.get("metadata", {})
            name = metadata.get("source", "Unknown")
            page = metadata.get("source_page", "")
            relevance = source.get("relevance_score", 0)
            
            details = ""
            if page:
                details += f"Page {page}"
            if relevance:
                details += f" • {relevance*100:.1f}%"
            
            source_table.add_row(f"• {name}", details)
        
        console.print(Panel(
            source_table,
            title="[dim]Sources[/]",
            border_style=COLORS['muted'],
            box=SIMPLE
        ))
    
    console.print()


def print_choice_result(result: Dict[str, Any]):
    """Print choice maker result."""
    content_parts = []
    
    # Intent section
    intent = result.get("intent")
    if intent:
        intent_data = intent.get("intent", intent)
        label = intent_data.get("label", "Unknown")
        score = intent_data.get("score", 0)
        
        content_parts.append(
            f"[bold {COLORS['neon']}]🎯 Intent[/]\n"
            f"   [bold white]{label}[/] "
            f"[{COLORS['muted']}]({score*100:.1f}% confidence)[/]\n"
        )
    
    # Entities section
    entities = result.get("entities")
    if entities:
        entity_list = entities.get("entities", {}).get("entities", [])
        if not entity_list:
            entity_list = entities.get("entities", [])
        
        if entity_list:
            content_parts.append(f"\n[bold {COLORS['neon']}]📦 Entities[/]")
            for entity in entity_list:
                content_parts.append(
                    f"\n   [{COLORS['info']}]{entity.get('entity', 'UNK')}[/]: "
                    f"[white]\"{entity.get('text', '')}\"[/] "
                    f"[{COLORS['muted']}]({entity.get('score', 0)*100:.1f}%)[/]"
                )
        else:
            content_parts.append(f"\n[{COLORS['muted']}]No entities detected[/]")
    
    panel = Panel(
        Text.from_markup("".join(content_parts)),
        title=f"[bold {COLORS['neon']}]🎯 Choice Analysis[/]",
        border_style=COLORS['neon'],
        box=ROUNDED,
        padding=(1, 2)
    )
    console.print(panel)
    console.print()


def print_document_result(success: bool, message: str, details: Optional[Dict] = None):
    """Print document ingestion result."""
    if success:
        icon = "✓"
        color = COLORS['success']
        title = "Document Ingested"
    else:
        icon = "✗"
        color = COLORS['error']
        title = "Ingestion Failed"
    
    content = f"[{color}]{icon}[/] {message}"
    
    if details:
        content += f"\n\n[{COLORS['muted']}]"
        for key, value in details.items():
            if key != "message":
                content += f"  {key}: {value}\n"
        content += "[/]"
    
    panel = Panel(
        Text.from_markup(content),
        title=f"[bold {color}]📄 {title}[/]",
        border_style=color,
        box=ROUNDED,
        padding=(0, 2)
    )
    console.print(panel)
    console.print()


def print_error(message: str, title: str = "Error"):
    """Print error message."""
    panel = Panel(
        Text(message, style=COLORS['error']),
        title=f"[bold {COLORS['error']}]✗ {title}[/]",
        border_style=COLORS['error'],
        box=ROUNDED,
        padding=(0, 2)
    )
    console.print(panel)
    console.print()


def print_info(message: str, title: str = "Info"):
    """Print info message."""
    panel = Panel(
        Text(message, style="white"),
        title=f"[bold {COLORS['info']}]ℹ {title}[/]",
        border_style=COLORS['info'],
        box=ROUNDED,
        padding=(0, 2)
    )
    console.print(panel)
    console.print()


def print_success(message: str, title: str = "Success"):
    """Print success message."""
    panel = Panel(
        Text(message, style="white"),
        title=f"[bold {COLORS['success']}]✓ {title}[/]",
        border_style=COLORS['success'],
        box=ROUNDED,
        padding=(0, 2)
    )
    console.print(panel)
    console.print()


def print_user_input(text: str, agent_icon: str = "►"):
    """Print user input in chat style."""
    console.print(f"[bold {COLORS['neon']}]{agent_icon}[/] [white]{text}[/]")
    console.print()


def print_components_table(components: Dict[str, Dict], selected: List[str]):
    """Print password components selection table."""
    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['neon']}",
        box=ROUNDED,
        border_style=COLORS['muted'],
        title="[bold white]Password Analysis Components[/]"
    )
    
    table.add_column("", width=3)
    table.add_column("ID", style="white", width=18)
    table.add_column("Name", style="white", width=15)
    table.add_column("Description", style=COLORS['muted'])
    
    for comp_id, comp_info in components.items():
        if comp_id in selected:
            check = Text("✓", style=COLORS['success'])
        else:
            check = Text("○", style=COLORS['muted'])
        
        table.add_row(
            check,
            comp_id,
            comp_info["name"],
            comp_info["description"]
        )
    
    console.print(table)
    console.print(f"[{COLORS['muted']}]Use /components toggle <id> to enable/disable[/]")
    console.print()


def print_mode_table(modes: Dict[str, str], current: str):
    """Print mode selection table."""
    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['neon']}",
        box=ROUNDED,
        border_style=COLORS['muted'],
        title="[bold white]Available Modes[/]"
    )
    
    table.add_column("", width=3)
    table.add_column("Mode", style="white", width=20)
    table.add_column("Description", style=COLORS['muted'])
    
    for mode_id, description in modes.items():
        if mode_id == current:
            check = Text("●", style=COLORS['success'])
            mode_style = f"bold {COLORS['neon']}"
        else:
            check = Text("○", style=COLORS['muted'])
            mode_style = "white"
        
        table.add_row(check, Text(mode_id, style=mode_style), description)
    
    console.print(table)
    console.print(f"[{COLORS['muted']}]Use /mode <mode_name> to switch[/]")
    console.print()


def print_config(config_data: Dict[str, Any]):
    """Print current configuration."""
    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['neon']}",
        box=ROUNDED,
        border_style=COLORS['muted'],
        title="[bold white]Current Configuration[/]"
    )
    
    table.add_column("Setting", style="white", width=25)
    table.add_column("Value", style=COLORS['info'])
    
    for key, value in config_data.items():
        table.add_row(key, str(value))
    
    console.print(table)
    console.print()


def create_spinner(message: str = "Processing..."):
    """Create a spinner for async operations."""
    return console.status(f"[{COLORS['neon']}]{message}[/]", spinner="dots")


def clear_screen():
    """Clear the terminal screen."""
    console.clear()


# Export console for direct use
__all__ = [
    'console',
    'print_banner',
    'print_welcome',
    'print_help',
    'print_status_table',
    'print_agent_switch',
    'print_password_result',
    'print_crypto_response',
    'print_choice_result',
    'print_document_result',
    'print_error',
    'print_info',
    'print_success',
    'print_user_input',
    'print_components_table',
    'print_mode_table',
    'print_config',
    'create_spinner',
    'clear_screen',
    'COLORS'
]
