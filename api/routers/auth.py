from fastapi import APIRouter, Depends, HTTPException
from api.database import get_db
from api.models.auth_schemas import (
    UserSignUp,
    UserSignIn,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordUpdateRequest
)
from api.services.auth_service import AuthService
from api.auth import get_current_user_id

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=dict)
async def login(
    user_data: UserSignUp,
    db = Depends(get_db)
):
    """
    Unified login endpoint - automatically handles both signin and signup.
    
    If user exists, signs them in. If not, creates a new account automatically.
    
    - **email**: Valid email address
    - **password**: Strong password (min 6 characters)
    - **username**: Optional username (required for new signups, will use email prefix if not provided)
    - **full_name**: Optional full name
    
    Returns:
    - User information
    - Access token and refresh token
    - Action taken ("signin" or "signup")
    """
    service = AuthService(db)
    return await service.login_or_signup(user_data)


# @router.post("/signup", response_model=dict)
# async def sign_up(
#     user_data: UserSignUp,
#     db = Depends(get_db)
# ):
#     """
#     Register a new user.
    
#     - **email**: Valid email address
#     - **password**: Strong password (min 6 characters)
#     - **username**: Optional username (will use email prefix if not provided)
#     - **full_name**: Optional full name
#     """
#     service = AuthService(db)
#     return await service.sign_up(user_data)


# @router.post("/signin", response_model=dict)
# async def sign_in(
#     credentials: UserSignIn,
#     db = Depends(get_db)
# ):
#     """
#     Sign in with email and password.
    
#     Returns access token, refresh token, and user information.
#     """
#     service = AuthService(db)
#     return await service.sign_in(credentials)


@router.post("/signout")
async def sign_out(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """
    Sign out the current user.
    
    Requires authentication.
    """
    service = AuthService(db)
    # Note: Supabase handles token invalidation
    return {"message": "Successfully signed out"}


@router.post("/refresh")
async def refresh_token(
    token_data: RefreshTokenRequest,
    db = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: The refresh token received during sign in
    """
    service = AuthService(db)
    return await service.refresh_token(token_data.refresh_token)


@router.get("/me", response_model=dict)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """
    Get current authenticated user's profile.
    
    Requires authentication.
    """
    service = AuthService(db)
    return await service.get_user(user_id)


@router.put("/me", response_model=dict)
async def update_profile(
    update_data: dict,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """
    Update current user's profile.
    
    Requires authentication.
    
    Allowed fields: username, full_name, bio, avatar_url
    """
    # Filter allowed fields
    allowed_fields = ['username', 'full_name', 'bio', 'avatar_url']
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if not filtered_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    service = AuthService(db)
    return await service.update_user_profile(user_id, filtered_data)


@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db = Depends(get_db)
):
    """
    Request a password reset email.
    
    - **email**: Email address to send reset link to
    """
    service = AuthService(db)
    return await service.request_password_reset(reset_data.email)


# @router.post("/password-update")
# async def update_password(
#     password_data: PasswordUpdateRequest,
#     user_id: str = Depends(get_current_user_id),
#     db = Depends(get_db)
# ):
#     """
#     Update password for authenticated user.
    
#     Requires authentication.
    
#     - **password**: New password
#     """
#     # Get access token from the current session
#     # This is a simplified version - in production, you'd extract it properly
#     service = AuthService(db)
#     return {"message": "Password update endpoint - use Supabase client directly for password updates"}


@router.get("/user/{user_id}", response_model=dict)
async def get_user_by_id(
    user_id: str,
    db = Depends(get_db)
):
    """
    Get public user profile by user ID.
    
    Does not require authentication.
    """
    service = AuthService(db)
    user = await service.get_user(user_id)
    
    # Return only public fields
    return {
        "id": user["id"],
        "username": user.get("username"),
        "full_name": user.get("full_name"),
        "bio": user.get("bio"),
        "avatar_url": user.get("avatar_url")
    }
