"""
Agent implementations for the CLI interface.
Each agent handles a specific domain of functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .api import api_client, APIResponse
from .config import PASSWORD_COMPONENTS, CHOICE_MODES, DOCUMENT_TYPES
from .ui import (
    console,
    print_password_result,
    print_crypto_response,
    print_choice_result,
    print_document_result,
    print_error,
    print_info,
    print_components_table,
    print_mode_table,
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


# Agent registry
AGENTS = {
    "password": PasswordAgent,
    "crypto": CryptoAgent,
    "choice": ChoiceAgent,
    "document": DocumentAgent,
}


def create_agent(agent_type: str) -> BaseAgent:
    """Create an agent instance."""
    agent_class = AGENTS.get(agent_type)
    if agent_class:
        return agent_class()
    raise ValueError(f"Unknown agent type: {agent_type}")
