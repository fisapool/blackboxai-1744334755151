from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Security configurations
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# TODO: Move to environment variables
SECRET_KEY = "your-secret-key-here"  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # TODO: Implement user lookup from database
    user = {"username": username, "is_active": True}
    if user is None:
        raise credentials_exception
    return user

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        # TODO: Implement actual user authentication against database
        user = {
            "username": form_data.username,
            "hashed_password": pwd_context.hash(form_data.password)
        }
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user["username"]})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing login request"
        )

@router.get("/me")
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current user information
    """
    return current_user

@router.post("/register")
async def register_user(username: str, password: str) -> Dict[str, Any]:
    """
    Register a new user
    """
    try:
        # TODO: Implement actual user registration in database
        hashed_password = pwd_context.hash(password)
        return {
            "username": username,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user"
        )

@router.put("/me/update")
async def update_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
    new_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update current user information
    """
    try:
        # TODO: Implement actual user update in database
        if new_password:
            hashed_password = pwd_context.hash(new_password)
        
        return {
            "username": current_user["username"],
            "updated_at": datetime.utcnow().isoformat(),
            "message": "User updated successfully"
        }
    except Exception as e:
        logger.error(f"Update user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user information"
        )
