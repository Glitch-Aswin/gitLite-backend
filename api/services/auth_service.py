from supabase import Client
from fastapi import HTTPException
from api.models.auth_schemas import UserSignUp, UserSignIn


class AuthService:
    def __init__(self, db: Client):
        self.db = db
    
    async def login_or_signup(self, user_data: UserSignUp):
        """
        Unified login endpoint - automatically handles both signin and signup.
        If user exists, signs them in. If not, creates a new account.
        """
        try:
            # First, try to sign in
            try:
                response = self.db.auth.sign_in_with_password({
                    "email": user_data.email,
                    "password": user_data.password
                })
                
                if response.user and response.session:
                    # User exists, successful sign in
                    profile = None
                    try:
                        profile_response = self.db.table('users').select('*').eq('id', response.user.id).execute()
                        if profile_response.data:
                            profile = profile_response.data[0]
                    except:
                        pass
                    
                    return {
                        "user": {
                            "id": response.user.id,
                            "email": response.user.email,
                            "full_name": profile.get('full_name') if profile else None,
                            "username": profile.get('username') if profile else None,
                            "created_at": response.user.created_at
                        },
                        "session": {
                            "access_token": response.session.access_token,
                            "refresh_token": response.session.refresh_token,
                            "expires_in": response.session.expires_in,
                            "token_type": "bearer"
                        },
                        "action": "signin"
                    }
            except Exception as signin_error:
                # Sign in failed, likely user doesn't exist - proceed to signup
                pass
            
            # User doesn't exist, create new account
            response = self.db.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "full_name": user_data.full_name,
                        "username": user_data.username
                    }
                }
            })
            
            if not response.user:
                raise HTTPException(status_code=400, detail="Failed to create user")
            
            # Create user profile in public.users table
            if user_data.username or user_data.full_name:
                try:
                    self.db.table('users').insert({
                        'id': response.user.id,
                        'email': user_data.email,
                        'username': user_data.username or user_data.email.split('@')[0],
                        'full_name': user_data.full_name
                    }).execute()
                except Exception as e:
                    print(f"Profile creation warning: {e}")
            
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": user_data.full_name,
                    "username": user_data.username,
                    "created_at": response.user.created_at
                },
                "session": {
                    "access_token": response.session.access_token if response.session else None,
                    "refresh_token": response.session.refresh_token if response.session else None,
                    "expires_in": response.session.expires_in if response.session else None,
                    "token_type": "bearer"
                },
                "action": "signup"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Login/Signup failed: {str(e)}")
    
    async def sign_up(self, user_data: UserSignUp):
        """Register a new user"""
        try:
            # Sign up user with Supabase Auth
            response = self.db.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "full_name": user_data.full_name,
                        "username": user_data.username
                    }
                }
            })
            
            if not response.user:
                raise HTTPException(status_code=400, detail="Failed to create user")
            
            # Create user profile in public.users table
            if user_data.username or user_data.full_name:
                try:
                    self.db.table('users').insert({
                        'id': response.user.id,
                        'email': user_data.email,
                        'username': user_data.username or user_data.email.split('@')[0],
                        'full_name': user_data.full_name
                    }).execute()
                except Exception as e:
                    # If profile creation fails, user is still created in auth
                    print(f"Profile creation warning: {e}")
            
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": user_data.full_name,
                    "username": user_data.username,
                    "created_at": response.user.created_at
                },
                "session": {
                    "access_token": response.session.access_token if response.session else None,
                    "refresh_token": response.session.refresh_token if response.session else None,
                    "expires_in": response.session.expires_in if response.session else None,
                    "token_type": "bearer"
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Sign up failed: {str(e)}")
    
    async def sign_in(self, credentials: UserSignIn):
        """Sign in a user"""
        try:
            response = self.db.auth.sign_in_with_password({
                "email": credentials.email,
                "password": credentials.password
            })
            
            if not response.user or not response.session:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Get user profile
            profile = None
            try:
                profile_response = self.db.table('users').select('*').eq('id', response.user.id).execute()
                if profile_response.data:
                    profile = profile_response.data[0]
            except:
                pass
            
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": profile.get('full_name') if profile else None,
                    "username": profile.get('username') if profile else None,
                    "created_at": response.user.created_at
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_in": response.session.expires_in,
                    "token_type": "bearer"
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Sign in failed: {str(e)}")
    
    async def sign_out(self, access_token: str):
        """Sign out a user"""
        try:
            # Set the session token
            self.db.auth.set_session(access_token, "")
            self.db.auth.sign_out()
            return {"message": "Successfully signed out"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Sign out failed: {str(e)}")
    
    async def refresh_token(self, refresh_token: str):
        """Refresh access token"""
        try:
            response = self.db.auth.refresh_session(refresh_token)
            
            if not response.session:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in,
                "token_type": "bearer"
            }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Token refresh failed: {str(e)}")
    
    async def get_user(self, user_id: str):
        """Get user details"""
        try:
            # Get from auth
            user_response = self.db.auth.admin.get_user_by_id(user_id)
            
            # Get profile
            profile_response = self.db.table('users').select('*').eq('id', user_id).execute()
            profile = profile_response.data[0] if profile_response.data else {}
            
            return {
                "id": user_id,
                "email": user_response.user.email if user_response.user else None,
                "full_name": profile.get('full_name'),
                "username": profile.get('username'),
                "bio": profile.get('bio'),
                "avatar_url": profile.get('avatar_url'),
                "created_at": profile.get('created_at')
            }
            
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"User not found: {str(e)}")
    
    async def update_user_profile(self, user_id: str, update_data: dict):
        """Update user profile"""
        try:
            response = self.db.table('users').update(update_data).eq('id', user_id).execute()
            
            if not response.data:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Profile update failed: {str(e)}")
    
    async def request_password_reset(self, email: str):
        """Request password reset email"""
        try:
            self.db.auth.reset_password_email(email)
            return {"message": "Password reset email sent"}
        except Exception as e:
            # Don't reveal if email exists
            return {"message": "If the email exists, a password reset link will be sent"}
    
    async def update_password(self, access_token: str, new_password: str):
        """Update user password"""
        try:
            self.db.auth.set_session(access_token, "")
            response = self.db.auth.update_user({"password": new_password})
            
            if not response.user:
                raise HTTPException(status_code=400, detail="Failed to update password")
            
            return {"message": "Password updated successfully"}
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Password update failed: {str(e)}")
