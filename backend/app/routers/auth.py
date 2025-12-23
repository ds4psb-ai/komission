"""
Authentication Router - Google OAuth + JWT
Production-Ready Implementation
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
import httpx

from app.config import settings
from app.database import get_db
from app.models import User

router = APIRouter()

# JWT Config - Use secure secret from settings
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


# ============ Schemas ============

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    k_points: int
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True


class GoogleAuthRequest(BaseModel):
    """Google OAuth token from frontend"""
    credential: str  # Google ID token from Sign-In with Google


class AuthResponse(BaseModel):
    """Response after successful authentication"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# ============ JWT Functions ============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if logged in, None otherwise"""
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ============ Google OAuth ============

async def verify_google_token(credential: str) -> dict:
    """
    Verify Google ID token and return user info.
    Uses Google's tokeninfo endpoint for simplicity.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Verify token with Google
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token"
                )
            
            token_info = response.json()
            
            # Verify audience (client_id)
            if settings.ENVIRONMENT != "development":
                if not settings.GOOGLE_CLIENT_ID:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Google client ID not configured"
                    )
                if token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token was not issued for this application"
                    )
            elif settings.GOOGLE_CLIENT_ID:
                if token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token was not issued for this application"
                    )
            
            return {
                "email": token_info.get("email"),
                "name": token_info.get("name"),
                "picture": token_info.get("picture"),
                "google_id": token_info.get("sub"),
                "email_verified": token_info.get("email_verified") == "true"
            }
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not verify Google token: {str(e)}"
        )


# ============ Endpoints ============

@router.post("/google", response_model=AuthResponse)
async def google_auth(
    auth_request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate with Google Sign-In.
    Creates new user if first time, logs in existing user.
    """
    # Verify Google token
    google_user = await verify_google_token(auth_request.credential)
    
    if not google_user.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not get email from Google account"
        )
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == google_user["email"])
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            email=google_user["email"],
            firebase_uid=f"google_{google_user['google_id']}",
            name=google_user.get("name", google_user["email"].split("@")[0]),
            profile_image=google_user.get("picture"),
            role="user",
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✅ New user created: {user.email}")
    else:
        # Update profile image if changed
        if google_user.get("picture") and user.profile_image != google_user["picture"]:
            user.profile_image = google_user["picture"]
            await db.commit()
    
    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
            k_points=user.k_points,
            profile_image=user.profile_image
        )
    )


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible token login (for development/testing).
    In production, use /google endpoint.
    """
    if settings.ENVIRONMENT != "development" or not settings.ALLOW_DEV_LOGIN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    # Find user by email
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user:
        # Auto-create user only in development
        if settings.ENVIRONMENT == "development":
            user = User(
                email=form_data.username,
                firebase_uid=f"dev_{form_data.username}",
                name=form_data.username.split("@")[0],
                role="user"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found. Please sign in with Google."
            )
    
    # Create token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        k_points=current_user.k_points,
        profile_image=current_user.profile_image
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    Since we use JWT, the actual logout happens on the client side
    by removing the token. This endpoint is for logging/analytics.
    """
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh JWT token for logged-in user"""
    access_token = create_access_token(data={"sub": str(current_user.id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
