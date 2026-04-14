from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from hashlib import sha256
import random
import re
from database import get_db
from models import Usuario, CatalogoCorreo, RolUsuario, EstadoUsuario, Auditoria, Carrera
from schemas import (
    UsuarioCreate, UsuarioResponse, Token, UsuarioLogin, Message,
    ForgotPasswordRequest, ForgotPasswordConfirmRequest, ForgotPasswordRequestResponse,
    UsuarioCreateWithFile
)
from auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user
)
from config import settings
from services.cloudinary_service import cloudinary_service

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    value_str = str(value).strip().lower()
    return value_str in ('true', '1', 'yes', 'on')

def _parse_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    value_str = str(value).strip()
    if value_str == "":
        return None
    try:
        return int(value_str)
    except ValueError:
        return None

async def _extract_register_data(request: Request):
    """Extrae datos del registro, incluyendo archivo de foto de perfil"""
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("foto_perfil")
        data = {
            "correo_institucional": form.get("correo_institucional"),
            "password": form.get("password"),
            "nombre": form.get("nombre"),
            "apellido_paterno": form.get("apellido_paterno"),
            "apellido_materno": form.get("apellido_materno"),
            "fecha_nacimiento": form.get("fecha_nacimiento"),
            "telefono": form.get("telefono"),
            "biografia": form.get("biografia"),
            "carrera_id": _parse_int(form.get("carrera_id")),
            "cuatrimestre_id": _parse_int(form.get("cuatrimestre_id")),
        }
        return data, file

    # Fallback para JSON (sin archivo)
    payload = await request.json()
    return payload, None

@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, db: Session = Depends(get_db)):
    """Registra un nuevo usuario en el sistema (correo institucional valido)"""
    try:
        payload, file = await _extract_register_data(request)
        
        # Validar datos básicos
        if not payload.get("correo_institucional") or not payload.get("password"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Correo institucional y contraseña son requeridos"
            )
        
        usuario_data = UsuarioCreateWithFile.model_validate(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Datos inválidos: {str(e)}"
        )
    
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
    match = re.match(r"^(\d{6})@([a-z0-9][a-z0-9.-]{1,20})\.upchiapas\.edu\.mx$", email)
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
        # Si no hay usuario registrado con ese correo, liberar el catalogo
        if not existing_user:
            catalogo.usado = False
            catalogo.consumido_por_usuario_id = None
            catalogo.consumido_en = None
        else:
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
    
    # Procesar foto de perfil si se proporcionó
    foto_perfil_url = None
    file_data = None
    if file and file.filename:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten imágenes para la foto de perfil"
            )
        
        try:
            file_data = await file.read()
            if len(file_data) > 5 * 1024 * 1024:  # 5MB máximo
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La foto de perfil no debe superar 5MB"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar la foto de perfil: {str(e)}"
            )
    
    # Crear nuevo usuario sin URL de foto todavía
    hashed_password = get_password_hash(usuario_data.password)
    new_user = Usuario(
        correo_institucional=email,
        hash_contrasena=hashed_password,
        nombre=usuario_data.nombre,
        apellido_paterno=usuario_data.apellido_paterno,
        apellido_materno=usuario_data.apellido_materno,
        fecha_nacimiento=usuario_data.fecha_nacimiento,
        telefono=usuario_data.telefono,
        foto_perfil_url=None,
        biografia=usuario_data.biografia,
        carrera_id=carrera_id,
        cuatrimestre_id=cuatrimestre_id,
        rol=RolUsuario.estudiante,
        estado=EstadoUsuario.activo,
        correo_verificado=True  # Los correos del catálogo se consideran verificados
    )
    
    db.add(new_user)
    db.flush()  # Para obtener el ID sin hacer commit
    
    # Subir la foto a Cloudinary usando el ID real del usuario
    if file_data is not None:
        if not cloudinary_service.is_configured():
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Servicio de almacenamiento de imágenes no disponible"
            )
        try:
            public_id = f"perfiles/{new_user.id}"
            foto_perfil_url = cloudinary_service.upload_image(file_data, public_id)
            new_user.foto_perfil_url = foto_perfil_url
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al guardar la foto de perfil: {str(e)}"
            )
    
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


@router.post("/forgot-password/request", response_model=ForgotPasswordRequestResponse)
def request_password_reset(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Genera un codigo temporal para restablecer contraseña"""
    correo = payload.correo_institucional.strip().lower()
    usuario = db.query(Usuario).filter(Usuario.correo_institucional == correo).first()

    # Respuesta generica para no revelar si el correo existe o no
    generic_message = "Si el correo existe, se genero un codigo de recuperacion valido por 15 minutos"
    if usuario is None:
        return {"message": generic_message}

    code = f"{random.randint(0, 999999):06d}"
    code_hash = sha256(code.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    db.add(
        Auditoria(
            actor_usuario_id=usuario.id,
            accion="password_reset_request",
            entidad="auth_password_reset",
            entidad_id=str(usuario.id),
            detalle={
                "correo": correo,
                "codigo_hash": code_hash,
                "expira_en": expires_at.isoformat(),
                "usado": False,
            },
        )
    )
    db.commit()

    # Actualmente no hay proveedor de correo integrado; devolvemos codigo para flujo móvil.
    # En producción se recomienda reemplazar esto por envío de correo/SMS y ocultar el código.
    return {"message": generic_message, "reset_code": code}


@router.post("/forgot-password/confirm", response_model=Message)
def confirm_password_reset(payload: ForgotPasswordConfirmRequest, db: Session = Depends(get_db)):
    """Valida codigo de recuperacion y actualiza contraseña"""
    correo = payload.correo_institucional.strip().lower()
    usuario = db.query(Usuario).filter(Usuario.correo_institucional == correo).first()
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Codigo invalido o expirado")

    registro = db.query(Auditoria).filter(
        Auditoria.actor_usuario_id == usuario.id,
        Auditoria.accion == "password_reset_request",
        Auditoria.entidad == "auth_password_reset"
    ).order_by(Auditoria.creada_en.desc()).first()

    if registro is None or not isinstance(registro.detalle, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Codigo invalido o expirado")

    detalle = dict(registro.detalle)
    if detalle.get("usado") is True:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El codigo ya fue usado")

    expira_en = detalle.get("expira_en")
    try:
        expira_en_dt = datetime.fromisoformat(expira_en)
    except Exception:
        expira_en_dt = None

    if expira_en_dt is None or datetime.utcnow() > expira_en_dt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Codigo invalido o expirado")

    payload_hash = sha256(payload.codigo.encode("utf-8")).hexdigest()
    if payload_hash != detalle.get("codigo_hash"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Codigo invalido o expirado")

    usuario.hash_contrasena = get_password_hash(payload.nueva_password)
    detalle["usado"] = True
    registro.detalle = detalle

    db.add(
        Auditoria(
            actor_usuario_id=usuario.id,
            accion="password_reset_completed",
            entidad="usuarios",
            entidad_id=str(usuario.id),
            detalle={"correo": correo},
        )
    )
    db.commit()

    return {"message": "Contrasena actualizada correctamente"}
