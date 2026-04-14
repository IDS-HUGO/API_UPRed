-- =====================================================================
-- SETUP COMPLETO - BASE DE DATOS UPRED
-- Motor: MySQL 8.0+
-- Red Social Universitaria
-- =====================================================================

-- Eliminar base de datos si existe (¡CUIDADO EN PRODUCCIÓN!)
DROP DATABASE IF EXISTS upred_db;

-- Crear base de datos con charset UTF8
CREATE DATABASE upred_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE upred_db;

SET FOREIGN_KEY_CHECKS=0;

-- =====================================================================
-- ESTRUCTURA ACADÉMICA
-- =====================================================================

CREATE TABLE sedes (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    codigo              VARCHAR(30) NOT NULL UNIQUE,
    nombre              VARCHAR(120) NOT NULL,
    ciudad              VARCHAR(80),
    creado_en           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sedes_codigo (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE facultades (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    codigo              VARCHAR(30) NOT NULL UNIQUE,
    nombre              VARCHAR(120) NOT NULL,
    sede_id             BIGINT,
    creado_en           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (sede_id) REFERENCES sedes(id) ON DELETE SET NULL,
    INDEX idx_facultades_sede (sede_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE carreras (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    codigo              VARCHAR(30) NOT NULL UNIQUE,
    nombre              VARCHAR(120) NOT NULL,
    facultad_id         BIGINT,
    activa              BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (facultad_id) REFERENCES facultades(id) ON DELETE SET NULL,
    INDEX idx_carreras_facultad (facultad_id),
    INDEX idx_carreras_activa (activa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE cuatrimestres (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    numero              SMALLINT NOT NULL UNIQUE,
    descripcion         VARCHAR(80),
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_numero_cuatrimestre CHECK (numero >= 1 AND numero <= 20),
    INDEX idx_cuatrimestres_numero (numero)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- CATÁLOGO DE CORREOS INSTITUCIONALES (WHITELIST)
-- =====================================================================

CREATE TABLE catalogo_correos (
    id                          BIGINT AUTO_INCREMENT PRIMARY KEY,
    correo_institucional        VARCHAR(255) NOT NULL UNIQUE,
    matricula                   VARCHAR(30) UNIQUE,
    carrera_id                  BIGINT,
    cuatrimestre_id             BIGINT,
    habilitado                  BOOLEAN NOT NULL DEFAULT TRUE,
    usado                       BOOLEAN NOT NULL DEFAULT FALSE,
    consumido_por_usuario_id    BIGINT,
    consumido_en                DATETIME,
    notas                       TEXT,
    creado_en                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE SET NULL,
    FOREIGN KEY (cuatrimestre_id) REFERENCES cuatrimestres(id) ON DELETE SET NULL,
    INDEX idx_catalogo_correos_correo (correo_institucional),
    INDEX idx_catalogo_correos_usado (usado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- USUARIOS (ESTUDIANTES) Y PERFIL
-- =====================================================================

CREATE TABLE usuarios (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    correo_institucional    VARCHAR(255) NOT NULL UNIQUE,
    hash_contrasena         TEXT NOT NULL,
    nombre                  VARCHAR(80) NOT NULL,
    apellido_paterno        VARCHAR(80) NOT NULL,
    apellido_materno        VARCHAR(80),
    fecha_nacimiento        DATE NOT NULL,
    telefono                VARCHAR(30),
    foto_perfil_url         TEXT,
    biografia               TEXT,
    carrera_id              BIGINT,
    cuatrimestre_id         BIGINT,
    rol                     ENUM('estudiante', 'moderador', 'administrador') NOT NULL DEFAULT 'estudiante',
    estado                  ENUM('activo', 'suspendido', 'eliminado') NOT NULL DEFAULT 'activo',
    correo_verificado       BOOLEAN NOT NULL DEFAULT FALSE,
    ultima_conexion_en      DATETIME,
    creado_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    eliminado_en            DATETIME,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE SET NULL,
    FOREIGN KEY (cuatrimestre_id) REFERENCES cuatrimestres(id) ON DELETE SET NULL,
    INDEX idx_usuarios_correo (correo_institucional),
    INDEX idx_usuarios_carrera (carrera_id),
    INDEX idx_usuarios_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE catalogo_correos ADD FOREIGN KEY (consumido_por_usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL;

CREATE TABLE dispositivos_usuario (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id              BIGINT NOT NULL,
    uuid_dispositivo        VARCHAR(120) NOT NULL,
    plataforma              VARCHAR(20) NOT NULL DEFAULT 'android',
    token_push              TEXT,
    activo                  BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultima_actividad_en     DATETIME,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY uq_dispositivo_usuario (usuario_id, uuid_dispositivo),
    INDEX idx_dispositivos_usuario (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- RELACIONES ENTRE USUARIOS
-- =====================================================================

CREATE TABLE seguidores (
    seguidor_id             BIGINT NOT NULL,
    seguido_id              BIGINT NOT NULL,
    creado_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (seguidor_id, seguido_id),
    FOREIGN KEY (seguidor_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (seguido_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT chk_no_seguirse_a_si_mismo CHECK (seguidor_id <> seguido_id),
    INDEX idx_seguidores_seguido (seguido_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- PUBLICACIONES (NORMALIZADAS)
-- =====================================================================

CREATE TABLE tipos_publicacion (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    codigo                  VARCHAR(30) NOT NULL UNIQUE,
    nombre                  VARCHAR(60) NOT NULL,
    descripcion             VARCHAR(200)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE publicaciones (
    id                          BIGINT AUTO_INCREMENT PRIMARY KEY,
    autor_id                    BIGINT NOT NULL,
    tipo_publicacion_id         BIGINT,
    titulo                      VARCHAR(180) NOT NULL,
    contenido                   TEXT NOT NULL,
    audiencia                   ENUM('general', 'carrera') NOT NULL DEFAULT 'general',
    carrera_objetivo_id         BIGINT,
    cuatrimestre_objetivo_id    BIGINT,
    permite_comentarios         BOOLEAN NOT NULL DEFAULT TRUE,
    es_anonima                  BOOLEAN NOT NULL DEFAULT FALSE,
    activa                      BOOLEAN NOT NULL DEFAULT TRUE,
    programada_para             DATETIME,
    publicada_en                DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizada_en              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    eliminada_en                DATETIME,
    FOREIGN KEY (autor_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (tipo_publicacion_id) REFERENCES tipos_publicacion(id) ON DELETE SET NULL,
    FOREIGN KEY (carrera_objetivo_id) REFERENCES carreras(id) ON DELETE SET NULL,
    FOREIGN KEY (cuatrimestre_objetivo_id) REFERENCES cuatrimestres(id) ON DELETE SET NULL,
    INDEX idx_publicaciones_autor (autor_id),
    INDEX idx_publicaciones_audiencia (audiencia, carrera_objetivo_id),
    INDEX idx_publicaciones_fecha (publicada_en DESC),
    INDEX idx_publicaciones_activa (activa, publicada_en DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE multimedia_publicacion (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    publicacion_id          BIGINT NOT NULL,
    tipo                    ENUM('texto', 'imagen', 'archivo', 'audio', 'sistema') NOT NULL,
    url_archivo             TEXT,
    datos_archivo           MEDIUMBLOB,
    url_miniatura           TEXT,
    orden                   INT NOT NULL DEFAULT 1,
    creado_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (publicacion_id) REFERENCES publicaciones(id) ON DELETE CASCADE,
    INDEX idx_multimedia_publicacion (publicacion_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE comentarios_publicacion (
    id                          BIGINT AUTO_INCREMENT PRIMARY KEY,
    publicacion_id              BIGINT NOT NULL,
    usuario_id                  BIGINT NOT NULL,
    comentario_padre_id         BIGINT,
    contenido                   TEXT NOT NULL,
    activo                      BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en                   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (publicacion_id) REFERENCES publicaciones(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (comentario_padre_id) REFERENCES comentarios_publicacion(id) ON DELETE CASCADE,
    INDEX idx_comentarios_publicacion (publicacion_id),
    INDEX idx_comentarios_usuario (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE catalogo_reacciones (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    codigo                  VARCHAR(30) NOT NULL UNIQUE,
    nombre                  VARCHAR(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE reacciones_publicacion (
    publicacion_id          BIGINT NOT NULL,
    usuario_id              BIGINT NOT NULL,
    reaccion_id             BIGINT NOT NULL,
    creado_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (publicacion_id, usuario_id),
    FOREIGN KEY (publicacion_id) REFERENCES publicaciones(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (reaccion_id) REFERENCES catalogo_reacciones(id) ON DELETE RESTRICT,
    INDEX idx_reacciones_publicacion (publicacion_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- GRUPOS Y COMUNIDAD
-- =====================================================================

CREATE TABLE grupos (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    nombre                  VARCHAR(120) NOT NULL,
    descripcion             TEXT,
    carrera_id              BIGINT,
    privacidad              ENUM('publico', 'privado') NOT NULL DEFAULT 'publico',
    usuario_dueno_id        BIGINT NOT NULL,
    foto_grupo_url          TEXT,
    creado_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE SET NULL,
    FOREIGN KEY (usuario_dueno_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    UNIQUE KEY uq_grupo_nombre_carrera (nombre, carrera_id),
    INDEX idx_grupos_carrera (carrera_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE miembros_grupo (
    grupo_id                BIGINT NOT NULL,
    usuario_id              BIGINT NOT NULL,
    rol_miembro             ENUM('dueno', 'admin', 'miembro') NOT NULL DEFAULT 'miembro',
    estado_membresia        ENUM('pendiente', 'activo', 'rechazado', 'salio') NOT NULL DEFAULT 'activo',
    unido_en                DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    salio_en                DATETIME,
    PRIMARY KEY (grupo_id, usuario_id),
    FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_miembros_usuario (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE publicaciones_grupo (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    grupo_id                BIGINT NOT NULL,
    autor_id                BIGINT NOT NULL,
    titulo                  VARCHAR(180) NOT NULL,
    contenido               TEXT NOT NULL,
    creado_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
    FOREIGN KEY (autor_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_publicaciones_grupo (grupo_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- MENSAJERÍA 1 A 1 Y GRUPAL (WebSocket)
-- =====================================================================

CREATE TABLE salas_chat (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    sala_uuid               VARCHAR(36) NOT NULL UNIQUE,
    tipo_sala               ENUM('directo', 'grupal') NOT NULL,
    usuario_a_id            BIGINT,
    usuario_b_id            BIGINT,
    grupo_id                BIGINT,
    creado_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_a_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_b_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
    INDEX idx_salas_chat_tipo (tipo_sala),
    INDEX idx_salas_chat_usuarios (usuario_a_id, usuario_b_id),
    INDEX idx_salas_chat_grupo (grupo_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE mensajes (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    mensaje_uuid            VARCHAR(36) NOT NULL UNIQUE,
    sala_chat_id            BIGINT NOT NULL,
    remitente_id            BIGINT NOT NULL,
    tipo_mensaje            ENUM('texto', 'imagen', 'archivo', 'audio', 'sistema') NOT NULL DEFAULT 'texto',
    contenido               TEXT,
    url_archivo             TEXT,
    datos_archivo           MEDIUMBLOB,
    metadatos               JSON,
    enviado_en              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    editado_en              DATETIME,
    eliminado_en            DATETIME,
    FOREIGN KEY (sala_chat_id) REFERENCES salas_chat(id) ON DELETE CASCADE,
    FOREIGN KEY (remitente_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_mensajes_sala_fecha (sala_chat_id, enviado_en DESC),
    INDEX idx_mensajes_remitente (remitente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE destinatarios_mensaje (
    mensaje_id              BIGINT NOT NULL,
    destinatario_id         BIGINT NOT NULL,
    entregado_en            DATETIME,
    leido_en                DATETIME,
    creado_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (mensaje_id, destinatario_id),
    FOREIGN KEY (mensaje_id) REFERENCES mensajes(id) ON DELETE CASCADE,
    FOREIGN KEY (destinatario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_destinatarios_usuario (destinatario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- NOTIFICACIONES Y AUDITORÍA
-- =====================================================================

CREATE TABLE notificaciones (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id              BIGINT NOT NULL,
    tipo                    VARCHAR(50) NOT NULL,
    titulo                  VARCHAR(120) NOT NULL,
    cuerpo                  TEXT,
    datos                   JSON,
    leida                   BOOLEAN NOT NULL DEFAULT FALSE,
    creada_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    leida_en                DATETIME,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_notificaciones_usuario_leida (usuario_id, leida, creada_en DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE auditoria (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    actor_usuario_id        BIGINT,
    accion                  VARCHAR(100) NOT NULL,
    entidad                 VARCHAR(100) NOT NULL,
    entidad_id              VARCHAR(100),
    detalle                 JSON,
    creada_en               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor_usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_auditoria_actor_fecha (actor_usuario_id, creada_en DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS=1;

-- =====================================================================
-- DATOS SEMILLA (INICIALES)
-- =====================================================================

-- Sedes
INSERT INTO sedes (codigo, nombre, ciudad) VALUES 
('MAIN', 'Campus Principal', 'Ciudad Universitaria');

-- Facultades
INSERT INTO facultades (codigo, nombre, sede_id)
SELECT 'ING', 'Facultad de Ingeniería', s.id FROM sedes s WHERE s.codigo = 'MAIN';

INSERT INTO facultades (codigo, nombre, sede_id)
SELECT 'SAL', 'Facultad de Ciencias de la Salud', s.id FROM sedes s WHERE s.codigo = 'MAIN';

INSERT INTO facultades (codigo, nombre, sede_id)
SELECT 'ADM', 'Facultad de Administración', s.id FROM sedes s WHERE s.codigo = 'MAIN';

-- Carreras
INSERT INTO carreras (codigo, nombre, facultad_id)
SELECT 'SIS', 'Ingeniería de Sistemas', f.id FROM facultades f WHERE f.codigo = 'ING';

INSERT INTO carreras (codigo, nombre, facultad_id)
SELECT 'IND', 'Ingeniería Industrial', f.id FROM facultades f WHERE f.codigo = 'ING';

INSERT INTO carreras (codigo, nombre, facultad_id)
SELECT 'MED', 'Medicina', f.id FROM facultades f WHERE f.codigo = 'SAL';

INSERT INTO carreras (codigo, nombre, facultad_id)
SELECT 'ENF', 'Enfermería', f.id FROM facultades f WHERE f.codigo = 'SAL';

INSERT INTO carreras (codigo, nombre, facultad_id)
SELECT 'ADM', 'Administración de Empresas', f.id FROM facultades f WHERE f.codigo = 'ADM';

-- Cuatrimestres
INSERT INTO cuatrimestres (numero, descripcion) VALUES
    (1, 'Primer cuatrimestre'),
    (2, 'Segundo cuatrimestre'),
    (3, 'Tercer cuatrimestre'),
    (4, 'Cuarto cuatrimestre'),
    (5, 'Quinto cuatrimestre'),
    (6, 'Sexto cuatrimestre'),
    (7, 'Séptimo cuatrimestre'),
    (8, 'Octavo cuatrimestre');

-- Tipos de publicación
INSERT INTO tipos_publicacion (codigo, nombre, descripcion) VALUES
    ('general', 'General', 'Contenido general de la comunidad'),
    ('academica', 'Académica', 'Avisos académicos y tareas'),
    ('evento', 'Evento', 'Eventos estudiantiles o institucionales'),
    ('oportunidad', 'Oportunidad', 'Becas, empleos o convocatorias'),
    ('pregunta', 'Pregunta', 'Preguntas a la comunidad'),
    ('debate', 'Debate', 'Temas de debate y discusión');

-- Catálogo de reacciones
INSERT INTO catalogo_reacciones (codigo, nombre) VALUES
    ('me_gusta', 'Me gusta'),
    ('me_encanta', 'Me encanta'),
    ('interesante', 'Interesante'),
    ('apoyo', 'Apoyo'),
    ('felicidades', 'Felicidades');

-- Correos de prueba en el catálogo
INSERT INTO catalogo_correos (correo_institucional, matricula, carrera_id, cuatrimestre_id)
SELECT '20260001@universidad.edu', '20260001', c.id, cu.id
FROM carreras c CROSS JOIN cuatrimestres cu
WHERE c.codigo = 'SIS' AND cu.numero = 2;

INSERT INTO catalogo_correos (correo_institucional, matricula, carrera_id, cuatrimestre_id)
SELECT '20260002@universidad.edu', '20260002', c.id, cu.id
FROM carreras c CROSS JOIN cuatrimestres cu
WHERE c.codigo = 'MED' AND cu.numero = 3;

INSERT INTO catalogo_correos (correo_institucional, matricula, carrera_id, cuatrimestre_id)
SELECT '20260003@universidad.edu', '20260003', c.id, cu.id
FROM carreras c CROSS JOIN cuatrimestres cu
WHERE c.codigo = 'IND' AND cu.numero = 4;

INSERT INTO catalogo_correos (correo_institucional, matricula, carrera_id, cuatrimestre_id)
SELECT 'admin@universidad.edu', 'ADMIN01', c.id, cu.id
FROM carreras c CROSS JOIN cuatrimestres cu
WHERE c.codigo = 'SIS' AND cu.numero = 1;

-- =====================================================================
-- FIN DEL SETUP
-- =====================================================================

SELECT 'Base de datos upred_db creada y configurada exitosamente!' AS mensaje;
SELECT COUNT(*) AS total_carreras FROM carreras;
SELECT COUNT(*) AS correos_disponibles FROM catalogo_correos WHERE usado = FALSE;
