"""
Authentication & RBAC Authorization Middleware (Clean Architecture).
Implements role-based access control enforcing:
- RADIOLOGY_DIRECTOR
- REPORTING_RADIOLOGIST
- RADIOLOGY_RESIDENT
- RADIOGRAPHER
- COORDINATOR
- ADMINISTRATOR
"""
from datetime import datetime, timedelta, timezone
from enum import Enum
import logging
from typing import Annotated, Any, Dict, List, Optional
import uuid

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel, Field

from core.infrastructure.config import settings

logger = logging.getLogger("sims_radiology.api.auth")

security_scheme = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    RADIOLOGY_DIRECTOR = "RADIOLOGY_DIRECTOR"
    REPORTING_RADIOLOGIST = "REPORTING_RADIOLOGIST"
    RADIOLOGY_RESIDENT = "RADIOLOGY_RESIDENT"
    RADIOGRAPHER = "RADIOGRAPHER"
    COORDINATOR = "COORDINATOR"
    ADMINISTRATOR = "ADMINISTRATOR"


class TokenPayload(BaseModel):
    sub: str
    role: UserRole
    name: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    exp: datetime


class AuthenticatedUser(BaseModel):
    user_id: str
    role: UserRole
    name: str = "SIMS Clinical Staff"
    email: str = "staff@hospital.sims.org"
    license_number: Optional[str] = None


def create_access_token(
    user_id: str,
    role: UserRole,
    name: Optional[str] = None,
    email: Optional[str] = None,
    license_number: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate signed JWT access token containing subject and RBAC role."""
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = now + delta
    payload = {
        "sub": user_id,
        "role": role.value,
        "name": name or user_id,
        "email": email or f"{user_id.lower()}@sims.hospital.org",
        "license_number": license_number,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.SECURITY_ALGORITHM)
    return token


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_license_number: Optional[str] = Header(None, alias="X-License-Number"),
) -> AuthenticatedUser:
    """
    Extract and authenticate current user from Bearer JWT token.
    Supports development/test header fallback (X-User-Role, X-User-Id) when token is absent.
    """
    # 1. Bearer Token Verification
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.SECURITY_ALGORITHM],
            )
            user_id = payload.get("sub")
            role_str = payload.get("role")
            if not user_id or not role_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token claims: missing subject or role",
                )
            role = UserRole(role_str)
            return AuthenticatedUser(
                user_id=user_id,
                role=role,
                name=payload.get("name", user_id),
                email=payload.get("email", f"{user_id}@sims.hospital.org"),
                license_number=payload.get("license_number"),
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired",
            )
        except (jwt.InvalidTokenError, ValueError) as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {err}",
            )

    # 2. Development/Testing Header Fallback
    if x_user_role:
        try:
            role = UserRole(x_user_role.upper())
            user_id = x_user_id or f"USER-{x_user_role.upper()}"
            return AuthenticatedUser(
                user_id=user_id,
                role=role,
                name=f"Dr. {user_id}",
                email=f"{user_id.lower()}@sims.hospital.org",
                license_number=x_license_number or ("RAD-LIC-12345" if "RADIOLOGIST" in role.value or "DIRECTOR" in role.value else None),
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid X-User-Role specified: '{x_user_role}'",
            )

    # If neither Bearer token nor role header is provided:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials. Bearer token required.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_roles(*allowed_roles: UserRole):
    """
    FastAPI dependency factory enforcing server-side RBAC permissions.
    Raises HTTP 403 Forbidden if user's role is not among allowed_roles.
    """
    async def role_checker(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]
    ) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"RBAC DENIED: User '{current_user.user_id}' with role '{current_user.role.value}' "
                f"attempted to access endpoint requiring {[r.value for r in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Forbidden: User role '{current_user.role.value}' lacks required permissions. "
                    f"Allowed roles: {[r.value for r in allowed_roles]}"
                ),
            )
        return current_user

    return role_checker
