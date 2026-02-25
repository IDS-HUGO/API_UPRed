from sqlalchemy import Boolean, Column, Integer, BigInteger, String, Text, DateTime, Date, SmallInteger, Enum as SQLEnum, ForeignKey, CheckConstraint, UniqueConstraint, Index, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB, CITEXT
from database import Base
import enum
import uuid as uuid_pkg

# =====================================================================
# ENUMS
# =====================================================================

class RolUsuario(str, enum.Enum):
    estudiante = "estudiante"
    moderador = "moderador"
    administrador = "administrador"

class EstadoUsuario(str, enum.Enum):
    activo = "activo"
    suspendido = "suspendido"
    eliminado = "eliminado"

class AudienciaPublicacion(str, enum.Enum):
    general = "general"
    carrera = "carrera"

class PrivacidadGrupo(str, enum.Enum):
    publico = "publico"
    privado = "privado"

class RolMiembroGrupo(str, enum.Enum):
    dueno = "dueno"
    admin = "admin"
    miembro = "miembro"

class EstadoMembresia(str, enum.Enum):
    pendiente = "pendiente"
    activo = "activo"
    rechazado = "rechazado"
    salio = "salio"

class TipoSalaChat(str, enum.Enum):
    directo = "directo"
    grupal = "grupal"

class TipoMensaje(str, enum.Enum):
    texto = "texto"
    imagen = "imagen"
    archivo = "archivo"
    audio = "audio"
    sistema = "sistema"

# =====================================================================
# ESTRUCTURA ACADÉMICA
# =====================================================================

class Sede(Base):
    __tablename__ = "sedes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    codigo = Column(String(30), nullable=False, unique=True)
    nombre = Column(String(120), nullable=False)
    ciudad = Column(String(80))
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Relaciones
    facultades = relationship("Facultad", back_populates="sede")

class Facultad(Base):
    __tablename__ = "facultades"
    
    id = Column(BigInteger, primary_key=True, index=True)
    codigo = Column(String(30), nullable=False, unique=True)
    nombre = Column(String(120), nullable=False)
    sede_id = Column(BigInteger, ForeignKey("sedes.id", ondelete="SET NULL"))
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    sede = relationship("Sede", back_populates="facultades")
    carreras = relationship("Carrera", back_populates="facultad")

class Carrera(Base):
    __tablename__ = "carreras"
    
    id = Column(BigInteger, primary_key=True, index=True)
    codigo = Column(String(30), nullable=False, unique=True)
    nombre = Column(String(120), nullable=False)
    facultad_id = Column(BigInteger, ForeignKey("facultades.id", ondelete="SET NULL"))
    activa = Column(Boolean, nullable=False, default=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    facultad = relationship("Facultad", back_populates="carreras")
    usuarios = relationship("Usuario", back_populates="carrera")
    catalogo_correos = relationship("CatalogoCorreo", back_populates="carrera")
    publicaciones = relationship("Publicacion", foreign_keys="[Publicacion.carrera_objetivo_id]", back_populates="carrera_objetivo")
    grupos = relationship("Grupo", back_populates="carrera")

class Cuatrimestre(Base):
    __tablename__ = "cuatrimestres"
    
    id = Column(BigInteger, primary_key=True, index=True)
    numero = Column(SmallInteger, nullable=False, unique=True)
    descripcion = Column(String(80))
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint('numero >= 1 AND numero <= 20', name='chk_numero_cuatrimestre'),
    )
    
    # Relaciones
    usuarios = relationship("Usuario", back_populates="cuatrimestre")
    catalogo_correos = relationship("CatalogoCorreo", back_populates="cuatrimestre")

# =====================================================================
# CATÁLOGO DE CORREOS
# =====================================================================

class CatalogoCorreo(Base):
    __tablename__ = "catalogo_correos"
    
    id = Column(BigInteger, primary_key=True, index=True)
    correo_institucional = Column(String, nullable=False, unique=True)  # CITEXT en PostgreSQL
    matricula = Column(String(30), unique=True)
    carrera_id = Column(BigInteger, ForeignKey("carreras.id", ondelete="SET NULL"))
    cuatrimestre_id = Column(BigInteger, ForeignKey("cuatrimestres.id", ondelete="SET NULL"))
    habilitado = Column(Boolean, nullable=False, default=True)
    usado = Column(Boolean, nullable=False, default=False)
    consumido_por_usuario_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="SET NULL"))
    consumido_en = Column(TIMESTAMP(timezone=True))
    notas = Column(Text)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    carrera = relationship("Carrera", back_populates="catalogo_correos")
    cuatrimestre = relationship("Cuatrimestre", back_populates="catalogo_correos")
    consumido_por = relationship("Usuario", foreign_keys=[consumido_por_usuario_id])

# =====================================================================
# USUARIOS
# =====================================================================

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(BigInteger, primary_key=True, index=True)
    correo_institucional = Column(String, nullable=False, unique=True)  # CITEXT
    hash_contrasena = Column(Text, nullable=False)
    nombre = Column(String(80), nullable=False)
    apellido_paterno = Column(String(80), nullable=False)
    apellido_materno = Column(String(80))
    fecha_nacimiento = Column(Date, nullable=False)
    telefono = Column(String(30))
    foto_perfil_url = Column(Text)
    biografia = Column(Text)
    carrera_id = Column(BigInteger, ForeignKey("carreras.id", ondelete="SET NULL"))
    cuatrimestre_id = Column(BigInteger, ForeignKey("cuatrimestres.id", ondelete="SET NULL"))
    rol = Column(SQLEnum(RolUsuario), nullable=False, default=RolUsuario.estudiante)
    estado = Column(SQLEnum(EstadoUsuario), nullable=False, default=EstadoUsuario.activo)
    correo_verificado = Column(Boolean, nullable=False, default=False)
    ultima_conexion_en = Column(TIMESTAMP(timezone=True))
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    eliminado_en = Column(TIMESTAMP(timezone=True))
    
    # Relaciones
    carrera = relationship("Carrera", back_populates="usuarios")
    cuatrimestre = relationship("Cuatrimestre", back_populates="usuarios")
    dispositivos = relationship("DispositivoUsuario", back_populates="usuario", cascade="all, delete-orphan")
    publicaciones = relationship("Publicacion", back_populates="autor", cascade="all, delete-orphan")
    comentarios = relationship("ComentarioPublicacion", back_populates="usuario", cascade="all, delete-orphan")
    reacciones = relationship("ReaccionPublicacion", back_populates="usuario", cascade="all, delete-orphan")
    grupos_propios = relationship("Grupo", foreign_keys="[Grupo.usuario_dueno_id]", back_populates="dueno")
    membresías = relationship("MiembroGrupo", back_populates="usuario", cascade="all, delete-orphan")
    publicaciones_grupo = relationship("PublicacionGrupo", back_populates="autor", cascade="all, delete-orphan")
    mensajes_enviados = relationship("Mensaje", back_populates="remitente", cascade="all, delete-orphan")
    mensajes_recibidos = relationship("DestinatarioMensaje", back_populates="destinatario", cascade="all, delete-orphan")
    notificaciones = relationship("Notificacion", back_populates="usuario", cascade="all, delete-orphan")

class DispositivoUsuario(Base):
    __tablename__ = "dispositivos_usuario"
    
    id = Column(BigInteger, primary_key=True, index=True)
    usuario_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    uuid_dispositivo = Column(String(120), nullable=False)
    plataforma = Column(String(20), nullable=False, default="android")
    token_push = Column(Text)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    ultima_actividad_en = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        UniqueConstraint('usuario_id', 'uuid_dispositivo', name='uq_dispositivo_usuario'),
    )
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="dispositivos")

# =====================================================================
# SEGUIDORES
# =====================================================================

class Seguidor(Base):
    __tablename__ = "seguidores"
    
    seguidor_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    seguido_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint('seguidor_id <> seguido_id', name='chk_no_seguirse_a_si_mismo'),
    )

# =====================================================================
# PUBLICACIONES
# =====================================================================

class TipoPublicacion(Base):
    __tablename__ = "tipos_publicacion"
    
    id = Column(BigInteger, primary_key=True, index=True)
    codigo = Column(String(30), nullable=False, unique=True)
    nombre = Column(String(60), nullable=False)
    descripcion = Column(String(200))
    
    # Relaciones
    publicaciones = relationship("Publicacion", back_populates="tipo_publicacion")

class Publicacion(Base):
    __tablename__ = "publicaciones"
    
    id = Column(BigInteger, primary_key=True, index=True)
    autor_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    tipo_publicacion_id = Column(BigInteger, ForeignKey("tipos_publicacion.id", ondelete="SET NULL"))
    titulo = Column(String(180), nullable=False)
    contenido = Column(Text, nullable=False)
    audiencia = Column(SQLEnum(AudienciaPublicacion), nullable=False, default=AudienciaPublicacion.general)
    carrera_objetivo_id = Column(BigInteger, ForeignKey("carreras.id", ondelete="SET NULL"))
    cuatrimestre_objetivo_id = Column(BigInteger, ForeignKey("cuatrimestres.id", ondelete="SET NULL"))
    permite_comentarios = Column(Boolean, nullable=False, default=True)
    es_anonima = Column(Boolean, nullable=False, default=False)
    activa = Column(Boolean, nullable=False, default=True)
    programada_para = Column(TIMESTAMP(timezone=True))
    publicada_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizada_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    eliminada_en = Column(TIMESTAMP(timezone=True))
    
    # Relaciones
    autor = relationship("Usuario", back_populates="publicaciones")
    tipo_publicacion = relationship("TipoPublicacion", back_populates="publicaciones")
    carrera_objetivo = relationship("Carrera", foreign_keys=[carrera_objetivo_id], back_populates="publicaciones")
    multimedia = relationship("MultimediaPublicacion", back_populates="publicacion", cascade="all, delete-orphan")
    comentarios = relationship("ComentarioPublicacion", back_populates="publicacion", cascade="all, delete-orphan")
    reacciones = relationship("ReaccionPublicacion", back_populates="publicacion", cascade="all, delete-orphan")

class MultimediaPublicacion(Base):
    __tablename__ = "multimedia_publicacion"
    
    id = Column(BigInteger, primary_key=True, index=True)
    publicacion_id = Column(BigInteger, ForeignKey("publicaciones.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(SQLEnum(TipoMensaje), nullable=False)
    url_archivo = Column(Text, nullable=False)
    url_miniatura = Column(Text)
    orden = Column(Integer, nullable=False, default=1)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Relaciones
    publicacion = relationship("Publicacion", back_populates="multimedia")

class ComentarioPublicacion(Base):
    __tablename__ = "comentarios_publicacion"
    
    id = Column(BigInteger, primary_key=True, index=True)
    publicacion_id = Column(BigInteger, ForeignKey("publicaciones.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    comentario_padre_id = Column(BigInteger, ForeignKey("comentarios_publicacion.id", ondelete="CASCADE"))
    contenido = Column(Text, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    publicacion = relationship("Publicacion", back_populates="comentarios")
    usuario = relationship("Usuario", back_populates="comentarios")
    respuestas = relationship("ComentarioPublicacion", backref="padre", remote_side=[id])

class CatalogoReaccion(Base):
    __tablename__ = "catalogo_reacciones"
    
    id = Column(BigInteger, primary_key=True, index=True)
    codigo = Column(String(30), nullable=False, unique=True)
    nombre = Column(String(40), nullable=False)
    
    # Relaciones
    reacciones = relationship("ReaccionPublicacion", back_populates="reaccion")

class ReaccionPublicacion(Base):
    __tablename__ = "reacciones_publicacion"
    
    publicacion_id = Column(BigInteger, ForeignKey("publicaciones.id", ondelete="CASCADE"), primary_key=True)
    usuario_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    reaccion_id = Column(BigInteger, ForeignKey("catalogo_reacciones.id", ondelete="RESTRICT"), nullable=False)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Relaciones
    publicacion = relationship("Publicacion", back_populates="reacciones")
    usuario = relationship("Usuario", back_populates="reacciones")
    reaccion = relationship("CatalogoReaccion", back_populates="reacciones")

# =====================================================================
# GRUPOS
# =====================================================================

class Grupo(Base):
    __tablename__ = "grupos"
    
    id = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(Text)
    carrera_id = Column(BigInteger, ForeignKey("carreras.id", ondelete="SET NULL"))
    privacidad = Column(SQLEnum(PrivacidadGrupo), nullable=False, default=PrivacidadGrupo.publico)
    usuario_dueno_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    foto_grupo_url = Column(Text)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('nombre', 'carrera_id', name='uq_grupo_nombre_carrera'),
    )
    
    # Relaciones
    carrera = relationship("Carrera", back_populates="grupos")
    dueno = relationship("Usuario", foreign_keys=[usuario_dueno_id], back_populates="grupos_propios")
    miembros = relationship("MiembroGrupo", back_populates="grupo", cascade="all, delete-orphan")
    publicaciones = relationship("PublicacionGrupo", back_populates="grupo", cascade="all, delete-orphan")

class MiembroGrupo(Base):
    __tablename__ = "miembros_grupo"
    
    grupo_id = Column(BigInteger, ForeignKey("grupos.id", ondelete="CASCADE"), primary_key=True)
    usuario_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    rol_miembro = Column(SQLEnum(RolMiembroGrupo), nullable=False, default=RolMiembroGrupo.miembro)
    estado_membresia = Column(SQLEnum(EstadoMembresia), nullable=False, default=EstadoMembresia.activo)
    unido_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    salio_en = Column(TIMESTAMP(timezone=True))
    
    # Relaciones
    grupo = relationship("Grupo", back_populates="miembros")
    usuario = relationship("Usuario", back_populates="membresías")

class PublicacionGrupo(Base):
    __tablename__ = "publicaciones_grupo"
    
    id = Column(BigInteger, primary_key=True, index=True)
    grupo_id = Column(BigInteger, ForeignKey("grupos.id", ondelete="CASCADE"), nullable=False)
    autor_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    titulo = Column(String(180), nullable=False)
    contenido = Column(Text, nullable=False)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    grupo = relationship("Grupo", back_populates="publicaciones")
    autor = relationship("Usuario", back_populates="publicaciones_grupo")

# =====================================================================
# MENSAJERÍA
# =====================================================================

class SalaChat(Base):
    __tablename__ = "salas_chat"
    
    id = Column(BigInteger, primary_key=True, index=True)
    sala_uuid = Column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid_pkg.uuid4)
    tipo_sala = Column(SQLEnum(TipoSalaChat), nullable=False)
    usuario_a_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"))
    usuario_b_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"))
    grupo_id = Column(BigInteger, ForeignKey("grupos.id", ondelete="CASCADE"))
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    mensajes = relationship("Mensaje", back_populates="sala_chat", cascade="all, delete-orphan")

class Mensaje(Base):
    __tablename__ = "mensajes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    mensaje_uuid = Column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid_pkg.uuid4)
    sala_chat_id = Column(BigInteger, ForeignKey("salas_chat.id", ondelete="CASCADE"), nullable=False)
    remitente_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    tipo_mensaje = Column(SQLEnum(TipoMensaje), nullable=False, default=TipoMensaje.texto)
    contenido = Column(Text)
    url_archivo = Column(Text)
    metadatos = Column(JSONB, nullable=False, default={})
    enviado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    editado_en = Column(TIMESTAMP(timezone=True))
    eliminado_en = Column(TIMESTAMP(timezone=True))
    
    # Relaciones
    sala_chat = relationship("SalaChat", back_populates="mensajes")
    remitente = relationship("Usuario", back_populates="mensajes_enviados")
    destinatarios = relationship("DestinatarioMensaje", back_populates="mensaje", cascade="all, delete-orphan")

class DestinatarioMensaje(Base):
    __tablename__ = "destinatarios_mensaje"
    
    mensaje_id = Column(BigInteger, ForeignKey("mensajes.id", ondelete="CASCADE"), primary_key=True)
    destinatario_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    entregado_en = Column(TIMESTAMP(timezone=True))
    leido_en = Column(TIMESTAMP(timezone=True))
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Relaciones
    mensaje = relationship("Mensaje", back_populates="destinatarios")
    destinatario = relationship("Usuario", back_populates="mensajes_recibidos")

# =====================================================================
# NOTIFICACIONES Y AUDITORÍA
# =====================================================================

class Notificacion(Base):
    __tablename__ = "notificaciones"
    
    id = Column(BigInteger, primary_key=True, index=True)
    usuario_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(50), nullable=False)
    titulo = Column(String(120), nullable=False)
    cuerpo = Column(Text)
    datos = Column(JSONB, nullable=False, default={})
    leida = Column(Boolean, nullable=False, default=False)
    creada_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    leida_en = Column(TIMESTAMP(timezone=True))
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="notificaciones")

class Auditoria(Base):
    __tablename__ = "auditoria"
    
    id = Column(BigInteger, primary_key=True, index=True)
    actor_usuario_id = Column(BigInteger, ForeignKey("usuarios.id", ondelete="SET NULL"))
    accion = Column(String(100), nullable=False)
    entidad = Column(String(100), nullable=False)
    entidad_id = Column(String(100))
    detalle = Column(JSONB, nullable=False, default={})
    creada_en = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
