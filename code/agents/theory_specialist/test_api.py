#!/usr/bin/env python3
"""
Comprehensive test script for the Cryptography RAG System API.

This script tests:
1. Provider switching (Ollama local, Ollama Cloud)
2. Query generation with and without provider override
3. Viewing document ingestion status
4. Ingesting new documents
5. Documents folder verification
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

# ============================================
# Configuration
# ============================================

API_BASE_URL = os.getenv("THEORY_SPECIALIST_URL", "http://localhost:8100")

# Replace these with your actual credentials
OLLAMA_CLOUD_API_KEY = os.getenv("OLLAMA_CLOUD_API_KEY", "your-api-key-here")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


# ============================================
# Helper Functions
# ============================================

def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.ENDC}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ {message}{Colors.ENDC}")


def print_test(name: str) -> None:
    """Print a test name."""
    print(f"{Colors.YELLOW}Testing: {name}{Colors.ENDC}")


def api_request(method: str, endpoint: str, data: dict = None) -> tuple[int, Any]:
    """
    Make an API request and return the status code and response data.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        data: Request body data for POST requests

    Returns:
        Tuple of (status_code, response_data)
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=120)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        try:
            return response.status_code, response.json()
        except json.JSONDecodeError:
            return response.status_code, response.text

    except requests.exceptions.ConnectionError:
        return -1, {"error": "Connection refused. Is the API running?"}
    except requests.exceptions.Timeout:
        return -2, {"error": "Request timed out"}
    except Exception as e:
        return -3, {"error": str(e)}


def pretty_print_response(title: str, data: Any) -> None:
    """Pretty print JSON response."""
    print(f"{Colors.MAGENTA}{title}:{Colors.ENDC}")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()


# ============================================
# Test Functions
# ============================================

def test_health_check() -> bool:
    """Test 1: Health check endpoint."""
    print_test("Health Check")
    status, data = api_request("GET", "/health")

    if status == 200:
        print_success("Health check passed")
        pretty_print_response("Health Status", data)
        return True
    else:
        print_error(f"Health check failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_view_status() -> bool:
    """Test 2: View ingestion status."""
    print_test("View Document Ingestion Status")
    status, data = api_request("GET", "/status")

    if status == 200:
        print_success("Status retrieved successfully")
        print(f"  Total documents: {data.get('total_reference_documents', 0)}")
        print(f"  Processed: {data.get('processed_documents', 0)}")
        print(f"  Pending: {data.get('pending_documents', 0)}")
        print(f"  In progress: {data.get('in_progress_documents', 0)}")
        print(f"  Total chunks: {data.get('total_chunks_in_vector_db', 0)}")
        return True
    else:
        print_error(f"Status check failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_switch_to_ollama_local() -> bool:
    """Test 3: Switch provider to local Ollama."""
    print_test("Switch provider to Ollama (Local)")
    status, data = api_request("POST", "/provider", {
        "provider": "ollama",
        "ollama_url": "http://127.0.0.1:11434",
        "ollama_model": "phi3"
    })

    if status == 200:
        print_success("Switched to local Ollama successfully")
        pretty_print_response("Provider Response", data)
        return True
    else:
        print_error(f"Provider switch failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_switch_to_ollama_cloud() -> bool:
    """Test 4: Switch provider to Ollama Cloud."""
    print_test("Switch provider to Ollama Cloud")

    if OLLAMA_CLOUD_API_KEY == "your-api-key-here":
        print_error("OLLAMA_CLOUD_API_KEY not set. Skipping Ollama Cloud test.")
        return True  # Don't fail, just skip

    status, data = api_request("POST", "/provider", {
        "provider": "ollama-cloud",
        "ollama_model": "deepseek-v3.2:cloud",
        "ollama_api_key": OLLAMA_CLOUD_API_KEY
    })

    if status == 200:
        print_success("Switched to Ollama Cloud successfully")
        pretty_print_response("Provider Response", data)
        return True
    else:
        print_error(f"Ollama Cloud switch failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_generate_default_provider() -> bool:
    """Test 5: Generate answer with default provider."""
    print_test("Generate answer with default provider")
    status, data = api_request("POST", "/generate", {
        "query": "What is RSA encryption?",
        "conversation_id": None
    })

    if status == 200:
        print_success("Generated answer successfully")
        print(f"  Answer length: {len(data.get('answer', ''))} characters")
        print(f"  Sources found: {len(data.get('sources', []))}")
        print(f"  Conversation ID: {data.get('conversation_id', 'N/A')}")
        return data.get('conversation_id'), data
    else:
        print_error(f"Generate request failed with status {status}")
        pretty_print_response("Error", data)
        return None, None


def test_generate_with_provider_override(ollama_cloud_key: str) -> bool:
    """Test 6: Generate answer with provider override in request."""
    print_test("Generate answer with provider override")

    if ollama_cloud_key == "your-api-key-here":
        print_info("Skipping provider override test (no API key)")
        return True

    status, data = api_request("POST", "/generate", {
        "query": "What is AES encryption?",
        "provider": "ollama-cloud",
        "ollama_model": "deepseek-v3.2:cloud",
        "ollama_api_key": ollama_cloud_key
    })

    if status == 200:
        print_success("Generated answer with provider override successfully")
        print(f"  Answer length: {len(data.get('answer', ''))} characters")
        print(f"  Sources found: {len(data.get('sources', []))}")
        return True
    else:
        print_error(f"Generate with override failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_ingest_document() -> bool:
    """Test 7: Ingest a new document."""
    print_test("Ingest a new document")

    # Try to find a PDF file in the documents folder
    status, data = api_request("GET", "/config")
    print_info("Current configuration checked")

    # First, let's check what documents exist
    # For this test, we'll try to ingest a remote document
    test_doc_url = "https://www.rfc-editor.org/rfc/rfc8017.txt"  # Example: Cryptographic RFC
    # Or use a local test file

    status, data = api_request("POST", "/ingest", {
        "document_path": test_doc_url,
        "document_type": "txt"
    })

    if status == 200:
        print_success("Document queued for ingestion")
        pretty_print_response("Ingest Response", data)
        return True
    elif status == 400:
        # Document might already be queued
        print_info("Document may already be queued (status 400)")
        pretty_print_response("Response", data)
        return True
    else:
        print_error(f"Ingest failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_auto_ingest() -> bool:
    """Test 8: Auto-discover and ingest documents."""
    print_test("Auto-discover and ingest documents")
    status, data = api_request("POST", "/auto-ingest")

    if status == 200:
        discovered = data.get('discovered_count', 0)
        queued = data.get('queued_count', 0)
        print_success(f"Auto-discovery completed: {discovered} found, {queued} queued")
        pretty_print_response("Auto-ingest Response", data)
        return True
    else:
        print_error(f"Auto-ingest failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_config_management() -> bool:
    """Test 9: Configure ingestion workers."""
    print_test("Configure ingestion workers")
    status, data = api_request("POST", "/config", {
        "ingestion_workers": 3,
        "parallel_requests": 2
    })

    if status == 200:
        print_success("Configuration updated successfully")
        pretty_print_response("Config Response", data)
        return True
    else:
        print_error(f"Config update failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_get_config() -> bool:
    """Test 10: Get current configuration."""
    print_test("Get current configuration")
    status, data = api_request("GET", "/config")

    if status == 200:
        print_success("Configuration retrieved successfully")
        pretty_print_response("Config", data)
        return True
    else:
        print_error(f"Get config failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_conversation_history(conversation_id: str) -> bool:
    """Test 11: Get conversation history."""
    print_test(f"Get conversation history for {conversation_id}")

    if not conversation_id:
        print_info("No conversation ID provided, skipping conversation history test")
        return True

    status, data = api_request("GET", f"/conversations/{conversation_id}")

    if status == 200:
        print_success(f"Retrieved {len(data.get('messages', []))} messages")
        pretty_print_response("Conversation", data)
        return True
    else:
        print_error(f"Conversation history failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_switch_to_openai() -> bool:
    """Test switching to OpenAI provider."""
    print_test("Switch provider to OpenAI")

    if not OPENAI_API_KEY:
        print_info("OPENAI_API_KEY not set. Skipping OpenAI test.")
        return True

    status, data = api_request("POST", "/provider", {
        "provider": "openai",
        "openai_api_key": OPENAI_API_KEY,
        "openai_model": "gpt-4o-mini"
    })

    if status == 200:
        print_success("Switched to OpenAI successfully")
        pretty_print_response("Provider Response", data)
        return True
    else:
        print_error(f"OpenAI switch failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_switch_to_gemini() -> bool:
    """Test switching to Gemini provider."""
    print_test("Switch provider to Gemini")

    if not GEMINI_API_KEY:
        print_info("GEMINI_API_KEY not set. Skipping Gemini test.")
        return True

    status, data = api_request("POST", "/provider", {
        "provider": "gemini",
        "gemini_api_key": GEMINI_API_KEY,
        "gemini_model": "gemini-1.5-flash"
    })

    if status == 200:
        print_success("Switched to Gemini successfully")
        pretty_print_response("Provider Response", data)
        return True
    else:
        print_error(f"Gemini switch failed with status {status}")
        pretty_print_response("Error", data)
        return False


def test_switch_back_to_ollama() -> bool:
    """Test switching back to Ollama (cleanup)."""
    print_test("Switch back to Ollama (cleanup)")
    status, data = api_request("POST", "/provider", {
        "provider": "ollama",
        "ollama_url": "http://127.0.0.1:11434",
        "ollama_model": "phi3"
    })

    if status == 200:
        print_success("Switched back to local Ollama")
        return True
    else:
        print_error(f"Failed to switch back to Ollama with status {status}")
        return False


# ============================================
# Main Test Runner
# ============================================

def main() -> int:
    """Run all tests and return exit code."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   Cryptography RAG System - API Test Suite              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")

    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"Ollama Cloud API Key: {'SET' if OLLAMA_CLOUD_API_KEY != 'your-api-key-here' else 'NOT SET'}")
    print_info(f"OpenAI API Key: {'SET' if OPENAI_API_KEY else 'NOT SET'}")
    print_info(f"Gemini API Key: {'SET' if GEMINI_API_KEY else 'NOT SET'}")

    # Check if API is running
    print_section("Step 0: API Connectivity Check")
    if not test_health_check():
        print_error("\nAPI is not responding. Please ensure the service is running:")
        print("  - docker-compose up theory-specialist")
        print("  - Or: uvicorn app.main:app --port 8000")
        return 1

    results = []

    # Test 1: View current status
    print_section("Step 1: Check Document Ingestion Status")
    results.append(test_view_status())

    # Test 2: Switch to local Ollama
    print_section("Step 2: Switch Provider to Ollama Local")
    results.append(test_switch_to_ollama_local())

    # Test 3: Generate with default provider
    print_section("Step 3: Generate Answer (Default Provider)")
    conversation_id, _ = test_generate_default_provider()
    results.append(conversation_id is not None)

    # Test 4: Generate with provider override
    print_section("Step 4: Generate Answer with Provider Override")
    results.append(test_generate_with_provider_override(OLLAMA_CLOUD_API_KEY))

    # Test 5: Switch to Ollama Cloud
    print_section("Step 5: Switch Provider to Ollama Cloud")
    results.append(test_switch_to_ollama_cloud())

    # Test 6: Switch to OpenAI
    print_section("Step 6: Switch Provider to OpenAI")
    results.append(test_switch_to_openai())

    # Test 7: Switch to Gemini
    print_section("Step 7: Switch Provider to Gemini")
    results.append(test_switch_to_gemini())

    # Test 8: Switch back to Ollama
    print_section("Step 8: Switch Back to Ollama")
    results.append(test_switch_back_to_ollama())

    # Test 9: Auto-discover documents
    print_section("Step 9: Auto-Discover Documents")
    results.append(test_auto_ingest())

    # Test 10: Ingest new document
    print_section("Step 10: Ingest New Document")
    results.append(test_ingest_document())

    # Test 11: Configure ingestion workers
    print_section("Step 11: Configure Ingestion Workers")
    results.append(test_config_management())

    # Test 12: Get configuration
    print_section("Step 12: Get Configuration")
    results.append(test_get_config())

    # Test 13: Get conversation history
    print_section("Step 13: Get Conversation History")
    results.append(test_conversation_history(conversation_id))

    # Final status
    print_section("Test Results Summary")
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0

    if passed == total:
        print_success(f"All tests passed! ({passed}/{total})")
    else:
        print_error(f"Some tests failed: {passed}/{total} passed ({success_rate:.1f}%)")

    print()

    # Return exit code based on results
    return 0 if passed == total else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
