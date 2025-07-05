"""Cerebras API client implementation."""

import asyncio
import json
import time
from typing import AsyncIterator, Dict, List, Optional, Any

import aiohttp
from cerebras.cloud.sdk import Cerebras

from cerebras_cli.core.config import Config
from cerebras_cli.exceptions import APIError, AuthenticationError, ValidationError


class CerebrasClient:
    """Async client for interacting with Cerebras API.
    
    Provides both sync and async interfaces for compatibility.
    """
    
    def __init__(self, config: Config) -> None:
        """Initialize client with configuration.
        
        Args:
            config: Configuration object with API settings
            
        Raises:
            AuthenticationError: If API key is missing
        """
        if not config.api_key:
            raise AuthenticationError("Cerebras API key is required")
        
        self.config = config
        self._sync_client = Cerebras(api_key=config.api_key)
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self) -> "CerebrasClient":
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.api.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                }
            )
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def generate_completion_sync(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> Any:
        """Generate completion synchronously (for backward compatibility).
        
        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            
        Returns:
            API response object
            
        Raises:
            APIError: If API request fails
            ValidationError: If messages are invalid
        """
        try:
            self._validate_messages(messages)
            
            response = self._sync_client.chat.completions.create(
                messages=messages,
                model=self.config.model,
                stream=stream
            )
            
            return response
            
        except Exception as e:
            if "authentication" in str(e).lower():
                raise AuthenticationError(f"Authentication failed: {e}")
            elif "rate limit" in str(e).lower():
                raise APIError(f"Rate limit exceeded: {e}")
            else:
                raise APIError(f"API request failed: {e}")
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate completion asynchronously.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            API response as dictionary
            
        Raises:
            APIError: If API request fails
            ValidationError: If messages are invalid
        """
        self._validate_messages(messages)
        await self._ensure_session()
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        return await self._make_request("/v1/chat/completions", payload)
    
    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """Stream completion asynchronously.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Yields:
            Text chunks from the API response
            
        Raises:
            APIError: If API request fails
            ValidationError: If messages are invalid
        """
        self._validate_messages(messages)
        await self._ensure_session()
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        async for chunk in self._stream_request("/v1/chat/completions", payload):
            yield chunk
    
    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make HTTP request to API.
        
        Args:
            endpoint: API endpoint path
            payload: Request payload
            
        Returns:
            API response as dictionary
            
        Raises:
            APIError: If request fails
        """
        url = f"{self.config.api.base_url}{endpoint}"
        
        for attempt in range(self.config.api.max_retries + 1):
            try:
                async with self._session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        raise AuthenticationError("Invalid API key")
                    elif response.status == 429:
                        if attempt < self.config.api.max_retries:
                            await asyncio.sleep(self.config.api.retry_delay * (2 ** attempt))
                            continue
                        raise APIError("Rate limit exceeded")
                    else:
                        error_text = await response.text()
                        raise APIError(
                            f"API request failed with status {response.status}: {error_text}",
                            status_code=response.status
                        )
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.config.api.max_retries:
                    await asyncio.sleep(self.config.api.retry_delay * (2 ** attempt))
                    continue
                raise APIError(f"Network error: {e}")
        
        raise APIError("Max retries exceeded")
    
    async def _stream_request(
        self,
        endpoint: str,
        payload: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """Make streaming HTTP request to API.
        
        Args:
            endpoint: API endpoint path
            payload: Request payload
            
        Yields:
            Text chunks from the response
            
        Raises:
            APIError: If request fails
        """
        url = f"{self.config.api.base_url}{endpoint}"
        
        try:
            async with self._session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise APIError(
                        f"Streaming request failed with status {response.status}: {error_text}",
                        status_code=response.status
                    )
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        if data == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue  # Skip invalid JSON lines
                            
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise APIError(f"Streaming request failed: {e}")
    
    def _validate_messages(self, messages: List[Dict[str, str]]) -> None:
        """Validate message format.
        
        Args:
            messages: List of conversation messages
            
        Raises:
            ValidationError: If messages are invalid
        """
        if not messages:
            raise ValidationError("Messages list cannot be empty")
        
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                raise ValidationError(f"Message {i} must be a dictionary")
            
            if 'role' not in message:
                raise ValidationError(f"Message {i} missing 'role' field")
            
            if 'content' not in message:
                raise ValidationError(f"Message {i} missing 'content' field")
            
            if message['role'] not in ['system', 'user', 'assistant']:
                raise ValidationError(f"Message {i} has invalid role: {message['role']}")
            
            if not isinstance(message['content'], str):
                raise ValidationError(f"Message {i} content must be string")


class ResponseProcessor:
    """Process and format API responses."""
    
    @staticmethod
    def extract_content(response: Any) -> str:
        """Extract content from API response.
        
        Args:
            response: API response object
            
        Returns:
            Extracted text content
        """
        if hasattr(response, 'choices') and response.choices:
            return response.choices[0].message.content
        elif isinstance(response, dict) and 'choices' in response:
            return response['choices'][0]['message']['content']
        else:
            return str(response)
    
    @staticmethod
    def extract_usage_info(response: Any) -> Dict[str, Any]:
        """Extract usage information from API response.
        
        Args:
            response: API response object
            
        Returns:
            Dictionary with usage information
        """
        usage_info = {}
        
        if hasattr(response, 'usage'):
            usage = response.usage
            usage_info = {
                'total_tokens': getattr(usage, 'total_tokens', 0),
                'prompt_tokens': getattr(usage, 'prompt_tokens', 0),
                'completion_tokens': getattr(usage, 'completion_tokens', 0),
            }
        elif isinstance(response, dict) and 'usage' in response:
            usage = response['usage']
            usage_info = {
                'total_tokens': usage.get('total_tokens', 0),
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
            }
        
        # Add timing information if available
        if hasattr(response, 'time_info'):
            time_info = response.time_info
            usage_info.update({
                'total_time': getattr(time_info, 'total_time', 0),
                'tokens_per_second': usage_info.get('total_tokens', 0) / max(getattr(time_info, 'total_time', 1), 0.001)
            })
        
        return usage_info
