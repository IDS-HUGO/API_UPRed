from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from config import settings
from database import get_db
from models import Usuario, TipoUsuario
from schemas import TokenData

# Configuración de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que la contraseña coincida con el hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str) -> Optional[Usuario]:
    """Autentica un usuario con email y contraseña"""
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return None
    if not verify_password(password, usuario.password_hash):
        return None
    return usuario

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    """Obtiene el usuario actual desde el token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    usuario = db.query(Usuario).filter(Usuario.email == token_data.email).first()
    if usuario is None:
        raise credentials_exception
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    return usuario

async def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """Verifica que el usuario esté activo"""
    if not current_user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

def require_roles(allowed_roles: list[TipoUsuario]):
    """Decorador para requerir roles específicos"""
    def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.tipo_usuario not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción"
            )
        return current_user
    return role_checker

# Funciones auxiliares para verificar permisos

def is_admin(user: Usuario) -> bool:
    """Verifica si el usuario es administrador"""
    return user.tipo_usuario == TipoUsuario.ADMINISTRADOR

def is_docente(user: Usuario) -> bool:
    """Verifica si el usuario es docente"""
    return user.tipo_usuario == TipoUsuario.DOCENTE

def is_alumno(user: Usuario) -> bool:
    """Verifica si el usuario es alumno"""
    return user.tipo_usuario == TipoUsuario.ALUMNO

def can_modify_publicacion(user: Usuario, publicacion_usuario_id: int) -> bool:
    """Verifica si el usuario puede modificar una publicación"""
    return user.id == publicacion_usuario_id or is_admin(user)
