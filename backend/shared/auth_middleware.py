"""
Shared JWT Authentication Middleware
Can be used by all microservices to verify JWT tokens
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional

# These should match the auth service settings
SECRET_KEY = "your-secret-key-change-this-in-production-2024"
ALGORITHM = "HS256"

security = HTTPBearer()

class JWTBearer:
    """JWT Bearer token validator"""
    
    def __init__(self, required_roles: Optional[list] = None):
        self.required_roles = required_roles or []
    
    async def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        """Verify JWT token and return payload"""
        token = credentials.credentials
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Verify token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Check if role is required and matches
            if self.required_roles:
                user_role = payload.get("role")
                if user_role not in self.required_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access forbidden. Required roles: {', '.join(self.required_roles)}"
                    )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Dependency for any authenticated user
get_current_user = JWTBearer()

# Dependency for clinic admin only
get_clinic_admin = JWTBearer(required_roles=["clinic_admin"])

# Dependency for GCF coordinator only
get_gcf_coordinator = JWTBearer(required_roles=["gcf_coordinator"])

# Dependency for super admin only
get_super_admin = JWTBearer(required_roles=["super_admin"])

# Dependency for both clinic admin and GCF coordinator
get_any_user = JWTBearer(required_roles=["clinic_admin", "gcf_coordinator"])

# Dependency for all user types (including super admin)
get_any_authenticated_user = JWTBearer(required_roles=["clinic_admin", "gcf_coordinator", "super_admin"])
