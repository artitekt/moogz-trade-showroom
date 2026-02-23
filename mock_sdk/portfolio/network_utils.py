# (c) 2026 Matthew Peter Geary dba MoogzTrade. All Rights Reserved.
# This source code is proprietary and confidential. 
# Version: 1.1.0-GOLD | Module: Network Utilities
# Licensing: Contact [Your Email]

"""
Network Utilities Module
Enterprise-grade network resilience with Circuit Breaker pattern
"""

import time
import asyncio
import random
import functools
import socket
import hmac
import hashlib
import base64
from typing import Dict, Any, Optional, Callable, Union, TypeVar, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


class PartialSuccessError(Exception):
    """Exception for partial success scenarios"""
    pass


class DNSTimeoutError(Exception):
    """Exception for DNS timeout scenarios"""
    pass


@dataclass
class CircuitBreakerConfig:
    """Configuration for Circuit Breaker"""
    failure_threshold: int = 5          # Number of failures before opening
    recovery_timeout: float = 60.0      # Seconds to wait before trying again
    expected_exception: type = Exception  # Exception type that counts as failure
    success_threshold: int = 2          # Success count needed to close circuit
    timeout: float = 30.0               # Function timeout in seconds
    max_retries: int = 3                # Maximum retry attempts
    base_delay: float = 1.0             # Base delay for exponential backoff
    max_delay: float = 60.0             # Maximum delay for exponential backoff
    jitter: bool = True                 # Add jitter to prevent thundering herd
    
    # Elite-tier features
    failure_window_seconds: float = 30.0  # Rolling window for failure counting
    jitter_compensation: bool = True      # Enable self-healing jitter compensation
    min_success_samples: int = 2         # Minimum successes for jitter compensation


@dataclass
class CallResult:
    """Result of a circuit breaker protected call"""
    success: bool
    result: Any = None
    exception: Optional[Exception] = None
    duration: float = 0.0
    attempts: int = 0
    circuit_state: CircuitState = CircuitState.CLOSED
    partial_success: bool = False
    dns_timeout: bool = False


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """Enterprise Circuit Breaker implementation"""
    
    def __init__(self, config: CircuitBreakerConfig = None):
        """
        Initialize circuit breaker
        
        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.logger = logging.getLogger(__name__)
        
        # State tracking
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._last_success_time: Optional[datetime] = None
        
        # Statistics
        self._total_calls = 0
        self._total_failures = 0
        self._total_successes = 0
        
        # Elite-tier features: Windowed accounting
        self._failure_timestamps: List[datetime] = []  # Rolling window of failure timestamps
        self._recent_successes: List[datetime] = []   # Recent successes for jitter compensation
        self._isolated_failure_detected = False      # Track isolated failures
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state
    
    @property
    def failure_count(self) -> int:
        """Get current failure count"""
        return self._failure_count
    
    @property
    def success_count(self) -> int:
        """Get current success count"""
        return self._success_count
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self._state == CircuitState.OPEN
    
    @property
    def statistics(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_successes": self._total_successes,
            "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "last_success_time": self._last_success_time.isoformat() if self._last_success_time else None,
            "failure_rate": self._total_failures / max(self._total_calls, 1)
        }
    
    def _clean_failure_window(self):
        """Clean old failures outside the rolling window"""
        cutoff_time = datetime.now() - timedelta(seconds=self.config.failure_window_seconds)
        self._failure_timestamps = [ts for ts in self._failure_timestamps if ts > cutoff_time]
        self._failure_count = len(self._failure_timestamps)
    
    def _add_failure_to_window(self):
        """Add a failure to the rolling window"""
        self._failure_timestamps.append(datetime.now())
        self._clean_failure_window()
    
    def _check_jitter_compensation(self) -> bool:
        """Check if we should apply jitter compensation (self-healing)"""
        if not self.config.jitter_compensation:
            return False
        
        # Need at least minimum success samples
        if len(self._recent_successes) < self.config.min_success_samples:
            return False
        
        # Check if we have recent successes after an isolated failure
        if self._isolated_failure_detected:
            # If we have enough recent successes, heal the circuit
            recent_success_cutoff = datetime.now() - timedelta(seconds=10)  # Last 10 seconds
            recent_success_count = sum(1 for ts in self._recent_successes if ts > recent_success_cutoff)
            
            if recent_success_count >= self.config.min_success_samples:
                self.logger.info("Jitter compensation: Self-healing after isolated failure")
                self._isolated_failure_detected = False
                # Remove the isolated failure from the window
                if self._failure_timestamps:
                    self._failure_timestamps.pop(0)  # Remove the oldest (isolated) failure
                    self._failure_count = len(self._failure_timestamps)
                return True
        
        return False
    
    def _detect_isolated_failure(self):
        """Detect if this might be an isolated failure (jitter)"""
        if not self.config.jitter_compensation:
            return False
        
        # Check if this is the first failure in a while
        if self._failure_count == 1:
            # Look for recent successes
            recent_success_cutoff = datetime.now() - timedelta(seconds=5)  # Last 5 seconds
            recent_success_count = sum(1 for ts in self._recent_successes if ts > recent_success_cutoff)
            
            if recent_success_count >= 2:  # Had 2+ recent successes
                self._isolated_failure_detected = True
                self.logger.warning("Isolated failure detected (possible jitter)")
                return True
        
        return False
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset"""
        if self._state != CircuitState.OPEN:
            return False
        
        if not self._last_failure_time:
            return False
        
        time_since_failure = datetime.now() - self._last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout
    
    def _call_succeeded(self):
        """Handle successful call"""
        self._success_count += 1
        # Don't increment _total_successes here - handled in call_async
        self._last_success_time = datetime.now()
        
        # Track recent successes for jitter compensation
        self._recent_successes.append(datetime.now())
        # Keep only recent successes (last 30 seconds)
        cutoff_time = datetime.now() - timedelta(seconds=30)
        self._recent_successes = [ts for ts in self._recent_successes if ts > cutoff_time]
        
        # Check for jitter compensation
        if self._check_jitter_compensation():
            return  # Self-healing occurred
        
        if self._state == CircuitState.HALF_OPEN:
            if self._success_count >= self.config.success_threshold:
                # Circuit recovered, close it
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                self.logger.info("Circuit breaker closed after successful recovery")
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success in closed state
            self._failure_count = max(0, self._failure_count - 1)
    
    def _call_failed(self, exception: Exception):
        """Handle failed call"""
        self._failure_count += 1
        # Don't increment _total_failures here - handled in call_async
        self._last_failure_time = datetime.now()
        
        # Add failure to rolling window
        self._add_failure_to_window()
        
        # Check for isolated failure (jitter)
        if self._detect_isolated_failure():
            return  # Don't open circuit for isolated failures
        
        if self._state == CircuitState.CLOSED:
            if self._failure_count >= self.config.failure_threshold:
                # Open circuit due to too many failures in window
                self._state = CircuitState.OPEN
                self.logger.warning(f"Circuit breaker opened after {self._failure_count} failures in {self.config.failure_window_seconds}s window")
        elif self._state == CircuitState.HALF_OPEN:
            # Circuit failed during recovery, open it again
            self._state = CircuitState.OPEN
            self._success_count = 0
            self.logger.warning("Circuit breaker re-opened during recovery")
    
    def _handle_partial_success(self, result: Any) -> CallResult:
        """Handle partial success scenarios"""
        duration = time.time() - getattr(self, '_call_start_time', time.time())
        
        # Partial success counts as neither full success nor failure
        # but we track it for monitoring
        self._call_succeeded()  # Still count as success to keep circuit closed
        
        return CallResult(
            success=True,  # Consider partial success as success for circuit state
            result=result,
            duration=duration,
            attempts=1,
            circuit_state=self._state,
            partial_success=True
        )
    
    def _handle_dns_timeout(self, exception: Exception) -> CallResult:
        """Handle DNS timeout scenarios"""
        duration = time.time() - getattr(self, '_call_start_time', time.time())
        
        # DNS timeout is treated as a special type of failure
        # that may not require circuit opening
        self._failure_count += 1
        # Don't increment _total_failures here - handled in call_async
        self._last_failure_time = datetime.now()
        
        # Only open circuit if DNS timeouts exceed threshold
        dns_failure_threshold = self.config.failure_threshold * 2  # Higher threshold for DNS
        
        if self._state == CircuitState.CLOSED:
            if self._failure_count >= dns_failure_threshold:
                self._state = CircuitState.OPEN
                self.logger.warning(f"Circuit breaker opened after {self._failure_count} DNS timeouts")
        
        return CallResult(
            success=False,
            exception=exception,
            duration=duration,
            attempts=1,
            circuit_state=self._state,
            dns_timeout=True
        )
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        delay = self.config.base_delay * (2 ** (attempt - 1))
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Add jitter to prevent thundering herd
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    async def call_async(self, func: Callable, *args, **kwargs) -> CallResult:
        """
        Execute async function with circuit breaker protection
        
        Args:
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            CallResult with execution details
        """
        start_time = time.time()
        self._call_start_time = start_time  # Store for partial success handling
        attempts = 0
        last_exception = None
        result = None
        
        # Increment total calls exactly ONCE at the very beginning
        self._total_calls += 1
        
        # Check if circuit is open
        if self._state == CircuitState.OPEN and not self._should_attempt_reset():
            duration = time.time() - start_time
            # Count circuit open as failure
            self._total_failures += 1
            return CallResult(
                success=False,
                exception=CircuitBreakerError("Circuit breaker is open"),
                duration=duration,
                attempts=0,
                circuit_state=self._state
            )
        
        # Transition to half-open if we're attempting reset
        if self._state == CircuitState.OPEN and self._should_attempt_reset():
            self._state = CircuitState.HALF_OPEN
            self._success_count = 0
            self.logger.info("Circuit breaker transitioning to half-open")
        
        try:
            # Execute with retries
            for attempt in range(self.config.max_retries + 1):
                attempts += 1
                
                # Add delay for retries (except first attempt)
                if attempt > 0:
                    delay = self._calculate_backoff_delay(attempt)
                    await asyncio.sleep(delay)
                
                # Execute with timeout
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
                else:
                    # Wrap sync function for async execution
                    result = await asyncio.wait_for(
                        asyncio.to_thread(func, *args, **kwargs), 
                        timeout=self.config.timeout
                    )
                
                # Check for partial success scenarios
                if isinstance(result, dict) and result.get("status") == "partial_success":
                    return self._handle_partial_success(result)
                
                # Success - break out of retry loop
                break
                
        except Exception as e:
            last_exception = e
            
            # Handle special cases
            if isinstance(e, DNSTimeoutError):
                self._total_failures += 1
                return self._handle_dns_timeout(e)
            
            # Handle circuit breaker errors (shouldn't happen here but just in case)
            if isinstance(e, CircuitBreakerError):
                self._total_failures += 1
                raise e
            
            # Map network-related exceptions to failures
            network_exceptions = (
                ConnectionError,
                ConnectionRefusedError,
                socket.timeout,
                socket.gaierror,  # DNS resolution errors
                OSError,  # General socket errors
                asyncio.TimeoutError,
            )
            
            # Try to import aiohttp exceptions if available
            try:
                import aiohttp
                network_exceptions += (
                    aiohttp.ClientConnectorError,
                    aiohttp.ClientTimeout,
                    aiohttp.ClientConnectionError,
                )
            except ImportError:
                pass  # aiohttp not available
            
            # Check if this is a network-related failure
            is_network_failure = isinstance(e, network_exceptions)
            
            if is_network_failure:
                # Call failed - update circuit state
                self._call_failed(e)
            else:
                # For non-network exceptions, still count as failure but don't affect circuit state
                self._failure_count += 1
                self._last_failure_time = datetime.now()
            
            # If circuit is now open, break early
            if self._state == CircuitState.OPEN:
                pass  # Will be handled in finally block
        
        finally:
            # Centralized statistics handling
            if last_exception is None and result is not None:
                # Success case
                if not (isinstance(result, dict) and result.get("status") == "partial_success"):
                    self._call_succeeded()
                    self._total_successes += 1
                    duration = time.time() - start_time
                    return CallResult(
                        success=True,
                        result=result,
                        duration=duration,
                        attempts=attempts,
                        circuit_state=self._state
                    )
            elif last_exception is not None:
                # Failure case (except DNS timeout which is handled above)
                if not isinstance(last_exception, DNSTimeoutError):
                    self._total_failures += 1
                    duration = time.time() - start_time
                    return CallResult(
                        success=False,
                        exception=last_exception,
                        duration=duration,
                        attempts=attempts,
                        circuit_state=self._state
                    )
        
        # This should not be reached, but just in case
        duration = time.time() - start_time
        return CallResult(
            success=False,
            exception=RuntimeError("Unexpected flow in circuit breaker"),
            duration=duration,
            attempts=attempts,
            circuit_state=self._state
        )
    
    def call_sync(self, func: Callable, *args, **kwargs) -> CallResult:
        """
        Execute synchronous function with circuit breaker protection
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            CallResult with execution details
        """
        start_time = time.time()
        attempts = 0
        last_exception = None
        
        self._total_calls += 1
        
        # Check if circuit is open
        if self._state == CircuitState.OPEN and not self._should_attempt_reset():
            duration = time.time() - start_time
            return CallResult(
                success=False,
                exception=CircuitBreakerError("Circuit breaker is open"),
                duration=duration,
                attempts=0,
                circuit_state=self._state
            )
        
        # Transition to half-open if we're attempting reset
        if self._state == CircuitState.OPEN and self._should_attempt_reset():
            self._state = CircuitState.HALF_OPEN
            self._success_count = 0
            self.logger.info("Circuit breaker transitioning to half-open")
        
        # Execute with retries
        for attempt in range(self.config.max_retries + 1):
            attempts += 1
            
            try:
                # Add delay for retries (except first attempt)
                if attempt > 0:
                    delay = self._calculate_backoff_delay(attempt)
                    time.sleep(delay)
                
                # Execute with timeout
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Function call timed out after {self.config.timeout} seconds")
                
                # Set timeout
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(self.config.timeout))
                
                try:
                    result = func(*args, **kwargs)
                finally:
                    signal.alarm(0)  # Cancel alarm
                
                # Success
                duration = time.time() - start_time
                self._call_succeeded()
                
                return CallResult(
                    success=True,
                    result=result,
                    duration=duration,
                    attempts=attempts,
                    circuit_state=self._state
                )
                
            except Exception as e:
                last_exception = e
                
                # Check if this exception counts as a failure
                if isinstance(e, self.config.expected_exception) or isinstance(e, TimeoutError):
                    self._call_failed(e)
                else:
                    # Unexpected exception, still count as failure
                    self._call_failed(e)
                
                # If circuit is now open, break early
                if self._state == CircuitState.OPEN:
                    break
        
        # All attempts failed
        duration = time.time() - start_time
        return CallResult(
            success=False,
            exception=last_exception,
            duration=duration,
            attempts=attempts,
            circuit_state=self._state
        )
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self.logger.info("Circuit breaker manually reset to closed state")


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """
    Get or create a circuit breaker by name
    
    Args:
        name: Circuit breaker name
        config: Configuration for new circuit breaker
        
    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(config)
    return _circuit_breakers[name]


def circuit_breaker(name: str = None, config: CircuitBreakerConfig = None):
    """
    Decorator to apply circuit breaker to functions
    
    Args:
        name: Circuit breaker name (defaults to function name)
        config: Circuit breaker configuration
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        breaker = get_circuit_breaker(breaker_name, config)
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await breaker.call_async(func, *args, **kwargs)
                if result.success:
                    return result.result
                else:
                    raise result.exception
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = breaker.call_sync(func, *args, **kwargs)
                if result.success:
                    return result.result
                else:
                    raise result.exception
            
            return sync_wrapper
    
    return decorator


def resilient_api_call(endpoint: str, method: str = "GET", 
                      failure_threshold: int = 5, timeout: float = 30.0,
                      max_retries: int = 3, secret_key: str = None, api_key: str = None):
    """
    Specialized decorator for API calls with sensible defaults and optional signing
    
    Args:
        endpoint: API endpoint identifier
        method: HTTP method
        failure_threshold: Failure threshold for circuit breaker
        timeout: Request timeout
        max_retries: Maximum retry attempts
        secret_key: Secret key for HMAC signing
        api_key: API key for signing
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        timeout=timeout,
        max_retries=max_retries,
        expected_exception=(ConnectionError, TimeoutError, HTTPError)
    )
    
    # Apply circuit breaker
    cb_decorator = circuit_breaker(f"api_{endpoint}_{method.lower()}", config)
    
    # Apply signing if keys provided
    if secret_key and api_key:
        sign_decorator = signed_request(f"api_{endpoint}", secret_key, api_key)
        return lambda func: cb_decorator(sign_decorator(func))
    else:
        return cb_decorator


# HTTPError for API calls
class HTTPError(Exception):
    """HTTP error for API calls"""
    pass


class RequestSigningError(Exception):
    """Request signing error"""
    pass


@dataclass
class RequestSignature:
    """HMAC-SHA256 request signature"""
    signature: str
    timestamp: str
    api_key: str
    algorithm: str = "HMAC-SHA256"
    
    def to_headers(self) -> Dict[str, str]:
        """Convert signature to HTTP headers"""
        return {
            'X-Signature': self.signature,
            'X-Timestamp': self.timestamp,
            'X-API-Key': self.api_key,
            'X-Algorithm': self.algorithm
        }


class RequestSigner:
    """HMAC-SHA256 request signer for MITM protection"""
    
    def __init__(self, secret_key: str, api_key: str):
        """
        Initialize request signer
        
        Args:
            secret_key: Secret key for HMAC signing
            api_key: API key identifier
        """
        self.secret_key = secret_key.encode('utf-8')
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.tolerance_seconds = 300  # 5-minute tolerance for timestamp validation
    
    def _create_canonical_request(self, method: str, url: str, headers: Dict[str, str], 
                                body: str = "", timestamp: str = None) -> str:
        """
        Create canonical request string for signing
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
            timestamp: Request timestamp
            
        Returns:
            Canonical request string
        """
        # Use provided timestamp or generate new one
        if timestamp is None:
            timestamp = str(int(time.time()))
        
        # Parse URL to get path and query
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(url)
        
        # Canonical URI (path)
        canonical_uri = parsed_url.path or '/'
        
        # Canonical query string (sorted)
        query_params = parse_qs(parsed_url.query, keep_blank_values=True)
        canonical_query = '&'.join(f"{k}={v}" for k, v in sorted(query_params.items()) for v in v)
        
        # Canonical headers (sorted, lowercase)
        canonical_headers = []
        for header_name in sorted(headers.keys()):
            header_value = headers[header_name].strip()
            canonical_headers.append(f"{header_name.lower()}:{header_value}")
        
        canonical_headers_str = '\n'.join(canonical_headers) + '\n'
        
        # Signed headers (sorted, lowercase)
        signed_headers = ';'.join(sorted(headers.keys()))
        
        # Hash of payload
        payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
        
        # Build canonical request
        canonical_request = '\n'.join([
            method.upper(),
            canonical_uri,
            canonical_query,
            canonical_headers_str,
            signed_headers,
            payload_hash
        ])
        
        return canonical_request, timestamp, signed_headers
    
    def sign_request(self, method: str, url: str, headers: Dict[str, str] = None, 
                     body: str = "", timestamp: str = None) -> RequestSignature:
        """
        Sign an HTTP request with HMAC-SHA256
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
            timestamp: Request timestamp (for testing)
            
        Returns:
            Request signature
        """
        if headers is None:
            headers = {}
        
        try:
            # Create canonical request
            canonical_request, timestamp, signed_headers = self._create_canonical_request(
                method, url, headers, body, timestamp
            )
            
            # Create string to sign
            string_to_sign = '\n'.join([
                'HMAC-SHA256',
                timestamp,
                hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
            ])
            
            # Calculate signature
            signature = hmac.new(
                self.secret_key,
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            # Base64 encode signature
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            
            self.logger.debug(f"Signed request: {method} {url}")
            
            return RequestSignature(
                signature=signature_b64,
                timestamp=timestamp,
                api_key=self.api_key
            )
            
        except Exception as e:
            self.logger.error(f"Request signing failed: {e}")
            raise RequestSigningError(f"Failed to sign request: {e}")
    
    def verify_signature(self, method: str, url: str, headers: Dict[str, str], 
                        body: str, signature: RequestSignature) -> bool:
        """
        Verify a request signature
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
            signature: Signature to verify
            
        Returns:
            True if signature is valid
        """
        try:
            # Check timestamp tolerance
            current_time = int(time.time())
            request_time = int(signature.timestamp)
            
            if abs(current_time - request_time) > self.tolerance_seconds:
                self.logger.warning(f"Timestamp out of tolerance: {current_time - request_time}s")
                return False
            
            # Recreate canonical request
            canonical_request, _, _ = self._create_canonical_request(
                method, url, headers, body, signature.timestamp
            )
            
            # Recreate string to sign
            string_to_sign = '\n'.join([
                'HMAC-SHA256',
                signature.timestamp,
                hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
            ])
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.secret_key,
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            # Compare with provided signature
            provided_signature = base64.b64decode(signature.signature)
            
            # Constant-time comparison to prevent timing attacks
            return hmac.compare_digest(expected_signature, provided_signature)
            
        except Exception as e:
            self.logger.error(f"Signature verification failed: {e}")
            return False
    
    def add_signature_headers(self, method: str, url: str, headers: Dict[str, str] = None, 
                             body: str = "") -> Dict[str, str]:
        """
        Add signature headers to request
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Existing headers
            body: Request body
            
        Returns:
            Headers with signature added
        """
        if headers is None:
            headers = {}
        
        # Sign the request
        signature = self.sign_request(method, url, headers, body)
        
        # Add signature headers
        signed_headers = headers.copy()
        signed_headers.update(signature.to_headers())
        
        return signed_headers


# Global request signer registry
_request_signers: Dict[str, RequestSigner] = {}


def get_request_signer(name: str, secret_key: str, api_key: str) -> RequestSigner:
    """
    Get or create a request signer by name
    
    Args:
        name: Signer name
        secret_key: Secret key for signing
        api_key: API key identifier
        
    Returns:
        RequestSigner instance
    """
    if name not in _request_signers:
        _request_signers[name] = RequestSigner(secret_key, api_key)
    return _request_signers[name]


def signed_request(name: str, secret_key: str, api_key: str):
    """
    Decorator to add HMAC-SHA256 signing to HTTP requests
    
    Args:
        name: Signer name
        secret_key: Secret key for signing
        api_key: API key identifier
    """
    def decorator(func: Callable) -> Callable:
        signer = get_request_signer(name, secret_key, api_key)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract request details from kwargs or use defaults
            method = kwargs.get('method', 'GET')
            url = kwargs.get('url', '')
            headers = kwargs.get('headers', {})
            body = kwargs.get('body', '')
            
            # Add signature headers
            signed_headers = signer.add_signature_headers(method, url, headers, body)
            kwargs['headers'] = signed_headers
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract request details from kwargs or use defaults
            method = kwargs.get('method', 'GET')
            url = kwargs.get('url', '')
            headers = kwargs.get('headers', {})
            body = kwargs.get('body', '')
            
            # Add signature headers
            signed_headers = signer.add_signature_headers(method, url, headers, body)
            kwargs['headers'] = signed_headers
            
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all circuit breakers"""
    return {name: breaker.statistics for name, breaker in _circuit_breakers.items()}


def reset_all_circuit_breakers():
    """Reset all circuit breakers to closed state"""
    for breaker in _circuit_breakers.values():
        breaker.reset()
