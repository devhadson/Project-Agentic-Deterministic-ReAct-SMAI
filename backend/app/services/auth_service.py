from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from requests_oauthlib import OAuth2Session
from typing import List
from sqlalchemy import text
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.services.db_service import get_user_by_username, get_user_by_email, create_google_user

def authenticate_local(db: Session, username: str, password_input: str) -> dict:
    try:
        # 1. Búsqueda de usuario en PostgreSQL
        user = get_user_by_username(db, username)
        
        # 2. Validación de existencia
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El usuario ingresado no existe en el sistema."
            )

        # 3. Validación de hash de contraseña (para cuentas locales)
        if not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El usuario está registrado vía OAuth (Google). Inicie sesión con Google."
            )

        # 4. Verificación de hash de contraseña
        if not verify_password(password_input, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="La contraseña ingresada es incorrecta."
            )

        # 5. Generación de Token JWT tras pasar todas las validaciones
        token = create_access_token({"sub": user.username, "rol": user.rol_nombre})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "rol_nombre": user.rol_nombre
        }

    except HTTPException:
        # Re-elevamos excepciones HTTP ya personalizadas arriba
        raise

    except SQLAlchemyError as db_err:
        # Captura errores específicos de base de datos
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar la base de datos: {str(db_err)}"
        )

    except Exception as e:
        # Captura cualquier otro error no controlado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado durante la autenticación: {str(e)}"
        )

def get_google_auth_url() -> str:
    # 🔍 Verificación preventiva para capturar el error de configuración
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID no está configurado en el archivo .env o en la App Settings.")
    if not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("GOOGLE_CLIENT_SECRET no está configurado en el archivo .env o en la App Settings.")
    if not settings.GOOGLE_REDIRECT_URI:
        raise ValueError("GOOGLE_REDIRECT_URI no está configurado en el archivo .env o en la App Settings.")
    
    scope = ["https://www.googleapis.com/auth/userinfo.email", 
             "https://www.googleapis.com/auth/userinfo.profile", 
             "openid"]
    google = OAuth2Session(
        settings.GOOGLE_CLIENT_ID, 
        scope=scope, 
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    
    auth_url, _ = google.authorization_url(
        'https://accounts.google.com/o/oauth2/v2/auth', 
        access_type="offline",
        prompt="consent"
    )
    return auth_url

def authenticate_google(db: Session, code: str) -> dict:
    try:
        google = OAuth2Session(
            settings.GOOGLE_CLIENT_ID, 
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        # 💡 SE SIMPLIFICA EL INTERCAMBIO DEL TOKEN PASSANDO SOLAMENTE code
        token = google.fetch_token(
            'https://oauth2.googleapis.com/token',
            code=code,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        
        # Obtener información del usuario
        user_info_resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
        if user_info_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo obtener la información del perfil desde Google."
            )
            
        user_info = user_info_resp.json()
        email = user_info.get('email')
        name = user_info.get('name', 'Usuario Google')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta de Google no proporcionó un correo válido."
            )
        
        # Búsqueda o Creación de Usuario en la BD
        user = get_user_by_email(db, email)
        if not user:
            username = email.split('@')[0]
            user = create_google_user(db, username=username, email=email, display_name=name)
            
        # Generar Access Token
        access_token = create_access_token({"sub": user.username, "rol": user.rol_nombre})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email if user.email else "",
            "rol_nombre": user.rol_nombre
        }

    except HTTPException:
        raise
    except SQLAlchemyError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la base de datos durante la autenticación OAuth: {str(db_err)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al procesar la autenticación de Google: {str(e)}"
        )

@staticmethod
def get_user_permissions(db: Session, rol_nombre: str) -> List[str]:
    """
    Consulta la base de datos para obtener los nombres de los módulos
    permitidos asignados al rol especificado.
    """
    query = text("""
        SELECT m.nombre 
        FROM modulos m
        JOIN roles_modulos rm ON m.id = rm.modulo_id
        JOIN roles r ON r.id = rm.rol_id
        WHERE LOWER(r.nombre) = LOWER(:rol)
    """)
    results = db.execute(query, {"rol": rol_nombre}).fetchall()
    # Retorna lista de nombres de módulos
    return [r[0] for r in results]