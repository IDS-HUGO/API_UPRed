from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from database import get_db
from models import Usuario, DominioCorreo, TipoUsuario
from schemas import (
    UsuarioCreate, UsuarioResponse, Token, UsuarioLogin, Message
)
from auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user
)
from config import settings

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

def validar_dominio_correo(db: Session, email: str, tipo_usuario: TipoUsuario) -> bool:
    """Valida que el dominio del correo esté permitido para el tipo de usuario"""
    # Administradores no requieren validación de dominio
    if tipo_usuario == TipoUsuario.ADMINISTRADOR:
        return True
    
    # Extraer dominio del email
    dominio = "@" + email.split("@")[1]
    
    # Buscar si el dominio está registrado para este tipo de usuario
    dominio_permitido = db.query(DominioCorreo).filter(
        DominioCorreo.dominio == dominio,
        DominioCorreo.tipo_usuario == tipo_usuario,
        DominioCorreo.activo == True
    ).first()
    
    return dominio_permitido is not None

@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario en el sistema"""
    
    # Verificar si el email ya existe
    existing_user = db.query(Usuario).filter(Usuario.email == usuario_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )
    
    # Validar dominio de correo para ALUMNO y DOCENTE
    if usuario_data.tipo_usuario != TipoUsuario.ADMINISTRADOR:
        if not validar_dominio_correo(db, usuario_data.email, usuario_data.tipo_usuario):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El dominio del correo no está permitido para usuarios de tipo {usuario_data.tipo_usuario}"
            )
    
    # Validar que ALUMNO tenga matrícula
    if usuario_data.tipo_usuario == TipoUsuario.ALUMNO and not usuario_data.matricula:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los alumnos deben proporcionar su matrícula"
        )
    
    # Validar que DOCENTE tenga número de empleado
    if usuario_data.tipo_usuario == TipoUsuario.DOCENTE and not usuario_data.numero_empleado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los docentes deben proporcionar su número de empleado"
        )
    
    # Validar que tenga carrera (excepto ADMINISTRADOR)
    if usuario_data.tipo_usuario != TipoUsuario.ADMINISTRADOR and not usuario_data.carrera_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe seleccionar una carrera"
        )
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(usuario_data.password)
    new_user = Usuario(
        nombre=usuario_data.nombre,
        apellido=usuario_data.apellido,
        email=usuario_data.email,
        password_hash=hashed_password,
        tipo_usuario=usuario_data.tipo_usuario,
        carrera_id=usuario_data.carrera_id,
        matricula=usuario_data.matricula,
        numero_empleado=usuario_data.numero_empleado,
        activo=True,
        verificado=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def login(usuario_login: UsuarioLogin, db: Session = Depends(get_db)):
    """Inicia sesión y retorna un token JWT"""
    
    # Autenticar usuario
    usuario = authenticate_user(db, usuario_login.email, usuario_login.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el usuario esté activo
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacta al administrador."
        )
    
    # Crear token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.email, "tipo": usuario.tipo_usuario.value},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": usuario
    }

@router.post("/login/oauth2", response_model=Token)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login compatible con OAuth2 (para documentación automática de FastAPI)"""
    
    usuario = authenticate_user(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.email, "tipo": usuario.tipo_usuario.value},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": usuario
    }

@router.get("/me", response_model=UsuarioResponse)
def get_current_user_info(current_user: Usuario = Depends(get_current_user)):
    """Obtiene la información del usuario autenticado"""
    return current_user

@router.get("/dominios-correo")
def get_dominios_correo(db: Session = Depends(get_db)):
    """Obtiene la lista de dominios de correo permitidos por tipo de usuario"""
    dominios = db.query(DominioCorreo).filter(DominioCorreo.activo == True).all()
    
    result = {
        "ALUMNO": [],
        "DOCENTE": []
    }
    
    for dominio in dominios:
        result[dominio.tipo_usuario.value].append(dominio.dominio)
    
    return result
