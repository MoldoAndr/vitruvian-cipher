"""
Main CLI application.
Entry point for the Agent CLI interface.
"""

import asyncio
import sys
import os
import time
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.text import Text

from .config import config, AGENT_MODES, SERVICE_NAMES
from .ui import (
    console,
    print_banner,
    print_welcome,
    print_help,
    print_status_table,
    print_agent_switch,
    print_error,
    print_info,
    print_success,
    print_config,
    clear_screen,
    create_spinner,
    run_intro_sequence,
    COLORS
)
from .commands import parse_input, CommandType
from .agents import create_agent, BaseAgent, AGENTS
from .api import api_client
from .completions import create_completer


# Prompt style
PROMPT_STYLE = Style.from_dict({
    'prompt': '#00ff88 bold',
    'agent': '#666666',
    'bottom-toolbar': 'bg:#1a1a1a #666666',
})


class AgentCLI:
    """Main CLI application class."""
    
    def __init__(self):
        self.running = False
        self.current_agent: Optional[BaseAgent] = None
        self.current_agent_name: Optional[str] = None  # Start with no agent selected
        self.last_interrupt_time: float = 0  # For double Ctrl+C detection
        
        # Set up history file
        history_dir = os.path.expanduser("~/.agent-cli")
        os.makedirs(history_dir, exist_ok=True)
        history_file = os.path.join(history_dir, "history")
        
        # Set up prompt session with completer
        self.completer = create_completer(self)
        self.session = PromptSession(
            history=FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory(),
            style=PROMPT_STYLE,
            enable_history_search=True,
            completer=self.completer,
            complete_while_typing=False,
        )
        
        # Key bindings
        self.kb = KeyBindings()
        
        @self.kb.add('c-c')
        def _(event):
            """Handle Ctrl+C."""
            event.app.exit(result='')
        
        @self.kb.add('c-d')
        def _(event):
            """Handle Ctrl+D - exit gracefully."""
            event.app.exit(result=None)
    
    def get_prompt(self) -> HTML:
        """Get the formatted prompt."""
        if self.current_agent_name is None:
            return HTML('<agent>[No Agent]</agent> <prompt>► </prompt>')
        
        agent_info = AGENT_MODES.get(self.current_agent_name, {})
        icon = agent_info.get("icon", "►")
        name = agent_info.get("name", "Agent")
        
        return HTML(f'<agent>[{name}]</agent> <prompt>{icon} </prompt>')
    
    def get_toolbar(self) -> HTML:
        """Get the bottom toolbar content."""
        if self.current_agent_name is None:
            agent_name = "None (use /agent to select)"
            exit_hint = "<b>Ctrl+C×2</b> exit"
        else:
            agent_info = AGENT_MODES.get(self.current_agent_name, {})
            agent_name = agent_info.get("name", "Agent")
            exit_hint = "<b>Ctrl+C</b> exit agent"
        
        # Build toolbar parts
        parts = [
            f"<b>Agent:</b> {agent_name}",
            "<b>/help</b> commands",
            "<b>Tab</b> complete",
            exit_hint
        ]
        
        return HTML(" │ ".join(parts))
    
    async def switch_agent(self, agent_name: str) -> bool:
        """Switch to a different agent."""
        if agent_name not in AGENTS:
            print_error(f"Unknown agent: {agent_name}")
            console.print(f"[{COLORS['muted']}]Available agents: {', '.join(AGENTS.keys())}[/]")
            return False
        
        self.current_agent_name = agent_name
        self.current_agent = create_agent(agent_name)
        
        agent_info = AGENT_MODES.get(agent_name, {
            "name": agent_name.title(),
            "description": "Agent",
            "icon": "►"
        })
        print_agent_switch(agent_name, agent_info)
        return True
    
    async def check_status(self) -> None:
        """Check and display service status."""
        with create_spinner("Checking service status..."):
            statuses = await api_client.check_all_health()
        print_status_table(statuses)
    
    async def show_config(self) -> None:
        """Show current configuration."""
        config_data = {
            "Current Agent": self.current_agent_name or "None",
            "Password Checker URL": config.password_checker.base_url,
            "Theory Specialist URL": config.theory_specialist.base_url,
            "Choice Maker URL": config.choice_maker.base_url,
        }
        
        if self.current_agent:
            for key, value in self.current_agent.session.settings.items():
                config_data[f"Agent: {key}"] = str(value)
        
        print_config(config_data)
    
    async def show_history(self) -> None:
        """Show conversation history."""
        if not self.current_agent or not self.current_agent.session.history:
            print_info("No conversation history")
            return
        
        console.print(f"\n[bold {COLORS['neon']}]Conversation History[/]\n")
        for i, entry in enumerate(self.current_agent.session.history, 1):
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            
            if role == "user":
                console.print(f"  [{COLORS['info']}][{i}] You:[/] {content}")
            elif role == "system":
                if isinstance(content, dict):
                    console.print(f"  [{COLORS['neon']}][{i}] Agent:[/] [dim](structured response)[/]")
                else:
                    # Truncate long responses
                    display = content[:100] + "..." if len(str(content)) > 100 else content
                    console.print(f"  [{COLORS['neon']}][{i}] Agent:[/] {display}")
            elif role == "error":
                console.print(f"  [{COLORS['error']}][{i}] Error:[/] {content}")
        console.print()
    
    async def handle_command(self, cmd) -> bool:
        """
        Handle a parsed command.
        Returns False if should quit, True otherwise.
        """
        if cmd.type == CommandType.QUIT:
            return False
        
        elif cmd.type == CommandType.HELP:
            print_help()
        
        elif cmd.type == CommandType.AGENT:
            if cmd.args:
                await self.switch_agent(cmd.args[0].lower())
            else:
                console.print(f"[{COLORS['muted']}]Usage: /agent <name>[/]")
                console.print(f"[{COLORS['muted']}]Available: {', '.join(AGENTS.keys())}[/]")
                console.print()
        
        elif cmd.type == CommandType.STATUS:
            await self.check_status()
        
        elif cmd.type == CommandType.CONFIG:
            await self.show_config()
        
        elif cmd.type == CommandType.HISTORY:
            await self.show_history()
        
        elif cmd.type == CommandType.CLEAR:
            clear_screen()
            print_banner()
        
        elif cmd.type == CommandType.RESET:
            if self.current_agent:
                self.current_agent.reset()
                print_success("Session reset")
            else:
                print_info("No active session")
        
        elif cmd.type == CommandType.UNKNOWN:
            print_error(f"Unknown command: {cmd.raw}")
            console.print(f"[{COLORS['muted']}]Type /help for available commands[/]")
            console.print()
        
        # Agent-specific commands
        elif cmd.type in (CommandType.MODE, CommandType.COMPONENTS, CommandType.TYPE, CommandType.NEWCHAT):
            if self.current_agent:
                # Map command type to command string
                cmd_map = {
                    CommandType.MODE: "mode",
                    CommandType.COMPONENTS: "components",
                    CommandType.TYPE: "type",
                    CommandType.NEWCHAT: "newchat",
                }
                cmd_str = cmd_map.get(cmd.type, "")
                if not self.current_agent.handle_command(cmd_str, cmd.args):
                    print_error(f"Command /{cmd_str} not available for this agent")
            else:
                print_error("No agent selected")
        
        elif cmd.type == CommandType.INPUT:
            if cmd.raw and self.current_agent:
                await self.current_agent.process(cmd.raw)
            elif cmd.raw:
                print_error("No agent selected. Use /agent <name> to select one.")
        
        return True
    
    async def run(self) -> None:
        """Run the main CLI loop."""
        self.running = True
        
        # Run the godlevel intro sequence
        run_intro_sequence()
        
        # Show normal startup after intro
        print_banner()
        print_welcome()
        
        # No default agent - user must select one
        console.print(f"[{COLORS['muted']}]Select an agent with /agent <name> to get started[/]")
        console.print()
        
        # Main loop
        while self.running:
            try:
                # Get user input
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.session.prompt(
                        self.get_prompt(),
                        key_bindings=self.kb,
                        bottom_toolbar=self.get_toolbar,
                    )
                )
                
                # Ctrl+D returns None - exit gracefully
                if user_input is None:
                    self.running = False
                    continue
                
                # Empty input - just continue
                if user_input == '':
                    continue
                
                # Parse and handle command
                cmd = parse_input(user_input)
                should_continue = await self.handle_command(cmd)
                
                if not should_continue:
                    self.running = False
                
            except KeyboardInterrupt:
                current_time = time.time()
                
                # If we have an agent selected, first Ctrl+C exits the agent
                if self.current_agent_name is not None:
                    self.current_agent_name = None
                    self.current_agent = None
                    console.print(f"\n[{COLORS['info']}]Exited agent. Select another with /agent <name>[/]")
                    self.last_interrupt_time = current_time
                    continue
                
                # No agent selected - check for double Ctrl+C to exit
                if current_time - self.last_interrupt_time < 1.5:
                    self.running = False
                    console.print()
                else:
                    self.last_interrupt_time = current_time
                    console.print(f"\n[{COLORS['warning']}]Press Ctrl+C again to exit[/]")
                continue
            
            except EOFError:
                self.running = False
            
            except Exception as e:
                print_error(str(e), "Unexpected Error")
        
        # Cleanup
        await api_client.close()
        console.print(f"\n[{COLORS['neon']}]Goodbye! 👋[/]\n")


def main():
    """Entry point for the CLI."""
    cli = AgentCLI()
    
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        console.print(f"\n[{COLORS['neon']}]Interrupted. Goodbye![/]\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
