"""
Agent implementations for the CLI interface.
Each agent handles a specific domain of functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .api import api_client, APIResponse
from .config import PASSWORD_COMPONENTS, CHOICE_MODES, DOCUMENT_TYPES, EXECUTOR_OPERATIONS
from .ui import (
    console,
    print_password_result,
    print_crypto_response,
    print_choice_result,
    print_document_result,
    print_executor_result,
    print_error,
    print_info,
    print_components_table,
    print_mode_table,
    print_operations_table,
    print_pqc_health,
    create_spinner,
    COLORS
)


@dataclass
class AgentSession:
    """Holds session state for an agent."""
    history: List[Dict[str, Any]] = field(default_factory=list)
    conversation_id: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all agents."""
    
    name: str = "Base Agent"
    icon: str = "►"
    description: str = "Base agent"
    
    def __init__(self):
        self.session = AgentSession()
    
    @abstractmethod
    async def process(self, user_input: str) -> None:
        """Process user input."""
        pass
    
    def reset(self) -> None:
        """Reset agent session."""
        self.session = AgentSession()
    
    def get_prompt(self) -> str:
        """Get the input prompt for this agent."""
        return f"[bold {COLORS['neon']}]{self.icon}[/bold {COLORS['neon']}] "
    
    def handle_command(self, command: str, args: List[str]) -> bool:
        """
        Handle agent-specific commands.
        Returns True if command was handled, False otherwise.
        """
        return False


class PasswordAgent(BaseAgent):
    """Agent for password security analysis."""
    
    name = "Password Analysis"
    icon = "🔐"
    description = "Analyze password strength using multiple security engines"
    
    def __init__(self):
        super().__init__()
        self.session.settings["components"] = ["pass_strength_ai", "zxcvbn", "haveibeenpwned"]
    
    async def process(self, user_input: str) -> None:
        """Analyze a password."""
        if not user_input.strip():
            print_error("Please enter a password to analyze")
            return
        
        components = self.session.settings.get("components", [])
        if not components:
            print_error("No components selected. Use /components to enable analysis engines.")
            return
        
        # Store in history
        self.session.history.append({
            "role": "user",
            "content": f"[Password: {'*' * len(user_input)}]"
        })
        
        with create_spinner("Analyzing password security..."):
            response = await api_client.analyze_password(user_input, components)
        
        if response.success:
            print_password_result(response.data)
            self.session.history.append({
                "role": "system",
                "content": f"Score: {response.data.get('normalized_score', 0)}/100"
            })
        else:
            print_error(response.error, "Analysis Failed")
            self.session.history.append({
                "role": "error",
                "content": response.error
            })
    
    def handle_command(self, command: str, args: List[str]) -> bool:
        """Handle password agent specific commands."""
        if command == "components":
            if not args:
                # Show components
                print_components_table(
                    PASSWORD_COMPONENTS, 
                    self.session.settings.get("components", [])
                )
                return True
            
            if args[0] == "toggle" and len(args) > 1:
                comp_id = args[1]
                if comp_id in PASSWORD_COMPONENTS:
                    components = self.session.settings.get("components", [])
                    if comp_id in components:
                        components.remove(comp_id)
                        print_info(f"Disabled: {PASSWORD_COMPONENTS[comp_id]['name']}")
                    else:
                        components.append(comp_id)
                        print_info(f"Enabled: {PASSWORD_COMPONENTS[comp_id]['name']}")
                    self.session.settings["components"] = components
                else:
                    print_error(f"Unknown component: {comp_id}")
                return True
        
        return False


class CryptoAgent(BaseAgent):
    """Agent for cryptography questions."""
    
    name = "Cryptography Expert"
    icon = "🧠"
    description = "Ask questions about cryptographic algorithms and security"
    
    async def process(self, user_input: str) -> None:
        """Query the crypto expert."""
        if not user_input.strip():
            print_error("Please enter a question")
            return
        
        self.session.history.append({
            "role": "user",
            "content": user_input
        })
        
        with create_spinner("Thinking..."):
            response = await api_client.query_crypto_expert(
                user_input,
                self.session.conversation_id
            )
        
        if response.success:
            data = response.data
            self.session.conversation_id = data.get("conversation_id")
            
            answer = data.get("answer", "No response")
            sources = data.get("sources", [])
            
            print_crypto_response(answer, sources)
            self.session.history.append({
                "role": "system",
                "content": answer,
                "sources": sources
            })
        else:
            print_error(response.error, "Query Failed")
            self.session.history.append({
                "role": "error",
                "content": response.error
            })
    
    def handle_command(self, command: str, args: List[str]) -> bool:
        """Handle crypto agent specific commands."""
        if command == "newchat":
            self.session.conversation_id = None
            self.session.history = []
            print_info("Started new conversation")
            return True
        return False


class ChoiceAgent(BaseAgent):
    """Agent for intent and entity extraction."""
    
    name = "Choice Maker"
    icon = "🎯"
    description = "Extract intents and entities from text"
    
    def __init__(self):
        super().__init__()
        self.session.settings["mode"] = "both"
    
    async def process(self, user_input: str) -> None:
        """Extract intent and/or entities."""
        if not user_input.strip():
            print_error("Please enter text to analyze")
            return
        
        mode = self.session.settings.get("mode", "both")
        
        self.session.history.append({
            "role": "user",
            "content": user_input
        })
        
        with create_spinner("Analyzing text..."):
            if mode == "both":
                intent_resp, entity_resp = await api_client.extract_both(user_input)
                
                # Handle various response structures - check for 'result', 'intent', 'prediction', or direct data
                intent_data = None
                if intent_resp.success and intent_resp.data:
                    intent_data = (intent_resp.data.get("result") or 
                                   intent_resp.data.get("intent") or 
                                   intent_resp.data.get("prediction") or
                                   intent_resp.data)
                
                entities_data = None
                if entity_resp.success and entity_resp.data:
                    entities_data = (entity_resp.data.get("result") or 
                                     entity_resp.data.get("entities") or 
                                     entity_resp.data.get("prediction") or
                                     entity_resp.data)
                
                result = {
                    "intent": intent_data,
                    "entities": entities_data
                }
                success = intent_resp.success or entity_resp.success
                error = intent_resp.error or entity_resp.error if not success else None
            elif mode == "intent_extraction":
                response = await api_client.extract_intent(user_input)
                intent_data = None
                if response.success and response.data:
                    intent_data = (response.data.get("result") or 
                                   response.data.get("intent") or 
                                   response.data.get("prediction") or
                                   response.data)
                result = {
                    "intent": intent_data,
                    "entities": None
                }
                success = response.success
                error = response.error
            else:  # entity_extraction
                response = await api_client.extract_entities(user_input)
                entities_data = None
                if response.success and response.data:
                    entities_data = (response.data.get("result") or 
                                     response.data.get("entities") or 
                                     response.data.get("prediction") or
                                     response.data)
                result = {
                    "intent": None,
                    "entities": entities_data
                }
                success = response.success
                error = response.error
        
        if success:
            print_choice_result(result)
            self.session.history.append({
                "role": "system",
                "content": result
            })
        else:
            print_error(error, "Analysis Failed")
            self.session.history.append({
                "role": "error",
                "content": error
            })
    
    def handle_command(self, command: str, args: List[str]) -> bool:
        """Handle choice agent specific commands."""
        if command == "mode":
            if not args:
                print_mode_table(CHOICE_MODES, self.session.settings.get("mode", "both"))
                return True
            
            new_mode = args[0]
            if new_mode in CHOICE_MODES:
                self.session.settings["mode"] = new_mode
                print_info(f"Mode set to: {new_mode}")
            else:
                print_error(f"Invalid mode: {new_mode}")
                print_mode_table(CHOICE_MODES, self.session.settings.get("mode", "both"))
            return True
        
        return False


class DocumentAgent(BaseAgent):
    """Agent for document ingestion."""
    
    name = "Document Ingestion"
    icon = "📄"
    description = "Add documents to the knowledge base"
    
    def __init__(self):
        super().__init__()
        self.session.settings["type"] = "pdf"
    
    async def process(self, user_input: str) -> None:
        """Ingest a document."""
        if not user_input.strip():
            print_error("Please enter a document path")
            return
        
        doc_type = self.session.settings.get("type", "pdf")
        
        self.session.history.append({
            "role": "user",
            "content": f"Ingest: {user_input}"
        })
        
        with create_spinner("Ingesting document..."):
            response = await api_client.ingest_document(user_input, doc_type)
        
        if response.success:
            message = response.data.get("message", "Document ingested successfully")
            print_document_result(True, message, response.data)
            self.session.history.append({
                "role": "system",
                "content": message
            })
        else:
            print_document_result(False, response.error)
            self.session.history.append({
                "role": "error",
                "content": response.error
            })
    
    def handle_command(self, command: str, args: List[str]) -> bool:
        """Handle document agent specific commands."""
        if command == "type":
            if not args:
                current = self.session.settings.get("type", "pdf")
                for dtype, name in DOCUMENT_TYPES.items():
                    marker = "●" if dtype == current else "○"
                    console.print(f"  [{COLORS['neon'] if dtype == current else COLORS['muted']}]{marker}[/] {dtype}: {name}")
                console.print()
                return True
            
            new_type = args[0].lower()
            if new_type in DOCUMENT_TYPES:
                self.session.settings["type"] = new_type
                print_info(f"Document type set to: {DOCUMENT_TYPES[new_type]}")
            else:
                print_error(f"Invalid type: {new_type}. Use: pdf, markdown, or text")
            return True
        
        return False


class ExecutorAgent(BaseAgent):
    """Agent for executing cryptographic commands via OpenSSL."""
    
    name = "Command Executor"
    icon = "⚡"
    description = "Execute cryptographic operations via OpenSSL backend"
    
    def __init__(self):
        super().__init__()
        self.session.settings["operation"] = None
        self.session.settings["last_keys"] = {}  # Store generated keys for convenience
    
    async def process(self, user_input: str) -> None:
        """Execute a command or parse interactive input."""
        if not user_input.strip():
            print_error("Please enter an operation or parameters")
            self._show_quick_help()
            return
        
        # Check if it's a direct operation command (e.g., "base64_encode hello")
        parts = user_input.strip().split(maxsplit=1)
        operation = parts[0].lower()
        
        # Check if it's a known operation
        all_ops = {}
        for category_ops in EXECUTOR_OPERATIONS.values():
            all_ops.update(category_ops)
        
        if operation in all_ops:
            await self._execute_operation(operation, parts[1] if len(parts) > 1 else "")
        elif operation == "ops" or operation == "operations":
            await self._show_operations()
        elif operation == "keys":
            self._show_stored_keys()
        elif operation == "pqc_health":
            await self._show_pqc_health()
        elif operation == "help":
            self._show_quick_help()
        else:
            # Try to parse as parameters for current operation
            if self.session.settings.get("operation"):
                await self._execute_with_params(user_input)
            else:
                print_error(f"Unknown operation: {operation}")
                self._show_quick_help()
    
    async def _execute_operation(self, operation: str, args: str) -> None:
        """Execute a specific operation."""
        params = self._parse_args(operation, args)
        
        if params is None:
            return
        
        self.session.history.append({
            "role": "user",
            "content": f"{operation}: {args if args else '(default params)'}"
        })
        
        with create_spinner(f"Executing {operation}..."):
            response = await api_client.execute_command(operation, params)
        
        if response.success:
            result = response.data
            print_executor_result(result)
            
            # Store keys if this was a keygen operation
            if operation == "aes_keygen" and result.get("result"):
                self.session.settings["last_keys"]["aes"] = result["result"]
                print_info("Keys stored! Use 'keys' command to view them.")
            elif operation == "rsa_keygen" and result.get("result"):
                self.session.settings["last_keys"]["rsa"] = result["result"]
                print_info("Keys stored! Use 'keys' command to view them.")
            elif operation == "pqc_sig_keygen" and result.get("result"):
                self.session.settings["last_keys"]["pqc_sig"] = result["result"]
                print_info("PQC keys stored! Use 'keys' command to view them.")
            
            self.session.history.append({
                "role": "system",
                "content": result.get("result", {})
            })
        else:
            error_msg = response.error
            if response.data and response.data.get("error"):
                error_msg = response.data["error"].get("message", error_msg)
            print_error(error_msg, "Execution Failed")
            self.session.history.append({
                "role": "error",
                "content": error_msg
            })
    
    def _parse_args(self, operation: str, args: str) -> dict:
        """Parse arguments for an operation."""
        params = {}
        
        # Simple operations that just need data
        if operation in ["base64_encode", "hex_encode"]:
            params["data"] = args if args else ""
            if not params["data"]:
                print_error("Please provide data to encode")
                print_info(f"Usage: {operation} <data>")
                return None
        
        elif operation in ["base64_decode"]:
            params["encoded"] = args if args else ""
            if not params["encoded"]:
                print_error("Please provide Base64 data to decode")
                return None
        
        elif operation in ["hex_decode"]:
            params["hex"] = args if args else ""
            if not params["hex"]:
                print_error("Please provide hex data to decode")
                return None
        
        elif operation in ["random_bytes", "random_hex", "random_base64"]:
            try:
                params["length"] = int(args) if args else 32
            except ValueError:
                print_error("Length must be a number")
                return None
        
        elif operation == "hash":
            parts = args.split() if args else []
            params["data"] = parts[0] if parts else ""
            params["algorithm"] = parts[1] if len(parts) > 1 else "sha256"
            if not params["data"]:
                print_error("Please provide data to hash")
                print_info("Usage: hash <data> [algorithm]")
                return None
        
        elif operation == "hmac":
            parts = args.split() if args else []
            if len(parts) < 2:
                print_error("Please provide data and key")
                print_info("Usage: hmac <data> <key> [algorithm]")
                return None
            params["data"] = parts[0]
            params["key"] = parts[1]
            params["algorithm"] = parts[2] if len(parts) > 2 else "sha256"
        
        elif operation == "aes_keygen":
            try:
                params["bits"] = int(args) if args else 256
            except ValueError:
                params["bits"] = 256
        
        elif operation == "aes_encrypt":
            # Check for stored keys
            stored = self.session.settings.get("last_keys", {}).get("aes")
            if stored and not args:
                print_error("Please provide plaintext to encrypt")
                print_info("Usage: aes_encrypt <plaintext>")
                print_info("(Will use stored keys from last aes_keygen)")
                return None
            
            if stored:
                params["plaintext"] = args
                params["key"] = stored["key_hex"]
                params["iv"] = stored["iv_hex"]
                params["hmac_key"] = stored["hmac_key_hex"]
            else:
                print_error("No stored keys. Run 'aes_keygen' first, or provide full params.")
                return None
        
        elif operation == "aes_decrypt":
            stored = self.session.settings.get("last_keys", {}).get("aes")
            if not args:
                print_error("Please provide: <ciphertext_base64> <hmac_hex>")
                return None
            parts = args.split()
            if len(parts) < 2:
                print_error("Please provide: <ciphertext_base64> <hmac_hex> [iv_hex]")
                return None
            if stored:
                params["ciphertext"] = parts[0]
                params["hmac"] = parts[1]
                params["key"] = stored["key_hex"]
                params["iv"] = parts[2] if len(parts) > 2 else stored["iv_hex"]
                params["hmac_key"] = stored["hmac_key_hex"]
            else:
                print_error("No stored keys. Run 'aes_keygen' first.")
                return None
        
        elif operation == "rsa_keygen":
            try:
                params["bits"] = int(args) if args else 2048
            except ValueError:
                params["bits"] = 2048

        elif operation == "rsa_pubkey":
            stored = self.session.settings.get("last_keys", {}).get("rsa")
            if stored:
                params["private_key"] = stored["private_key_pem"]
            else:
                print_error("No stored keys. Run 'rsa_keygen' first.")
                return None

        elif operation == "pqc_sig_keygen":
            params["algorithm"] = args if args else "mldsa44"

        elif operation == "pqc_sig_sign":
            stored = self.session.settings.get("last_keys", {}).get("pqc_sig")
            if not args:
                print_error("Please provide data to sign")
                return None
            if stored:
                params["data"] = args
                params["private_key"] = stored["private_key_pem"]
                params["algorithm"] = stored.get("algorithm", "mldsa44")
            else:
                print_error("No stored PQC keys. Run 'pqc_sig_keygen' first.")
                return None

        elif operation == "pqc_sig_verify":
            stored = self.session.settings.get("last_keys", {}).get("pqc_sig")
            parts = args.split() if args else []
            if len(parts) < 2:
                print_error("Please provide: <data> <signature_base64>")
                return None
            if stored:
                params["data"] = parts[0]
                params["signature"] = parts[1]
                params["public_key"] = stored["public_key_pem"]
                params["algorithm"] = stored.get("algorithm", "mldsa44")
            else:
                print_error("No stored PQC keys. Run 'pqc_sig_keygen' first.")
                return None
        
        elif operation in ["rsa_sign", "rsa_encrypt"]:
            stored = self.session.settings.get("last_keys", {}).get("rsa")
            if not args:
                print_error("Please provide data")
                return None
            if stored:
                params["data" if operation == "rsa_sign" else "plaintext"] = args
                params["private_key" if operation == "rsa_sign" else "public_key"] = \
                    stored["private_key_pem" if operation == "rsa_sign" else "public_key_pem"]
            else:
                print_error("No stored keys. Run 'rsa_keygen' first.")
                return None
        
        elif operation == "rsa_verify":
            stored = self.session.settings.get("last_keys", {}).get("rsa")
            parts = args.split() if args else []
            if len(parts) < 2:
                print_error("Please provide: <data> <signature_base64>")
                return None
            if stored:
                params["data"] = parts[0]
                params["signature"] = parts[1]
                params["public_key"] = stored["public_key_pem"]
            else:
                print_error("No stored keys. Run 'rsa_keygen' first.")
                return None
        
        elif operation == "rsa_decrypt":
            stored = self.session.settings.get("last_keys", {}).get("rsa")
            if not args:
                print_error("Please provide ciphertext_base64")
                return None
            if stored:
                params["ciphertext"] = args
                params["private_key"] = stored["private_key_pem"]
            else:
                print_error("No stored keys. Run 'rsa_keygen' first.")
                return None
        
        return params
    
    async def _execute_with_params(self, params_str: str) -> None:
        """Execute current operation with provided parameters."""
        operation = self.session.settings.get("operation")
        await self._execute_operation(operation, params_str)
    
    async def _show_operations(self) -> None:
        """Show all available operations."""
        with create_spinner("Fetching operations..."):
            response = await api_client.get_operations()
        
        if response.success:
            print_operations_table(response.data.get("operations", []))
        else:
            # Fallback to local list
            print_operations_table(None)
    
    def _show_stored_keys(self) -> None:
        """Show stored keys."""
        keys = self.session.settings.get("last_keys", {})
        if not keys:
            print_info("No stored keys. Generate some with 'aes_keygen' or 'rsa_keygen'.")
            return
        
        console.print(f"\n[bold {COLORS['neon']}]Stored Keys[/]\n")
        
        if "aes" in keys:
            console.print(f"[{COLORS['info']}]AES Keys:[/]")
            console.print(f"  key_hex: {keys['aes']['key_hex'][:16]}...")
            console.print(f"  iv_hex: {keys['aes']['iv_hex']}")
            console.print(f"  hmac_key_hex: {keys['aes']['hmac_key_hex'][:16]}...")
            console.print()
        
        if "rsa" in keys:
            console.print(f"[{COLORS['info']}]RSA Keys:[/]")
            console.print(f"  bits: {keys['rsa'].get('bits', 'unknown')}")
            console.print(f"  private_key: [dim](stored, {len(keys['rsa']['private_key_pem'])} chars)[/]")
            console.print(f"  public_key: [dim](stored, {len(keys['rsa']['public_key_pem'])} chars)[/]")
            console.print()

        if "pqc_sig" in keys:
            console.print(f"[{COLORS['info']}]PQC Signature Keys:[/]")
            console.print(f"  algorithm: {keys['pqc_sig'].get('algorithm', 'unknown')}")
            console.print(f"  private_key: [dim](stored, {len(keys['pqc_sig']['private_key_pem'])} chars)[/]")
            console.print(f"  public_key: [dim](stored, {len(keys['pqc_sig']['public_key_pem'])} chars)[/]")
            console.print()
    
    def _show_quick_help(self) -> None:
        """Show quick help."""
        console.print(f"\n[{COLORS['muted']}]Quick commands:[/]")
        console.print(f"  [bold]ops[/]              - List all operations")
        console.print(f"  [bold]keys[/]             - Show stored keys")
        console.print(f"  [bold]base64_encode[/] <text>  - Encode to Base64")
        console.print(f"  [bold]random_hex[/] 32    - Generate 32 random hex bytes")
        console.print(f"  [bold]random_base64[/] 32 - Generate 32 random bytes (Base64)")
        console.print(f"  [bold]hash[/] <data> sha256 - Hash data")
        console.print(f"  [bold]aes_keygen[/]       - Generate AES keys")
        console.print(f"  [bold]rsa_keygen[/] 2048  - Generate RSA keypair")
        console.print(f"  [bold]pqc_sig_keygen[/] mldsa44 - Generate PQC signature keys")
        console.print(f"  [bold]pqc_health[/]       - Check PQC provider status")
        console.print()
    
    def handle_command(self, command: str, args: List[str]) -> bool:
        """Handle executor agent specific commands."""
        if command == "ops" or command == "operations":
            import asyncio
            asyncio.create_task(self._show_operations())
            return True
        if command == "pqc_health":
            import asyncio
            asyncio.create_task(self._show_pqc_health())
            return True
        return False

    async def _show_pqc_health(self) -> None:
        """Show PQC provider health."""
        with create_spinner("Checking PQC provider..."):
            response = await api_client.get_pqc_health()
        if response.success:
            print_pqc_health(response.data)
        else:
            print_error(response.error, "PQC Health Check Failed")


# Agent registry
AGENTS = {
    "password": PasswordAgent,
    "crypto": CryptoAgent,
    "choice": ChoiceAgent,
    "document": DocumentAgent,
    "executor": ExecutorAgent,
}


def create_agent(agent_type: str) -> BaseAgent:
    """Create an agent instance."""
    agent_class = AGENTS.get(agent_type)
    if agent_class:
        return agent_class()
    raise ValueError(f"Unknown agent type: {agent_type}")
