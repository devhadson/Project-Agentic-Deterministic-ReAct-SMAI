import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.core.config import settings

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    
    # Convierte a bytes ambos valores de forma segura
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
    
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Asegúrate de que SECRET_KEY sea un string válido
    encoded_jwt = jwt.encode(to_encode, str(settings.SECRET_KEY), algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None