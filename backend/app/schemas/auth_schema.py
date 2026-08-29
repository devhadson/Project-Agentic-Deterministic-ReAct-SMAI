from pydantic import BaseModel
from typing import List

class LoginRequest(BaseModel):
    username: str
    password: str

class GoogleCallbackRequest(BaseModel):
    code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    display_name: str
    email: str
    rol_nombre: str

class UserResponse(BaseModel):
    username: str
    email: str
    display_name: str
    rol_nombre: str
    auth_provider: str

class UserPermissionsResponse(BaseModel):
    rol: str
    modulos: List[str]