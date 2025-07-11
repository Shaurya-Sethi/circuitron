# Connection and Network Error Analysis Report

## Executive Summary

After conducting a thorough review of the Circuitron codebase, I've identified several critical issues in connection handling, network error management, and Docker container lifecycle management. The "Fatal error: Network operation timed out" errors are likely caused by a combination of inadequate timeout handling, race conditions in container startup, insufficient retry mechanisms, and poor error propagation.

## Critical Issues Identified

### 1. **Inconsistent Timeout Values and Poor Coordination**

**Problem:** Multiple timeout values across different components create race conditions:
- MCP connection timeout: 10s (production) / 15s (Docker)
- MCP client session timeout: same as connection timeout
- MCP SSE read timeout: 2x connection timeout (20s/30s)
- Network operation timeout: 60s (global setting)
- Health check timeout: 5s
- MCP startup max attempts: 20s (1s intervals)

**Root Cause:** The MCP container might start successfully but the server inside takes longer to initialize than the connection timeouts allow.

### 2. **Inadequate MCP Server Startup Synchronization**

**Current Flow Issues:**
```python
# mcp_server.py - start() function
for _ in range(max_attempts):
    time.sleep(1)  # Only 1 second wait
    if is_running(url):  # 5 second timeout health check
        return True
```

**Problems:**
- Only waits 1 second between checks - insufficient for container/server initialization
- Health check has 5s timeout, but only checks once per second
- No exponential backoff or progressive timeout increases
- Container status check doesn't validate actual server health

### 3. **Race Conditions in Container Management**

**Issue in DockerSession.start():**
```python
if status.lower().startswith("up"):
    if self._health_check():
        self.started = True
        return
    self._run(["docker", "rm", "-f", self.container_name], check=True)
```

**Problems:**
- Container marked as "up" doesn't mean application is ready
- Health check failure immediately removes container - too aggressive
- No wait time for application initialization after container start

### 4. **Poor Error Handling Chain**

**MCPManager Connection Logic:**
```python
async def _connect_server_with_timeout(self) -> None:
    for attempt in range(3):
        try:
            await asyncio.wait_for(self._server.connect(), timeout=20.0)
            return
        except Exception as exc:
            if attempt == 2:
                logging.warning("Failed to connect MCP server %s: %s", self._server.name, exc)
            else:
                await asyncio.sleep(2**attempt)  # Only 2^0=1s, 2^1=2s waits
```

**Issues:**
- Only 3 attempts with minimal backoff
- 20s timeout per attempt, but no coordination with container startup
- Doesn't check if container is actually running before attempting connection
- Warning logged but no exception raised - silently fails

### 5. **Network Error Detection Logic Flaws**

**In guardrails.py and debug.py:**
```python
except asyncio.TimeoutError:
    raise PipelineError("Network operation timed out. Please check your connection and try again.")
except (httpx.HTTPError, openai.OpenAIError) as exc:
    if not is_connected():
        raise PipelineError("Internet connection lost. Please check your connection and try again.")
```

**Problems:**
- `asyncio.TimeoutError` doesn't necessarily indicate network issues
- Could be MCP server unresponsiveness, container issues, or actual network problems
- `is_connected()` only checks OpenAI API, not MCP server
- Misleading error messages directing users to check internet connection

### 6. **Missing Health Check Coordination**

**Current health check logic:**
```python
def _health_check(url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{url}/sse", timeout=5):
            pass
        return True
    except Exception:
        return False
```

**Issues:**
- Generic exception catching hides specific error types
- No distinction between connection refused, timeout, or other errors
- 5-second timeout may be insufficient for slow container startups
- No retry mechanism within health checks

## Proposed Solutions

### 1. **Implement Coordinated Startup with Proper Timeouts**

```python
# Enhanced MCP server startup
async def start_with_proper_coordination() -> bool:
    """Start MCP server with coordinated timeout handling."""
    url = os.getenv("MCP_URL", "http://localhost:8051")
    
    # Check if already running
    if await async_health_check(url, timeout=10):
        return True
    
    # Start container
    if not _start_container():
        return False
    
    # Wait for container to be ready with progressive timeouts
    container_ready = await _wait_for_container_ready(max_wait=30)
    if not container_ready:
        return False
    
    # Wait for MCP server to be ready with progressive timeouts
    server_ready = await _wait_for_mcp_server_ready(url, max_wait=60)
    return server_ready

async def _wait_for_mcp_server_ready(url: str, max_wait: int = 60) -> bool:
    """Wait for MCP server with exponential backoff."""
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < max_wait:
        wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
        await asyncio.sleep(wait_time)
        
        if await async_health_check(url, timeout=min(5 + attempt, 15)):
            logging.info("MCP server ready after %.1fs", time.time() - start_time)
            return True
        
        attempt += 1
        logging.debug("MCP server not ready yet (attempt %d), waiting %.1fs", attempt, wait_time)
    
    logging.error("MCP server failed to become ready within %ds", max_wait)
    return False
```

### 2. **Enhanced Health Checking with Error Classification**

```python
async def async_health_check(url: str, timeout: float = 10) -> bool:
    """Enhanced health check with proper error handling."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.head(f"{url}/sse")
            return response.status_code < 400
    except httpx.ConnectError:
        logging.debug("MCP server connection refused - server not ready")
        return False
    except httpx.TimeoutException:
        logging.debug("MCP server health check timeout")
        return False
    except Exception as exc:
        logging.warning("Unexpected health check error: %s", exc)
        return False

def classify_connection_error(exc: Exception) -> str:
    """Classify connection errors for better user feedback."""
    if isinstance(exc, httpx.ConnectError):
        return "MCP server not reachable - container may be starting"
    elif isinstance(exc, httpx.TimeoutException):
        return "MCP server response timeout - server may be overloaded"
    elif isinstance(exc, asyncio.TimeoutError):
        return "Operation timeout - may indicate resource constraints"
    else:
        return f"Unexpected connection error: {type(exc).__name__}"
```

### 3. **Improved Error Handling with Proper Classification**

```python
class ConnectionManager:
    """Centralized connection management with proper error handling."""
    
    async def ensure_mcp_connection(self) -> bool:
        """Ensure MCP server is running and connected."""
        # 1. Check container status
        container_status = self._get_container_status()
        if container_status != "running":
            if not await self._start_and_wait_for_container():
                raise PipelineError("Failed to start MCP container")
        
        # 2. Verify MCP server health
        if not await self._verify_mcp_health():
            raise PipelineError("MCP server failed health check")
        
        # 3. Test actual connection
        if not await self._test_mcp_connection():
            raise PipelineError("Failed to establish MCP connection")
        
        return True
    
    async def _handle_connection_error(self, exc: Exception) -> None:
        """Handle connection errors with proper classification."""
        error_type = classify_connection_error(exc)
        
        # Check if it's a container issue
        container_status = self._get_container_status()
        if container_status != "running":
            raise PipelineError(f"MCP container not running: {container_status}")
        
        # Check if it's a network issue
        if not await self._check_network_connectivity():
            raise PipelineError("Network connectivity issue detected")
        
        # Otherwise, it's likely an MCP server issue
        raise PipelineError(f"MCP server error: {error_type}")
```

### 4. **Robust Container Lifecycle Management**

```python
class EnhancedDockerSession:
    """Enhanced Docker session with proper lifecycle management."""
    
    async def start(self) -> None:
        """Start container with proper health verification."""
        with self._lock:
            # Clean up any stale containers
            await self._cleanup_stale_containers()
            
            # Check if container exists and is healthy
            if await self._is_container_healthy():
                self.started = True
                return
            
            # Remove unhealthy container
            await self._remove_container_if_exists()
            
            # Start new container
            await self._start_new_container()
            
            # Wait for container to be ready
            if not await self._wait_for_container_ready():
                raise RuntimeError("Container failed to become ready")
            
            self.started = True
    
    async def _wait_for_container_ready(self, max_wait: int = 60) -> bool:
        """Wait for container to be ready with exponential backoff."""
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < max_wait:
            if await self._health_check():
                logging.info("Container ready after %.1fs", time.time() - start_time)
                return True
            
            wait_time = min(2 ** attempt, 5)  # Cap at 5 seconds
            await asyncio.sleep(wait_time)
            attempt += 1
        
        return False
    
    async def _health_check(self) -> bool:
        """Enhanced health check with proper error handling."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "exec", self.container_name, "python3", "-c", "import skidl",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            return proc.returncode == 0
        except asyncio.TimeoutError:
            logging.debug("Container health check timeout")
            return False
        except Exception as exc:
            logging.debug("Container health check failed: %s", exc)
            return False
```

### 5. **Configuration Management for Timeouts**

```python
@dataclass
class ConnectionSettings:
    """Centralized connection and timeout settings."""
    
    # Container startup timeouts
    container_start_timeout: int = 30
    container_health_check_timeout: int = 10
    container_max_startup_attempts: int = 3
    
    # MCP server timeouts
    mcp_startup_timeout: int = 60
    mcp_health_check_timeout: int = 15
    mcp_connection_timeout: int = 20
    mcp_max_connection_attempts: int = 5
    
    # Network operation timeouts
    network_operation_timeout: int = 120  # Increased from 60
    api_request_timeout: int = 30
    
    # Retry settings
    initial_retry_delay: float = 1.0
    max_retry_delay: float = 10.0
    retry_exponential_base: float = 2.0
    
    def get_progressive_timeout(self, attempt: int, base_timeout: int) -> int:
        """Get progressively longer timeout for retries."""
        return min(base_timeout * (self.retry_exponential_base ** attempt), base_timeout * 3)
```

### 6. **Enhanced Error Propagation and User Feedback**

```python
async def run_with_enhanced_error_handling(
    prompt: str,
    show_reasoning: bool = False,
    retries: int = 0,
    output_dir: str | None = None,
) -> CodeGenerationOutput | None:
    """Run pipeline with enhanced error handling and user feedback."""
    
    connection_manager = ConnectionManager()
    
    try:
        # Ensure all services are ready before starting
        await connection_manager.ensure_all_services_ready()
        
        return await pipeline(prompt, show_reasoning=show_reasoning, output_dir=output_dir)
        
    except PipelineError as exc:
        # Pipeline errors are user-facing and should be shown as-is
        print(f"Pipeline error: {exc}")
        raise
        
    except asyncio.TimeoutError as exc:
        # Classify timeout errors properly
        error_context = await connection_manager.diagnose_timeout_error()
        raise PipelineError(f"Operation timeout: {error_context}") from exc
        
    except (httpx.HTTPError, openai.OpenAIError) as exc:
        # Network/API errors need diagnosis
        diagnosis = await connection_manager.diagnose_network_error(exc)
        raise PipelineError(f"Network error: {diagnosis}") from exc
        
    except Exception as exc:
        # Unexpected errors should be logged with context
        logging.error("Unexpected pipeline error", exc_info=True)
        context = await connection_manager.get_system_context()
        raise PipelineError(f"Unexpected error: {exc}. System context: {context}") from exc
```

## Implementation Priority

1. **High Priority (Immediate Fix)**:
   - Fix MCP server startup coordination with proper timeouts
   - Implement enhanced health checking with error classification
   - Add progressive timeout handling

2. **Medium Priority (Next Release)**:
   - Refactor Docker session management
   - Centralize connection management
   - Improve error message clarity

3. **Low Priority (Future Enhancement)**:
   - Add comprehensive monitoring and diagnostics
   - Implement connection pooling and failover
   - Add configuration management UI

## Testing Strategy

1. **Integration Tests**:
   - Container startup under various timing conditions
   - Network interruption scenarios
   - Resource constraint simulation

2. **Stress Tests**:
   - Rapid pipeline execution cycles
   - Concurrent pipeline runs
   - Memory and CPU pressure scenarios

3. **Error Scenario Tests**:
   - Docker daemon failures
   - Network timeouts at various stages
   - Container resource exhaustion

## Conclusion

The current network timeout errors are primarily caused by inadequate coordination between container startup, server initialization, and connection establishment. The proposed solutions address these issues through:

1. **Coordinated timing** with progressive timeouts
2. **Enhanced error classification** for better debugging
3. **Robust health checking** with proper retry mechanisms
4. **Centralized connection management** for consistency

Implementing these changes should significantly reduce the "Fatal error: Network operation timed out" issues and provide better visibility into the actual root causes when problems do occur.
