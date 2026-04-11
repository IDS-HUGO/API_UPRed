from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, date
from models import (
    RolUsuario, EstadoUsuario, AudienciaPublicacion, PrivacidadGrupo,
    RolMiembroGrupo, EstadoMembresia, TipoSalaChat, TipoMensaje
)
import uuid

# =====================================================================
# SCHEMAS GENERALES
# =====================================================================

class Message(BaseModel):
    message: str

# =====================================================================
# SCHEMA DE SEDES
# =====================================================================

class SedeBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=30)
    nombre: str = Field(..., min_length=1, max_length=120)
    ciudad: Optional[str] = Field(None, max_length=80)

class SedeCreate(SedeBase):
    pass

class SedeUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=1, max_length=30)
    nombre: Optional[str] = Field(None, min_length=1, max_length=120)
    ciudad: Optional[str] = Field(None, max_length=80)

class SedeResponse(SedeBase):
    id: int
    creado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE FACULTADES
# =====================================================================

class FacultadBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=30)
    nombre: str = Field(..., min_length=1, max_length=120)
    sede_id: Optional[int] = None

class FacultadCreate(FacultadBase):
    pass

class FacultadUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=1, max_length=30)
    nombre: Optional[str] = Field(None, min_length=1, max_length=120)
    sede_id: Optional[int] = None

class FacultadResponse(FacultadBase):
    id: int
    creado_en: datetime
    actualizado_en: datetime
    sede: Optional[SedeResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE CARRERAS
# =====================================================================

class CarreraBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=30)
    nombre: str = Field(..., min_length=1, max_length=120)
    facultad_id: Optional[int] = None
    activa: bool = True

class CarreraCreate(CarreraBase):
    pass

class CarreraUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=1, max_length=30)
    nombre: Optional[str] = Field(None, min_length=1, max_length=120)
    facultad_id: Optional[int] = None
    activa: Optional[bool] = None

class CarreraResponse(CarreraBase):
    id: int
    creado_en: datetime
    actualizado_en: datetime
    facultad: Optional[FacultadResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE CUATRIMESTRES
# =====================================================================

class CuatrimestreBase(BaseModel):
    numero: int = Field(..., ge=1, le=20)
    descripcion: Optional[str] = Field(None, max_length=80)
    activo: bool = True

class CuatrimestreCreate(CuatrimestreBase):
    pass

class CuatrimestreUpdate(BaseModel):
    numero: Optional[int] = Field(None, ge=1, le=20)
    descripcion: Optional[str] = Field(None, max_length=80)
    activo: Optional[bool] = None

class CuatrimestreResponse(CuatrimestreBase):
    id: int
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE CATÁLOGO DE CORREOS
# =====================================================================

class CatalogoCorreoBase(BaseModel):
    correo_institucional: EmailStr
    matricula: Optional[str] = Field(None, max_length=30)
    carrera_id: Optional[int] = None
    cuatrimestre_id: Optional[int] = None
    habilitado: bool = True
    notas: Optional[str] = None

class CatalogoCorreoCreate(CatalogoCorreoBase):
    pass

class CatalogoCorreoUpdate(BaseModel):
    habilitado: Optional[bool] = None
    notas: Optional[str] = None

class CatalogoCorreoResponse(CatalogoCorreoBase):
    id: int
    usado: bool
    consumido_por_usuario_id: Optional[int] = None
    consumido_en: Optional[datetime] = None
    creado_en: datetime
    actualizado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE USUARIOS
# =====================================================================

class UsuarioBase(BaseModel):
    correo_institucional: EmailStr
    nombre: str = Field(..., min_length=1, max_length=80)
    apellido_paterno: str = Field(..., min_length=1, max_length=80)
    apellido_materno: Optional[str] = Field(None, max_length=80)
    fecha_nacimiento: date
    telefono: Optional[str] = Field(None, max_length=30)
    foto_perfil_url: Optional[str] = None
    biografia: Optional[str] = None
    carrera_id: Optional[int] = None
    cuatrimestre_id: Optional[int] = None

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, max_length=100)

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=80)
    apellido_paterno: Optional[str] = Field(None, min_length=1, max_length=80)
    apellido_materno: Optional[str] = Field(None, max_length=80)
    fecha_nacimiento: Optional[date] = None
    telefono: Optional[str] = Field(None, max_length=30)
    foto_perfil_url: Optional[str] = None
    biografia: Optional[str] = None
    carrera_id: Optional[int] = None
    cuatrimestre_id: Optional[int] = None

class UsuarioResponse(UsuarioBase):
    id: int
    rol: RolUsuario
    estado: EstadoUsuario
    correo_verificado: bool
    ultima_conexion_en: Optional[datetime] = None
    creado_en: datetime
    actualizado_en: datetime
    carrera: Optional[CarreraResponse] = None
    cuatrimestre: Optional[CuatrimestreResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

class UsuarioLogin(BaseModel):
    correo_institucional: EmailStr
    password: str

# =====================================================================
# SCHEMA DE TOKENS
# =====================================================================

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse

class TokenData(BaseModel):
    correo_institucional: Optional[str] = None
    rol: Optional[RolUsuario] = None

# =====================================================================
# SCHEMA DE TIPOS DE PUBLICACIÓN
# =====================================================================

class TipoPublicacionBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=30)
    nombre: str = Field(..., min_length=1, max_length=60)
    descripcion: Optional[str] = Field(None, max_length=200)

class TipoPublicacionCreate(TipoPublicacionBase):
    pass

class TipoPublicacionResponse(TipoPublicacionBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE PUBLICACIONES
# =====================================================================

class AutorSimplificadoResponse(BaseModel):
    """Schema simplificado del autor para publicaciones (compatible con móvil)"""
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    foto_perfil_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class PublicacionBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=180)
    contenido: str = Field(..., min_length=1)
    audiencia: AudienciaPublicacion = AudienciaPublicacion.general
    carrera_objetivo_id: Optional[int] = None
    cuatrimestre_objetivo_id: Optional[int] = None
    tipo_publicacion_id: Optional[int] = None
    permite_comentarios: bool = True
    es_anonima: bool = False

class PublicacionCreate(PublicacionBase):
    pass

class PublicacionUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=180)
    contenido: Optional[str] = Field(None, min_length=1)
    audiencia: Optional[AudienciaPublicacion] = None
    carrera_objetivo_id: Optional[int] = None
    cuatrimestre_objetivo_id: Optional[int] = None
    tipo_publicacion_id: Optional[int] = None
    permite_comentarios: Optional[bool] = None
    es_anonima: Optional[bool] = None
    activa: Optional[bool] = None

class MultimediaPublicacionResponse(BaseModel):
    id: int
    publicacion_id: int
    tipo: TipoMensaje
    url_archivo: str
    url_miniatura: Optional[str] = None
    orden: int
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)

class PublicacionResponse(PublicacionBase):
    id: int
    autor_id: int
    activa: bool
    publicada_en: datetime
    actualizada_en: datetime
    imagen_url: Optional[str] = None
    autor: Optional[AutorSimplificadoResponse] = None
    tipo_publicacion: Optional[TipoPublicacionResponse] = None
    carrera_objetivo: Optional[CarreraResponse] = None
    multimedia: Optional[List[MultimediaPublicacionResponse]] = None
    total_comentarios: int = 0
    total_reacciones: int = 0
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE COMENTARIOS
# =====================================================================

class ComentarioPublicacionBase(BaseModel):
    publicacion_id: int
    contenido: str = Field(..., min_length=1)
    comentario_padre_id: Optional[int] = None

class ComentarioPublicacionCreate(ComentarioPublicacionBase):
    pass

class ComentarioPublicacionUpdate(BaseModel):
    contenido: Optional[str] = Field(None, min_length=1)
    activo: Optional[bool] = None

class ComentarioPublicacionResponse(ComentarioPublicacionBase):
    id: int
    usuario_id: int
    activo: bool
    creado_en: datetime
    actualizado_en: datetime
    usuario: Optional[UsuarioResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE REACCIONES
# =====================================================================

class CatalogoReaccionBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=30)
    nombre: str = Field(..., min_length=1, max_length=40)

class CatalogoReaccionCreate(CatalogoReaccionBase):
    pass

class CatalogoReaccionResponse(CatalogoReaccionBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class ReaccionPublicacionCreate(BaseModel):
    publicacion_id: int
    reaccion_id: int

class ReaccionPublicacionResponse(BaseModel):
    publicacion_id: int
    usuario_id: int
    reaccion_id: int
    creado_en: datetime
    reaccion: Optional[CatalogoReaccionResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE GRUPOS
# =====================================================================

class GrupoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    descripcion: Optional[str] = None
    carrera_id: Optional[int] = None
    privacidad: PrivacidadGrupo = PrivacidadGrupo.publico
    foto_grupo_url: Optional[str] = None

class GrupoCreate(GrupoBase):
    pass

class GrupoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=120)
    descripcion: Optional[str] = None
    privacidad: Optional[PrivacidadGrupo] = None
    foto_grupo_url: Optional[str] = None

class GrupoResponse(GrupoBase):
    id: int
    usuario_dueno_id: int
    creado_en: datetime
    actualizado_en: datetime
    dueno: Optional[UsuarioResponse] = None
    carrera: Optional[CarreraResponse] = None
    total_miembros: int = 0
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE MIEMBROS DE GRUPO
# =====================================================================

class MiembroGrupoCreate(BaseModel):
    grupo_id: int
    usuario_id: int
    rol_miembro: RolMiembroGrupo = RolMiembroGrupo.miembro

class MiembroGrupoDetailResponse(BaseModel):
    """Schema simplificado de miembro para incluir en GrupoDetailResponse"""
    usuario_id: int
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    foto_perfil_url: Optional[str] = None
    rol_miembro: RolMiembroGrupo
    estado_membresia: EstadoMembresia
    
    model_config = ConfigDict(from_attributes=True)

class GrupoDetailResponse(GrupoBase):
    """Schema que incluye los miembros del grupo"""
    id: int
    usuario_dueno_id: int
    creado_en: datetime
    actualizado_en: datetime
    dueno: Optional[UsuarioResponse] = None
    carrera: Optional[CarreraResponse] = None
    total_miembros: int = 0
    miembros: List[MiembroGrupoDetailResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class MiembroGrupoUpdate(BaseModel):
    rol_miembro: Optional[RolMiembroGrupo] = None
    estado_membresia: Optional[EstadoMembresia] = None

class MiembroGrupoResponse(BaseModel):
    grupo_id: int
    usuario_id: int
    rol_miembro: RolMiembroGrupo
    estado_membresia: EstadoMembresia
    unido_en: datetime
    salio_en: Optional[datetime] = None
    usuario: Optional[UsuarioResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

# Resolve forward references declared in GrupoDetailResponse.
GrupoDetailResponse.model_rebuild()

# =====================================================================
# SCHEMA DE PUBLICACIONES DE GRUPO
# =====================================================================

class PublicacionGrupoBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=180)
    contenido: str = Field(..., min_length=1)

class PublicacionGrupoCreate(PublicacionGrupoBase):
    grupo_id: int

class PublicacionGrupoUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=180)
    contenido: Optional[str] = Field(None, min_length=1)

class PublicacionGrupoResponse(PublicacionGrupoBase):
    id: int
    grupo_id: int
    autor_id: int
    creado_en: datetime
    actualizado_en: datetime
    autor: Optional[UsuarioResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE MENSAJERÍA
# =====================================================================

class MensajeCreate(BaseModel):
    sala_chat_id: Optional[int] = None
    destinatario_id: Optional[int] = None  # Para mensajes directos
    tipo_mensaje: TipoMensaje = TipoMensaje.texto
    contenido: Optional[str] = None
    url_archivo: Optional[str] = None
    metadatos: Optional[dict] = {}

class MensajeResponse(BaseModel):
    id: int
    mensaje_uuid: uuid.UUID
    sala_chat_id: int
    remitente_id: int
    tipo_mensaje: TipoMensaje
    contenido: Optional[str] = None
    url_archivo: Optional[str] = None
    metadatos: dict
    enviado_en: datetime
    editado_en: Optional[datetime] = None
    eliminado_en: Optional[datetime] = None
    remitente: Optional[UsuarioResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

class SalaChatResponse(BaseModel):
    id: int
    sala_uuid: uuid.UUID
    tipo_sala: TipoSalaChat
    usuario_a_id: Optional[int] = None
    usuario_b_id: Optional[int] = None
    grupo_id: Optional[int] = None
    creado_en: datetime
    actualizado_en: datetime
    ultimo_mensaje: Optional[MensajeResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMA DE NOTIFICACIONES
# =====================================================================

class NotificacionCreate(BaseModel):
    usuario_id: int
    tipo: str = Field(..., max_length=50)
    titulo: str = Field(..., min_length=1, max_length=120)
    cuerpo: Optional[str] = None
    datos: Optional[dict] = {}

class NotificacionUpdate(BaseModel):
    leida: bool

class NotificacionResponse(BaseModel):
    id: int
    usuario_id: int
    tipo: str
    titulo: str
    cuerpo: Optional[str] = None
    datos: dict
    leida: bool
    creada_en: datetime
    leida_en: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class DeviceRegistrationRequest(BaseModel):
    uuid_dispositivo: str = Field(..., min_length=3, max_length=120)
    plataforma: str = Field(default="android", max_length=20)
    token_push: Optional[str] = None

class DeviceTokenUpdateRequest(BaseModel):
    uuid_dispositivo: str = Field(..., min_length=3, max_length=120)
    token_push: str = Field(..., min_length=20)

class NotificationConfigRequest(BaseModel):
    push_enabled: bool = True
    chat_enabled: bool = True
    groups_enabled: bool = True
    social_enabled: bool = True

class SyncEventRequest(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=120)
    payload: dict = Field(default_factory=dict)
    created_at: int

class SyncEventsBatchRequest(BaseModel):
    events: List[SyncEventRequest] = Field(default_factory=list)

class NotificationSummaryResponse(BaseModel):
    total_no_leidas: int = 0
    last_notification_at: Optional[datetime] = None

# =====================================================================
# SCHEMA DE SEGUIDORES
# =====================================================================

class SeguidorCreate(BaseModel):
    seguido_id: int

class SeguidorResponse(BaseModel):
    seguidor_id: int
    seguido_id: int
    creado_en: datetime
    seguido: Optional[UsuarioResponse] = None
    seguidor: Optional[UsuarioResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# SCHEMAS DE BÚSQUEDA
# =====================================================================

class BusquedaUsuarios(BaseModel):
    query: Optional[str] = None
    carrera_id: Optional[int] = None
    cuatrimestre_id: Optional[int] = None
    rol: Optional[RolUsuario] = None
    estado: Optional[EstadoUsuario] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class BusquedaPublicaciones(BaseModel):
    query: Optional[str] = None
    autor_id: Optional[int] = None
    carrera_id: Optional[int] = None
    cuatrimestre_id: Optional[int] = None
    tipo_publicacion_id: Optional[int] = None
    audiencia: Optional[AudienciaPublicacion] = None
    activa: bool = True
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class BusquedaGrupos(BaseModel):
    query: Optional[str] = None
    carrera_id: Optional[int] = None
    privacidad: Optional[PrivacidadGrupo] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
