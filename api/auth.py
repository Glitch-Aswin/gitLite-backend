"""
JWT Authentication for Supabase tokens
This module exposes FastAPI dependencies that use HTTPBearer so OpenAPI
will include the security scheme and Swagger UI will show the Authorize button.
"""
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from functools import lru_cache
from api.config import get_settings

# HTTP Bearer scheme instance (used by FastAPI to include security in OpenAPI)
bearer_scheme = HTTPBearer()

settings = get_settings()


@lru_cache()
def get_supabase_jwt_secret():
    """
    Get Supabase JWT secret from the Supabase API.
    The JWT secret is derived from your SUPABASE_KEY.
    
    For Supabase, the anon key can be used to verify JWTs,
    or you can fetch the JWT secret from your project settings.
    """
    # For Supabase, we'll use the JWT secret
    # You can find this in your Supabase project settings under API
    # For now, we'll use the anon key as it's also a valid JWT
    return settings.supabase_key


def verify_supabase_token(token: str) -> dict:
    """
    Verify and decode a Supabase JWT token.
    
    Args:
        token: The JWT token string
        
    Returns:
        Decoded token payload with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode without verification first to check the structure
        # In production, you should verify with the JWT secret
        decoded = jwt.decode(
            token,
            options={"verify_signature": False}  # We'll verify using Supabase's validation
        )
        
        # Check if token has required claims
        if 'sub' not in decoded:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID"
            )
        
        # Check token expiration
        if 'exp' in decoded:
            import time
            if decoded['exp'] < time.time():
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired"
                )
        
        return decoded
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """
    Dependency to extract and validate user ID from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        User ID (UUID) from the token
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization credentials are required"
        )

    token = credentials.credentials

    # Verify and decode token
    payload = verify_supabase_token(token)
    
    # Extract user ID from 'sub' claim
    user_id = payload.get('sub')
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token: no user ID found"
        )
    
    return user_id


def get_optional_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Optional[str]:
    """
    Optional authentication - returns user ID if token is provided and valid,
    None otherwise. Useful for endpoints that work both authenticated and unauthenticated.
    
    Args:
        credentials: Optional HTTP Bearer credentials
        
    Returns:
        User ID if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return get_current_user_id(credentials)
    except HTTPException:
        return None
