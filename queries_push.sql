-- 🔍 Queries para Diagnosticar Notificaciones Push
-- Ejecutar en: mysql -u root upred_db < queries_push.sql

-- ============================================================
-- 1. Estado General de Dispositivos
-- ============================================================
SELECT 
    '=== RESUMEN GENERAL ===' as info;

SELECT 
    CONCAT(
        'Total de usuarios: ',
        (SELECT COUNT(*) FROM usuarios),
        ' | Dispositivos registrados: ',
        (SELECT COUNT(*) FROM dispositivos_usuario),
        ' | Con token push: ',
        (SELECT COUNT(*) FROM dispositivos_usuario WHERE token_push IS NOT NULL)
    ) as estado;

-- ============================================================
-- 2. Usuarios SIN Dispositivo Registrado
-- ============================================================
SELECT 
    '=== USUARIOS SIN DISPOSITIVO ===' as info;

SELECT 
    u.id,
    u.nombre,
    u.apellido_paterno,
    u.correo_institucional,
    'SIN DISPOSITIVO' as estado
FROM usuarios u
WHERE u.id NOT IN (SELECT DISTINCT usuario_id FROM dispositivos_usuario)
LIMIT 10;

-- ============================================================
-- 3. Dispositivos por Usuario (últimos 20)
-- ============================================================
SELECT 
    '=== DISPOSITIVOS REGISTRADOS ===' as info;

SELECT 
    du.id,
    du.usuario_id,
    u.nombre,
    u.apellido_paterno,
    du.plataforma,
    SUBSTRING(du.token_push, 1, 20) as token_preview,
    IF(du.token_push IS NULL, '❌ SIN TOKEN', '✅ CON TOKEN') as estado_token,
    IF(du.activo = 1, '✅ ACTIVO', '❌ INACTIVO') as estado_activo,
    du.ultima_actividad_en,
    du.creado_en
FROM dispositivos_usuario du
LEFT JOIN usuarios u ON du.usuario_id = u.id
ORDER BY du.ultima_actividad_en DESC
LIMIT 20;

-- ============================================================
-- 4. Detalle de Dispositivos por Usuario
-- ============================================================
SELECT 
    '=== REVISAR USUARIO ESPECÍFICO ===' as info;
SELECT 'Para revisar usuario específico, cambiar "2" por su ID' as instruccion;

SELECT 
    du.*,
    u.nombre as usuario_nombre,
    u.apellido_paterno as usuario_apellido
FROM dispositivos_usuario du
LEFT JOIN usuarios u ON du.usuario_id = u.id
WHERE du.usuario_id = 2;

-- ============================================================
-- 5. Notificaciones Generadas (últimas 30)
-- ============================================================
SELECT 
    '=== ÚLTIMAS NOTIFICACIONES ===' as info;

SELECT 
    n.id,
    n.usuario_id,
    u.nombre,
    n.tipo,
    n.titulo,
    SUBSTRING(n.cuerpo, 1, 40) as cuerpo_preview,
    IF(n.leida = 1, '✅ LEÍDA', '❌ NO LEÍDA') as estado,
    n.creada_en
FROM notificaciones n
LEFT JOIN usuarios u ON n.usuario_id = u.id
ORDER BY n.creada_en DESC
LIMIT 30;

-- ============================================================
-- 6. Notificaciones de tipo "nuevo_seguidor"
-- ============================================================
SELECT 
    '=== NOTIFICACIONES NUEVO_SEGUIDOR ===' as info;

SELECT 
    n.id,
    n.usuario_id,
    u.nombre,
    n.cuerpo,
    IF(n.leida = 1, 'LEÍDA', 'NO LEÍDA') as estado,
    n.creada_en
FROM notificaciones n
LEFT JOIN usuarios u ON n.usuario_id = u.id
WHERE n.tipo = 'nuevo_seguidor'
ORDER BY n.creada_en DESC
LIMIT 20;

-- ============================================================
-- 7. Notificaciones de tipo "nuevo_comentario"
-- ============================================================
SELECT 
    '=== NOTIFICACIONES NUEVO_COMENTARIO ===' as info;

SELECT 
    n.id,
    n.usuario_id,
    u.nombre,
    n.cuerpo,
    IF(n.leida = 1, 'LEÍDA', 'NO LEÍDA') as estado,
    n.creada_en
FROM notificaciones n
LEFT JOIN usuarios u ON n.usuario_id = u.id
WHERE n.tipo = 'nuevo_comentario'
ORDER BY n.creada_en DESC
LIMIT 20;

-- ============================================================
-- 8. Verificar Integridad de Datos
-- ============================================================
SELECT 
    '=== VERIFICACIÓN DE INTEGRIDAD ===' as info;

SELECT 
    CONCAT(
        'Usuarios: ', COUNT(DISTINCT u.id), ' | ',
        'Dispositivos huérfanos: ', 
        COUNT(DISTINCT CASE WHEN u.id IS NULL THEN du.id END)
    ) as integridad
FROM dispositivos_usuario du
LEFT JOIN usuarios u ON du.usuario_id = u.id;

-- ============================================================
-- 9. Estadísticas por Usuario
-- ============================================================
SELECT 
    '=== ESTADÍSTICAS POR USUARIO ===' as info;

SELECT 
    u.id,
    u.nombre,
    u.apellido_paterno,
    COUNT(DISTINCT du.id) as dispositivos,
    SUM(CASE WHEN du.token_push IS NOT NULL THEN 1 ELSE 0 END) as con_token,
    COUNT(DISTINCT n.id) as notificaciones,
    SUM(CASE WHEN n.leida = 0 THEN 1 ELSE 0 END) as no_leidas
FROM usuarios u
LEFT JOIN dispositivos_usuario du ON u.id = du.usuario_id
LEFT JOIN notificaciones n ON u.id = n.usuario_id
GROUP BY u.id, u.nombre, u.apellido_paterno
LIMIT 20;

-- ============================================================
-- 10. Actividad Reciente de Dispositivos
-- ============================================================
SELECT 
    '=== ACTIVIDAD RECIENTE ===' as info;

SELECT 
    du.usuario_id,
    u.nombre,
    u.apellido_paterno,
    du.plataforma,
    du.activo,
    du.ultima_actividad_en,
    TIMESTAMPDIFF(MINUTE, du.ultima_actividad_en, NOW()) as minutos_sin_actividad
FROM dispositivos_usuario du
LEFT JOIN usuarios u ON du.usuario_id = u.id
ORDER BY du.ultima_actividad_en DESC
LIMIT 20;

-- ============================================================
-- 11. CHECK: Tokens Push Válidos (No empty, No NULL)
-- ============================================================
SELECT 
    '=== TOKENS PUSH VÁLIDOS ===' as info;

SELECT 
    COUNT(*) as total_dispositivos,
    SUM(CASE WHEN token_push IS NOT NULL AND token_push != '' THEN 1 ELSE 0 END) as con_token_valido,
    SUM(CASE WHEN token_push IS NULL OR token_push = '' THEN 1 ELSE 0 END) as sin_token
FROM dispositivos_usuario;

-- ============================================================
-- 12. Exportar Dispositivos para Debug (Anonymized)
-- ============================================================
SELECT 
    '=== EXPORT: DISPOSITIVOS ANÓNIMOS ===' as info;

SELECT 
    user_id,
    device_count,
    valid_tokens,
    invalid_tokens,
    last_activity
FROM (
    SELECT 
        du.usuario_id as user_id,
        COUNT(*) as device_count,
        SUM(CASE WHEN du.token_push IS NOT NULL AND du.token_push != '' THEN 1 ELSE 0 END) as valid_tokens,
        SUM(CASE WHEN du.token_push IS NULL OR du.token_push = '' THEN 1 ELSE 0 END) as invalid_tokens,
        MAX(du.ultima_actividad_en) as last_activity
    FROM dispositivos_usuario du
    GROUP BY du.usuario_id
) subq
ORDER BY device_count DESC, last_activity DESC;

-- ============================================================
-- COMANDOS ÚTILES
-- ============================================================
-- Ver todo sobre usuario 2:
-- SELECT * FROM usuarios WHERE id = 2;
-- SELECT * FROM dispositivos_usuario WHERE usuario_id = 2;
-- SELECT * FROM notificaciones WHERE usuario_id = 2;

-- Limpiar dispositivos antiguos (sin actividad en 30 días):
-- DELETE FROM dispositivos_usuario WHERE ultima_actividad_en < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Reactivar todos los dispositivos:
-- UPDATE dispositivos_usuario SET activo = 1;

-- Limpiar tokens nulos:
-- DELETE FROM dispositivos_usuario WHERE token_push IS NULL OR token_push = '';
