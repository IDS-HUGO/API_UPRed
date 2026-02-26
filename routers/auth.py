from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import re
from database import get_db
from models import Usuario, CatalogoCorreo, RolUsuario, EstadoUsuario, Auditoria, Carrera
from schemas import (
    UsuarioCreate, UsuarioResponse, Token, UsuarioLogin, Message
)
from auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user
)
from config import settings

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario en el sistema (correo institucional valido)"""
    
    # Verificar si el correo ya está registrado
    email = usuario_data.correo_institucional.strip().lower()
    existing_user = db.query(Usuario).filter(
        Usuario.correo_institucional == email
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )
    
    # Validar formato institucional: 6 digitos + @ + codigo carrera + .upchiapas.edu.mx
    match = re.match(r"^(\d{6})@([a-z0-9]{2,8})\.upchiapas\.edu\.mx$", email)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El correo no esta autorizado. Formato: 6 digitos + @ + codigo carrera + .upchiapas.edu.mx"
        )

    # Verificar o crear entrada en catalogo para controlar uso
    catalogo = db.query(CatalogoCorreo).filter(
        CatalogoCorreo.correo_institucional == email
    ).first()

    if catalogo and catalogo.usado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El correo ya fue utilizado"
        )

    if catalogo and catalogo.habilitado is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El correo no esta habilitado"
        )

    if not catalogo:
        carrera_id = None
        carrera_code = match.group(2).upper()
        carrera = db.query(Carrera).filter(Carrera.codigo == carrera_code).first()
        if carrera:
            carrera_id = carrera.id

        catalogo = CatalogoCorreo(
            correo_institucional=email,
            carrera_id=carrera_id,
            cuatrimestre_id=usuario_data.cuatrimestre_id,
            habilitado=True,
            usado=False
        )
        db.add(catalogo)
    
    # Usar datos del catálogo si no se proporcionaron
    carrera_id = usuario_data.carrera_id or catalogo.carrera_id
    cuatrimestre_id = usuario_data.cuatrimestre_id or catalogo.cuatrimestre_id
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(usuario_data.password)
    new_user = Usuario(
        correo_institucional=email,
        hash_contrasena=hashed_password,
        nombre=usuario_data.nombre,
        apellido_paterno=usuario_data.apellido_paterno,
        apellido_materno=usuario_data.apellido_materno,
        fecha_nacimiento=usuario_data.fecha_nacimiento,
        telefono=usuario_data.telefono,
        foto_perfil_url=usuario_data.foto_perfil_url,
        biografia=usuario_data.biografia,
        carrera_id=carrera_id,
        cuatrimestre_id=cuatrimestre_id,
        rol=RolUsuario.estudiante,
        estado=EstadoUsuario.activo,
        correo_verificado=True  # Los correos del catálogo se consideran verificados
    )
    
    db.add(new_user)
    db.flush()  # Para obtener el ID sin hacer commit
    
    # Marcar el correo del catálogo como usado
    catalogo.usado = True
    catalogo.consumido_por_usuario_id = new_user.id
    catalogo.consumido_en = datetime.utcnow()
    
    # Registrar en auditoría
    auditoria = Auditoria(
        actor_usuario_id=new_user.id,
        accion="registro_estudiante",
        entidad="usuarios",
        entidad_id=str(new_user.id),
        detalle={"correo": new_user.correo_institucional}
    )
    db.add(auditoria)
    
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def login(usuario_login: UsuarioLogin, db: Session = Depends(get_db)):
    """Inicia sesión y retorna un token JWT"""
    
    # Autenticar usuario
    usuario = authenticate_user(db, usuario_login.correo_institucional, usuario_login.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el usuario esté activo
    if usuario.estado != EstadoUsuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Usuario {usuario.estado.value}. Contacta al administrador."
        )
    
    # Crear token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.correo_institucional, "rol": usuario.rol.value},
        expires_delta=access_token_expires
    )
    
    # Actualizar última conexión
    usuario.ultima_conexion_en = datetime.utcnow()
    db.commit()
    
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
    
    if usuario.estado != EstadoUsuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Usuario {usuario.estado.value}"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.correo_institucional, "rol": usuario.rol.value},
        expires_delta=access_token_expires
    )
    
    # Actualizar última conexión
    usuario.ultima_conexion_en = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": usuario
    }

@router.get("/me", response_model=UsuarioResponse)
async def get_me(current_user: Usuario = Depends(get_current_user)):
    """Obtiene los datos del usuario actual"""
    return current_user

@router.post("/logout", response_model=Message)
async def logout(current_user: Usuario = Depends(get_current_user)):
    """Cierra la sesión del usuario (en el cliente debe eliminar el token)"""
    return {"message": "Sesión cerrada correctamente"}
