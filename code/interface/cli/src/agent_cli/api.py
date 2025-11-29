"""
API client for communicating with agent services.
Handles all HTTP requests with proper error handling and timeouts.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import time

from .config import config


@dataclass
class APIResponse:
    """Standardized API response."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int = 0
    latency_ms: float = 0


class APIClient:
    """Async HTTP client for agent services."""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def _request(
        self, 
        method: str, 
        url: str, 
        json: Optional[Dict] = None,
        **kwargs
    ) -> APIResponse:
        """Make an HTTP request."""
        start_time = time.time()
        try:
            client = await self._get_client()
            response = await client.request(method, url, json=json, **kwargs)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code >= 200 and response.status_code < 300:
                try:
                    data = response.json()
                except:
                    data = {"message": response.text}
                return APIResponse(
                    success=True,
                    data=data,
                    status_code=response.status_code,
                    latency_ms=latency
                )
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail") or error_data.get("message") or str(error_data)
                except:
                    error_msg = response.text or f"HTTP {response.status_code}"
                return APIResponse(
                    success=False,
                    error=error_msg,
                    status_code=response.status_code,
                    latency_ms=latency
                )
        except httpx.TimeoutException:
            return APIResponse(
                success=False,
                error="Request timeout",
                latency_ms=(time.time() - start_time) * 1000
            )
        except httpx.ConnectError:
            return APIResponse(
                success=False,
                error="Connection failed - service may be offline",
                latency_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return APIResponse(
                success=False,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )
    
    # Health check methods
    async def check_health(self, service_config) -> Tuple[bool, float]:
        """Check health of a service."""
        url = service_config.get_url("health")
        response = await self._request("GET", url)
        return response.success, response.latency_ms
    
    async def check_all_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all services."""
        services = {
            "password_checker": ("Password Checker", config.password_checker),
            "theory_specialist": ("Theory Specialist", config.theory_specialist),
            "choice_maker": ("Choice Maker", config.choice_maker),
        }
        
        async def check_service(key: str, name: str, svc_config) -> Tuple[str, Dict]:
            online, latency = await self.check_health(svc_config)
            return key, {
                "name": name,
                "online": online,
                "latency": latency,
                "url": svc_config.base_url
            }
        
        tasks = [
            check_service(key, name, svc_config) 
            for key, (name, svc_config) in services.items()
        ]
        results = await asyncio.gather(*tasks)
        return dict(results)
    
    # Password Checker API
    async def analyze_password(
        self, 
        password: str, 
        components: List[str]
    ) -> APIResponse:
        """Analyze password strength."""
        url = config.password_checker.get_url("score")
        return await self._request("POST", url, json={
            "password": password,
            "components": components
        })
    
    # Theory Specialist / Crypto Expert API
    async def query_crypto_expert(
        self, 
        query: str, 
        conversation_id: Optional[str] = None
    ) -> APIResponse:
        """Query the cryptography expert."""
        url = config.theory_specialist.get_url("generate")
        payload = {"query": query}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        return await self._request("POST", url, json=payload)
    
    async def get_conversations(self) -> APIResponse:
        """Get list of conversations."""
        url = config.theory_specialist.get_url("conversations")
        return await self._request("GET", url)
    
    # Document Ingestion API
    async def ingest_document(
        self, 
        document_path: str, 
        document_type: str
    ) -> APIResponse:
        """Ingest a document into the knowledge base."""
        url = config.theory_specialist.get_url("ingest")
        return await self._request("POST", url, json={
            "document_path": document_path,
            "document_type": "md" if document_type == "markdown" else document_type
        })
    
    # Choice Maker API
    async def extract_intent(self, text: str) -> APIResponse:
        """Extract intent from text."""
        url = config.choice_maker.get_url("extract")
        return await self._request("POST", url, json={
            "text": text,
            "operation": "intent_extraction"
        })
    
    async def extract_entities(self, text: str) -> APIResponse:
        """Extract entities from text."""
        url = config.choice_maker.get_url("extract")
        return await self._request("POST", url, json={
            "text": text,
            "operation": "entity_extraction"
        })
    
    async def extract_both(self, text: str) -> Tuple[APIResponse, APIResponse]:
        """Extract both intent and entities."""
        intent_task = self.extract_intent(text)
        entity_task = self.extract_entities(text)
        return await asyncio.gather(intent_task, entity_task)


# Global API client instance
api_client = APIClient()
