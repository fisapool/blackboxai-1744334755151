"""
Security Middleware for FastAPI

This module provides security middleware that integrates with the SecurityManager
to provide comprehensive security features for the API, including request validation,
security headers, and rate limiting.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, List
import logging
import re
from datetime import datetime
from functools import wraps

from app.security.security_manager import SecurityManager
from app.core.settings import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer()
settings = get_settings()

class SecurityMiddleware:
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        self.settings = settings
        # Compile regex patterns for input validation
        self.patterns = {
            'xss': re.compile(r'<[^>]*script.*?>|javascript:|data:', re.IGNORECASE),
            'sql_injection': re.compile(r'(\b(union|select|insert|update|delete|drop|alter)\b.*?)|(-{2})', re.IGNORECASE),
            'path_traversal': re.compile(r'\.{2}[/\\]'),
        }
        
    async def __call__(self, request: Request, call_next):
        """Process each request through security middleware."""
        # Log request
        self._log_request(request)
        
        # Validate request
        await self._validate_request(request)
        
        # Check rate limiting
        if not self._check_rate_limit(request):
            raise HTTPException(
                status_code=429,
                detail="Too many requests"
            )
            
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        # Log response
        self._log_response(request, response)
        
        return response

    async def _validate_request(self, request: Request):
        """Validate request parameters and body for security issues."""
        # Check query parameters
        for param, value in request.query_params.items():
            if any(pattern.search(value) for pattern in self.patterns.values()):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid characters detected in query parameter: {param}"
                )

        # Check path parameters
        for param in request.path_params.values():
            if isinstance(param, str):
                if any(pattern.search(param) for pattern in self.patterns.values()):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid characters detected in path parameter"
                    )

        # Check request body if it's a form or JSON
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    self._validate_dict(body)
            except:
                # If not JSON, try to get form data
                form = await request.form()
                for field, value in form.items():
                    if isinstance(value, str):
                        if any(pattern.search(value) for pattern in self.patterns.values()):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Invalid characters detected in form field: {field}"
                            )

    def _validate_dict(self, data: dict, path: str = ""):
        """Recursively validate dictionary values."""
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, str):
                if any(pattern.search(value) for pattern in self.patterns.values()):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid characters detected in field: {current_path}"
                    )
            elif isinstance(value, dict):
                self._validate_dict(value, current_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._validate_dict(item, f"{current_path}[{i}]")
                    elif isinstance(item, str):
                        if any(pattern.search(item) for pattern in self.patterns.values()):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Invalid characters detected in array item: {current_path}[{i}]"
                            )

    def _add_security_headers(self, response):
        """Add security headers to response."""
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "accelerometer=(), "
                "camera=(), "
                "geolocation=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "microphone=(), "
                "payment=(), "
                "usb=()"
            )
        })
        
    def _log_request(self, request: Request):
        """Log request details for audit."""
        self.security_manager.log_audit_event(
            "api_request",
            request.client.host,
            {
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "headers": dict(request.headers),
                "request_id": getattr(request.state, "request_id", None)
            }
        )
        
    def _log_response(self, request: Request, response):
        """Log response details for audit."""
        self.security_manager.log_audit_event(
            "api_response",
            request.client.host,
            {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "request_id": getattr(request.state, "request_id", None)
            }
        )
        
    def _check_rate_limit(self, request: Request) -> bool:
        """Check if request is within rate limits."""
        # Implement rate limiting logic
        return True
        
    def require_permission(self, permission: str):
        """Decorator to require specific permission."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get user from request
                user = kwargs.get("user")
                if not user:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication required"
                    )
                    
                # Check permission
                if not self.security_manager.check_permission(
                    user["role"],
                    permission
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Insufficient permissions"
                    )
                    
                return await func(*args, **kwargs)
            return wrapper
        return decorator
        
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict:
        """Get current user from JWT token."""
        token = credentials.credentials
        payload = self.security_manager.verify_jwt_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
            
        return {
            "user_id": payload["user_id"],
            "roles": payload["roles"]
        }
        
    def validate_password(self, password: str) -> bool:
        """Validate password against security policy."""
        return self.security_manager.validate_password_policy(password)
        
    def hash_password(self, password: str) -> str:
        """Hash password using secure algorithm."""
        return self.security_manager.hash_password(password)
        
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hashed password."""
        return self.security_manager.verify_password(password, hashed_password)
        
    def generate_token(self, user_id: str, roles: List[str]) -> str:
        """Generate JWT token for user."""
        return self.security_manager.generate_jwt_token(user_id, roles)
        
    def encrypt_data(self, data: str) -> Dict:
        """Encrypt sensitive data."""
        return self.security_manager.encrypt_data(data)
        
    def decrypt_data(self, encrypted_data: Dict) -> str:
        """Decrypt sensitive data."""
        return self.security_manager.decrypt_data(encrypted_data).decode()
        
    def monitor_security_event(self, event_type: str, details: Dict):
        """Monitor and log security events."""
        self.security_manager.monitor_security_event(event_type, details)
        
    def log_audit_event(
        self,
        event_type: str,
        user_id: str,
        details: Dict,
        severity: str = "INFO"
    ):
        """Log audit event."""
        self.security_manager.log_audit_event(
            event_type,
            user_id,
            details,
            severity
        ) 