# Vitruvian Cipher CLI

A terminal-based interface for the Vitruvian Cipher cryptography and security analysis agents. Inspired by tools like Codex, Claude Code, and Gemini CLI.

```
    ╔═══════════════════════════════════════════════════════════════════╗
    ║     █████╗  ██████╗ ███████╗███╗   ██╗████████╗                   ║
    ║    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝                   ║
    ║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║                      ║
    ║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║                      ║
    ║    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║                      ║
    ║    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝                      ║
    ║              ██████╗██╗     ██╗    ██╗   ██╗██████╗               ║
    ║             ██║     ██║     ██║    ██║   ██║ █████╔╝              ║
    ║             ╚██████╗███████╗██║     ╚████╔╝ ███████╗              ║
    ╚═══════════════════════════════════════════════════════════════════╝
```

## Features

- **🔐 Password Analysis** - Analyze password strength using AI, zxcvbn, and breach detection
- **🧠 Cryptography Expert** - Ask questions about cryptographic algorithms and security
- **🎯 Choice Maker** - Extract intents and entities from natural language
- **📄 Document Ingestion** - Add documents to the knowledge base

## Installation

### From Source

```bash
cd interface/cli
pip install -e .
```

### Using pip

```bash
pip install "git+https://github.com/MoldoAndr/vitruvian-cipher@main#subdirectory=code/interface/cli"
```

## Usage

### Starting the CLI

```bash
# Using the installed command
vitruvian-cipher

# Or the legacy aliases
agent-cli
acli

# Or directly with Python
python -m agent_cli.main
```

### Commands

| Command | Description |
|---------|-------------|
| `/help`, `/h` | Show help message |
| `/agent <name>` | Switch agent (password, crypto, choice, document) |
| `/status`, `/s` | Check service health |
| `/config` | Show current configuration |
| `/history` | Show conversation history |
| `/clear` | Clear screen |
| `/reset` | Reset current session |
| `/quit`, `/q` | Exit CLI |

### Agent-Specific Commands

#### Password Agent
- `/components` - List analysis components
- `/components toggle <id>` - Enable/disable a component

#### Crypto Agent
- `/newchat` - Start a new conversation

#### Choice Agent
- `/mode` - Show available modes
- `/mode <mode>` - Set extraction mode (both, intent_extraction, entity_extraction)

#### Document Agent
- `/type` - Show document types
- `/type <type>` - Set document type (pdf, markdown, text)

## Examples

### Password Analysis

```
[Password Analysis] 🔐 MySecureP@ssw0rd!

╭─ 🔐 Password Analysis Complete ──────────────────────────╮
│                                                          │
│   85/100  STRONG                                         │
│                                                          │
│   ✓ AI Engine          87                                │
│   ✓ zxcvbn             83                                │
│   ✓ Breach Check       85                                │
│                                                          │
╰──────────────────────────────────────────────────────────╯
```

### Cryptography Questions

```
[Cryptography Expert] 🧠 What is AES encryption?

╭─ 🧠 Crypto Expert ───────────────────────────────────────╮
│                                                          │
│   AES (Advanced Encryption Standard) is a symmetric      │
│   block cipher algorithm that uses 128-bit blocks and    │
│   supports key sizes of 128, 192, and 256 bits...        │
│                                                          │
╰──────────────────────────────────────────────────────────╯
```

### Intent & Entity Extraction

```
[Choice Maker] 🎯 I want to check if password123 is secure

╭─ 🎯 Choice Analysis ─────────────────────────────────────╮
│                                                          │
│   🎯 Intent                                              │
│      password_check (92.5% confidence)                   │
│                                                          │
│   📦 Entities                                            │
│      PASSWORD: "password123" (89.2%)                     │
│                                                          │
╰──────────────────────────────────────────────────────────╯
```

## Configuration

The CLI can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PASSWORD_CHECKER_URL` | `http://localhost:9000` | Password checker service URL |
| `THEORY_SPECIALIST_URL` | `http://localhost:8100` | Theory specialist service URL |
| `CHOICE_MAKER_URL` | `http://localhost:8081` | Choice maker service URL |

## Architecture

```
src/agent_cli/
├── __init__.py      # Package initialization
├── main.py          # Main CLI application
├── config.py        # Configuration management
├── ui.py            # Rich terminal UI components
├── api.py           # HTTP API client
├── agents.py        # Agent implementations
└── commands.py      # Command parsing
```

## Requirements

- Python 3.10+
- Rich (terminal UI)
- Prompt Toolkit (input handling)
- httpx (async HTTP client)

## License

MIT License
