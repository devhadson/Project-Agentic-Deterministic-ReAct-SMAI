from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import Query
from app.core.database import get_db
from app.schemas.auth_schema import LoginRequest, GoogleCallbackRequest, TokenResponse, UserPermissionsResponse
from app.services.auth_service import authenticate_local, get_google_auth_url, authenticate_google, get_user_permissions

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login_local(payload: LoginRequest, db: Session = Depends(get_db)):
    # La función authenticate_local maneja los errores y responde con mensajes personalizados
    return authenticate_local(db, payload.username, payload.password)

@router.get("/google/url")
def get_google_url():
    return {"url": get_google_auth_url()}

@router.post("/google/callback", response_model=TokenResponse)
def google_callback(payload: GoogleCallbackRequest, db: Session = Depends(get_db)):
    try:
        return authenticate_google(db, payload.code)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error en callback Google: {str(e)}")

@router.get(
    "/permissions", 
    response_model=UserPermissionsResponse, 
    status_code=status.HTTP_200_OK,
    summary="Obtener módulos/permisos por rol"
)
def get_permissions_by_role(
    rol: str = Query(..., description="Nombre del rol del usuario (paciente, enfermería, médico, administrador)"),
    db: Session = Depends(get_db)
):
    try:
        modulos = get_user_permissions(db, rol)
        return {"rol": rol, "modulos": modulos}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando permisos en base de datos: {str(e)}"
        )