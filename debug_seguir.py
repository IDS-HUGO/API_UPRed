#!/usr/bin/env python3
"""
Debug específico del error 400 en seguir usuario
Ejecutar en EC2: python3 debug_seguir.py
"""

import mysql.connector
from mysql.connector import Error

def debug_seguir_error():
    """Debug del error 400 en POST /api/usuarios/1/seguir"""

    print("🐛 DEBUG: Error 400 en seguir usuario")
    print("=" * 50)

    try:
        # Conectar a BD
        connection = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
            database="upred_db"
        )

        cursor = connection.cursor(dictionary=True)

        print("\n1️⃣ Verificando usuarios involucrados:")

        # Usuario que hace la petición (current_user - seguidor)
        cursor.execute("SELECT id, nombre, apellido_paterno, correo_institucional FROM usuarios WHERE id = 2")
        seguidor = cursor.fetchone()
        print(f"   Seguidor (usuario autenticado): {seguidor}")

        # Usuario a seguir (usuario_id = 1)
        cursor.execute("SELECT id, nombre, apellido_paterno, correo_institucional FROM usuarios WHERE id = 1")
        seguido = cursor.fetchone()
        print(f"   Seguido (usuario objetivo): {seguido}")

        print("\n2️⃣ Verificando si ya existe relación:")

        # Verificar relación de seguimiento
        cursor.execute("""
            SELECT * FROM seguidores
            WHERE seguidor_id = 2 AND seguido_id = 1
        """)
        relacion_existente = cursor.fetchone()

        if relacion_existente:
            print("   ❌ YA EXISTE relación de seguimiento")
            print(f"   Detalles: {relacion_existente}")
            print("   💡 CAUSA DEL ERROR 400: 'Ya sigues a este usuario'")
            return "YA_SIGUE"
        else:
            print("   ✅ NO existe relación de seguimiento previa")

        print("\n3️⃣ Verificando auto-seguimiento:")

        if 2 == 1:  # seguidor_id == seguido_id
            print("   ❌ Intento de auto-seguimiento")
            print("   💡 CAUSA DEL ERROR 400: 'No puedes seguirte a ti mismo'")
            return "AUTO_SEGUIMIENTO"
        else:
            print("   ✅ No es auto-seguimiento")

        print("\n4️⃣ Verificando dispositivos para push:")

        cursor.execute("""
            SELECT id, usuario_id, plataforma, token_push, activo, ultima_actividad_en
            FROM dispositivos_usuario
            WHERE usuario_id = 1 AND activo = 1 AND token_push IS NOT NULL
            ORDER BY ultima_actividad_en DESC
        """)
        dispositivos = cursor.fetchall()

        if dispositivos:
            print(f"   ✅ Usuario 1 tiene {len(dispositivos)} dispositivo(s) activo(s) con token")
            for disp in dispositivos:
                token_preview = disp['token_push'][:20] + "..." if disp['token_push'] else "NULL"
                print(f"      - ID: {disp['id']}, Plataforma: {disp['plataforma']}, Token: {token_preview}")
        else:
            print("   ❌ Usuario 1 NO tiene dispositivos activos con token push")
            print("   💡 POR ESTO NO LLEGAN LAS NOTIFICACIONES")

        print("\n5️⃣ Verificando estado de la BD:")

        cursor.execute("SELECT COUNT(*) as total FROM seguidores")
        total_seguidores = cursor.fetchone()['total']
        print(f"   Total relaciones de seguimiento: {total_seguidores}")

        cursor.execute("SELECT COUNT(*) as total FROM dispositivos_usuario")
        total_dispositivos = cursor.fetchone()['total']
        print(f"   Total dispositivos registrados: {total_dispositivos}")

        cursor.execute("SELECT COUNT(*) as total FROM notificaciones WHERE tipo = 'nuevo_seguidor'")
        total_notif_seguidores = cursor.fetchone()['total']
        print(f"   Notificaciones de nuevos seguidores: {total_notif_seguidores}")

        cursor.close()
        connection.close()

        print("\n" + "=" * 50)
        print("📊 RESUMEN:")

        if relacion_existente:
            print("❌ ERROR 400: Usuario 2 ya sigue a usuario 1")
            print("💡 SOLUCIÓN: Dejar de seguir primero, o verificar lógica en app")
        else:
            print("✅ Debería poder seguir - verificar código de la API")

        if not dispositivos:
            print("❌ PUSH: No hay dispositivos registrados para usuario 1")
            print("💡 SOLUCIÓN: La app móvil debe registrar dispositivo después de login")

        return "DEBUG_COMPLETED"

    except Error as e:
        print(f"❌ Error de BD: {e}")
        return "DB_ERROR"

if __name__ == "__main__":
    debug_seguir_error()
