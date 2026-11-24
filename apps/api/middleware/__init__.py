"""
API Middleware Package.
"""
from apps.api.middleware.auth import (
    AuthenticatedUser,
    UserRole,
    create_access_token,
    get_current_user,
    require_roles,
)
from apps.api.middleware.correlation import (
    CorrelationIdMiddleware,
    register_error_handlers,
)

__all__ = [
    "UserRole",
    "AuthenticatedUser",
    "create_access_token",
    "get_current_user",
    "require_roles",
    "CorrelationIdMiddleware",
    "register_error_handlers",
]
