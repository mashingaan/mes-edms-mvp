from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to capture IP address for audit logging."""
    
    async def dispatch(self, request: Request, call_next):
        # Extract IP address
        ip_address = self._get_client_ip(request)
        
        # Store in request state for access in route handlers
        request.state.ip = ip_address
        
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Get client IP from X-Forwarded-For header or request client."""
        # Check X-Forwarded-For header first (for proxied requests)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the list (original client)
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return None

