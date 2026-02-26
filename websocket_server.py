import os
from contextlib import contextmanager
from urllib.parse import quote_plus
import json
import uuid as uuid_pkg

from dotenv import load_dotenv
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import pymysql
from pymysql.cursors import DictCursor

app = Flask(__name__)

# Cargar variables desde .env si existe
load_dotenv()

# Configuración desde variables de entorno
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-key-change-me-in-production")
FLASK_ENV = os.getenv("FLASK_ENV", "development")
CORS_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))

# Configuración de MySQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306") or "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "upred_db")

# CORS para REST endpoints
CORS(app, origins=CORS_ORIGINS if CORS_ORIGINS != "*" else "*", supports_credentials=True)

# SocketIO con CORS configurable
socketio = SocketIO(
    app,
    cors_allowed_origins=CORS_ORIGINS,
    async_mode="eventlet",
    logger=FLASK_ENV == "development",
    engineio_logger=FLASK_ENV == "development",
)

# Almacenamiento en memoria de usuarios conectados
connected_users = {}  # {user_id: sid}



# =====================================================================
# CONEXIÓN A BASE DE DATOS MYSQL
# =====================================================================

@contextmanager
def get_db_connection():
    """Context manager para conexiones a la base de datos MySQL"""
    conn = None
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"[DB-ERROR] {e}")
        raise
    finally:
        if conn:
            conn.close()


# =====================================================================
# FUNCIONES DE BASE DE DATOS
# =====================================================================

def get_or_create_direct_chat(user_a_id, user_b_id):
    """Obtiene o crea una sala de chat directa entre dos usuarios"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Ordenar IDs para búsqueda consistente
            menor_id = min(int(user_a_id), int(user_b_id))
            mayor_id = max(int(user_a_id), int(user_b_id))
            
            # Intentar obtener sala existente
            cursor.execute("""
                SELECT id, sala_uuid
                FROM salas_chat
                WHERE tipo_sala = 'directo'
                AND LEAST(usuario_a_id, usuario_b_id) = %s
                AND GREATEST(usuario_a_id, usuario_b_id) = %s
            """, (menor_id, mayor_id))
            
            sala = cursor.fetchone()
            
            if sala:
                return sala
            
            # Crear nueva sala
            sala_uuid = str(uuid_pkg.uuid4())
            cursor.execute("""
                INSERT INTO salas_chat (sala_uuid, tipo_sala, usuario_a_id, usuario_b_id)
                VALUES (%s, 'directo', %s, %s)
            """, (sala_uuid, menor_id, mayor_id))
            
            # Obtener el ID insertado
            sala_id = cursor.lastrowid
            
            return {'id': sala_id, 'sala_uuid': sala_uuid}
            
    except Exception as e:
        print(f"[DB-ERROR] get_or_create_direct_chat: {e}")
        return None


def get_or_create_group_chat(group_id):
    """Obtiene o crea una sala de chat grupal"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Intentar obtener sala existente
            cursor.execute("""
                SELECT id, sala_uuid
                FROM salas_chat
                WHERE tipo_sala = 'grupal' AND grupo_id = %s
            """, (int(group_id),))
            
            sala = cursor.fetchone()
            
            if sala:
                return sala
            
            # Crear nueva sala
            sala_uuid = str(uuid_pkg.uuid4())
            cursor.execute("""
                INSERT INTO salas_chat (sala_uuid, tipo_sala, grupo_id)
                VALUES (%s, 'grupal', %s)
            """, (sala_uuid, int(group_id)))
            
            sala_id = cursor.lastrowid
            
            return {'id': sala_id, 'sala_uuid': sala_uuid}
            
    except Exception as e:
        print(f"[DB-ERROR] get_or_create_group_chat: {e}")
        return None


def save_message(sala_chat_id, sender_id, message_type, content, url_archivo=None, datos_archivo=None, metadatos=None):
    """Guarda un mensaje en la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            mensaje_uuid = str(uuid_pkg.uuid4())
            metadatos_json = json.dumps(metadatos or {})
            
            # Insertar mensaje
            cursor.execute("""
                INSERT INTO mensajes (mensaje_uuid, sala_chat_id, remitente_id, tipo_mensaje, contenido, url_archivo, datos_archivo, metadatos)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                mensaje_uuid,
                int(sala_chat_id),
                int(sender_id),
                message_type,
                content,
                url_archivo,
                datos_archivo,
                metadatos_json
            ))
            
            mensaje_id = cursor.lastrowid
            
            # Obtener el timestamp
            cursor.execute("SELECT enviado_en FROM mensajes WHERE id = %s", (mensaje_id,))
            result = cursor.fetchone()
            
            return {
                'id': mensaje_id,
                'mensaje_uuid': mensaje_uuid,
                'enviado_en': result['enviado_en']
            }
            
    except Exception as e:
        print(f"[DB-ERROR] save_message: {e}")
        return None


def mark_message_delivered(mensaje_id, destinatario_id):
    """Marca un mensaje como entregado a un destinatario"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO destinatarios_mensaje (mensaje_id, destinatario_id, entregado_en)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE entregado_en = NOW()
            """, (int(mensaje_id), int(destinatario_id)))
            
            return True
            
    except Exception as e:
        print(f"[DB-ERROR] mark_message_delivered: {e}")
        return False


def mark_message_read(mensaje_id, destinatario_id):
    """Marca un mensaje como leído"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO destinatarios_mensaje (mensaje_id, destinatario_id, entregado_en, leido_en)
                VALUES (%s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE entregado_en = NOW(), leido_en = NOW()
            """, (int(mensaje_id), int(destinatario_id)))
            
            return True
            
    except Exception as e:
        print(f"[DB-ERROR] mark_message_read: {e}")
        return False


def get_recent_messages(sala_chat_id, limit=50):
    """Obtiene los mensajes recientes de una sala"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    m.id, m.mensaje_uuid, m.remitente_id, m.tipo_mensaje,
                    m.contenido, m.url_archivo, m.enviado_en,
                    u.nombre, u.apellido_paterno
                FROM mensajes m
                JOIN usuarios u ON u.id = m.remitente_id
                WHERE m.sala_chat_id = %s AND m.eliminado_en IS NULL
                ORDER BY m.enviado_en DESC
                LIMIT %s
            """, (int(sala_chat_id), int(limit)))
            
            mensajes = cursor.fetchall()
            return list(reversed(mensajes))
            
    except Exception as e:
        print(f"[DB-ERROR] get_recent_messages: {e}")
        return []


def get_group_members(group_id):
    """Obtiene los IDs de los miembros activos de un grupo"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT usuario_id
                FROM miembros_grupo
                WHERE grupo_id = %s AND estado_membresia = 'activo'
            """, (int(group_id),))
            
            result = cursor.fetchall()
            return [str(row['usuario_id']) for row in result]
            
    except Exception as e:
        print(f"[DB-ERROR] get_group_members: {e}")
        return []


def search_user_by_email(email):
    """Busca un usuario por correo electrónico"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nombre, apellido_paterno, apellido_materno, correo_institucional
                FROM usuarios
                WHERE correo_institucional LIKE %s
                LIMIT 1
            """, (f"%{email}%",))
            
            result = cursor.fetchone()
            return result
            
    except Exception as e:
        print(f"[DB-ERROR] search_user_by_email: {e}")
        return None


def get_user_info(user_id):
    """Obtiene información del usuario"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nombre, apellido_paterno, apellido_materno, correo_institucional, foto_perfil_url
                FROM usuarios
                WHERE id = %s
            """, (int(user_id),))
            
            result = cursor.fetchone()
            return result
            
    except Exception as e:
        print(f"[DB-ERROR] get_user_info: {e}")
        return None

# =====================================================================
# WEBSOCKET HANDLERS
# =====================================================================

@app.route("/")
def health_check():
    return {
        "status": "ok",
        "service": "websocket_redUP_mysql",
        "database": "MySQL"
    }, 200


@socketio.on("connect")
def on_connect(auth=None):
    user_id = request.args.get("user_id")

    if not user_id:
        print("[CONNECT-ERROR] Conexión rechazada: falta user_id en query params")
        return False
    
    # Validación básica del user_id
    user_id = str(user_id).strip()
    if len(user_id) == 0 or len(user_id) > 100:
        print(f"[CONNECT-ERROR] user_id inválido: longitud={len(user_id)}")
        return False

    # Registrar usuario conectado
    connected_users[user_id] = request.sid
    
    # Unirse a room personal
    join_room(user_id)
    print(f"[CONNECT] user_id={user_id} | sid={request.sid} | unido a room='{user_id}'")

    emit(
        "connected",
        {
            "status": "connected",
            "user_id": user_id,
            "sid": request.sid,
            "timestamp": str(__import__('datetime').datetime.utcnow())
        },
    )


@socketio.on("disconnect")
def on_disconnect():
    # Encontrar y remover usuario de connected_users
    for user_id, sid in list(connected_users.items()):
        if sid == request.sid:
            del connected_users[user_id]
            print(f"[DISCONNECT] user_id={user_id} | sid={request.sid}")
            break
    else:
        print(f"[DISCONNECT] sid={request.sid} (usuario no encontrado)")


@socketio.on("search_user_by_email")
def on_search_user_by_email(data):
    """Busca un usuario por correo electrónico"""
    if not isinstance(data, dict):
        emit("error", {"message": "Payload inválido"})
        return
    
    email = data.get("email", "").strip()
    
    if not email:
        emit("error", {"message": "email es requerido"})
        return
    
    user = search_user_by_email(email)
    
    if user:
        emit("user_found", {
            "user_id": str(user['id']),
            "nombre": user['nombre'],
            "apellido_paterno": user['apellido_paterno'],
            "apellido_materno": user['apellido_materno'],
            "correo_institucional": user['correo_institucional'],
            "foto_perfil_url": user.get('foto_perfil_url')
        })
        print(f"[SEARCH_USER] email={email} | user_id={user['id']}")
    else:
        emit("user_not_found", {"message": f"Usuario con correo {email} no encontrado"})
        print(f"[SEARCH_USER_NOT_FOUND] email={email}")


@socketio.on("join_group")
def on_join_group(data):
    """Usuario se une a una sala de grupo"""
    if not isinstance(data, dict):
        emit("error", {"message": "Payload inválido para join_group"})
        return
    
    group_id = data.get("group_id")
    user_id = data.get("user_id")
    
    if not group_id or not user_id:
        emit("error", {"message": "group_id y user_id son requeridos"})
        return
    
    room = f"group_{group_id}"
    join_room(room)
    
    print(f"[JOIN_GROUP] user_id={user_id} | group_id={group_id} | room={room} | sid={request.sid}")
    
    emit("joined_group", {
        "group_id": str(group_id),
        "user_id": str(user_id),
        "room": room,
        "status": "joined",
        "timestamp": str(__import__('datetime').datetime.utcnow())
    })
    
    # Notificar a otros miembros
    emit("user_joined_group", {
        "group_id": str(group_id),
        "user_id": str(user_id),
        "timestamp": str(__import__('datetime').datetime.utcnow())
    }, room=room, skip_sid=request.sid)


@socketio.on("leave_group")
def on_leave_group(data):
    """Usuario saliente de una sala de grupo"""
    if not isinstance(data, dict):
        emit("error", {"message": "Payload inválido para leave_group"})
        return
    
    group_id = data.get("group_id")
    user_id = data.get("user_id")
    
    if not group_id or not user_id:
        emit("error", {"message": "group_id y user_id son requeridos"})
        return
    
    room = f"group_{group_id}"
    leave_room(room)
    
    print(f"[LEAVE_GROUP] user_id={user_id} | group_id={group_id} | room={room}")
    
    emit("left_group", {
        "group_id": str(group_id),
        "user_id": str(user_id),
        "status": "left",
        "timestamp": str(__import__('datetime').datetime.utcnow())
    })
    
    # Notificar a otros miembros
    emit("user_left_group", {
        "group_id": str(group_id),
        "user_id": str(user_id),
        "timestamp": str(__import__('datetime').datetime.utcnow())
    }, room=room)


@socketio.on("send_direct_message")
def on_send_direct_message(data):
    """Envía un mensaje directo entre dos usuarios"""
    if not isinstance(data, dict):
        emit("error", {"message": "Payload inválido"})
        return
    
    sender_id = data.get("sender_id")
    recipient_id = data.get("recipient_id")
    message_type = data.get("type", "texto")
    content = data.get("content")
    file_url = data.get("file_url")
    
    if not sender_id or not recipient_id:
        emit("error", {"message": "sender_id y recipient_id son requeridos"})
        return
    
    if not content and not file_url:
        emit("error", {"message": "content o file_url es requerido"})
        return
    
    # Obtener o crear sala de chat
    sala = get_or_create_direct_chat(sender_id, recipient_id)
    if not sala:
        emit("error", {"message": "No se pudo crear la sala de chat"})
        return
    
    # Obtener información del remitente
    sender_info = get_user_info(sender_id)
    if not sender_info:
        emit("error", {"message": "No se pudo obtener información del remitente"})
        return
    
    # Guardar mensaje en BD
    mensaje = save_message(
        sala['id'],
        sender_id,
        message_type,
        content,
        file_url,
        None,
        data.get("metadata", {})
    )
    
    if not mensaje:
        emit("error", {"message": "No se pudo guardar el mensaje"})
        return
    
    # Marcar como entregado para el destinatario
    mark_message_delivered(mensaje['id'], recipient_id)
    
    # Emitir a ambos usuarios
    message_data = {
        "message_id": mensaje['id'],
        "message_uuid": mensaje['mensaje_uuid'],
        "sender_id": str(sender_id),
        "sender_nombre": sender_info['nombre'],
        "sender_apellido": sender_info['apellido_paterno'],
        "recipient_id": str(recipient_id),
        "type": message_type,
        "content": content,
        "file_url": file_url,
        "timestamp": str(mensaje['enviado_en']),
        "sala_uuid": sala['sala_uuid'],
        "status": "delivered"
    }
    
    # Enviar al remitente (confirmación)
    emit("message_sent", message_data, room=str(sender_id))
    
    # Enviar al destinatario
    emit("new_message", message_data, room=str(recipient_id))
    
    print(f"[DIRECT_MESSAGE] {sender_id} -> {recipient_id} | mensaje_id={mensaje['id']}")


@socketio.on("send_group_message")
def on_send_group_message(data):
    """Envía un mensaje a un grupo"""
    if not isinstance(data, dict):
        emit("error", {"message": "Payload inválido"})
        return
    
    sender_id = data.get("sender_id")
    group_id = data.get("group_id")
    message_type = data.get("type", "texto")
    content = data.get("content")
    file_url = data.get("file_url")
    
    if not sender_id or not group_id:
        emit("error", {"message": "sender_id y group_id son requeridos"})
        return
    
    if not content and not file_url:
        emit("error", {"message": "content o file_url es requerido"})
        return
    
    # Obtener o crear sala grupal
    sala = get_or_create_group_chat(group_id)
    if not sala:
        emit("error", {"message": "No se pudo crear la sala de chat grupal"})
        return
    
    # Obtener información del remitente
    sender_info = get_user_info(sender_id)
    if not sender_info:
        emit("error", {"message": "No se pudo obtener información del remitente"})
        return
    
    # Guardar mensaje en BD
    mensaje = save_message(
        sala['id'],
        sender_id,
        message_type,
        content,
        file_url,
        None,
        data.get("metadata", {})
    )
    
    if not mensaje:
        emit("error", {"message": "No se pudo guardar el mensaje"})
        return
    
    # Obtener miembros del grupo
    members = get_group_members(group_id)
    
    # Marcar como entregado para todos los miembros
    for member_id in members:
        if str(member_id) != str(sender_id):
            mark_message_delivered(mensaje['id'], member_id)
    
    # Emitir a todos los miembros del grupo
    message_data = {
        "message_id": mensaje['id'],
        "message_uuid": mensaje['mensaje_uuid'],
        "sender_id": str(sender_id),
        "sender_nombre": sender_info['nombre'],
        "sender_apellido": sender_info['apellido_paterno'],
        "group_id": str(group_id),
        "type": message_type,
        "content": content,
        "file_url": file_url,
        "timestamp": str(mensaje['enviado_en']),
        "sala_uuid": sala['sala_uuid'],
        "status": "delivered"
    }
    
    room = f"group_{group_id}"
    
    # Enviar a todos en el grupo (incluyendo remitente)
    emit("new_group_message", message_data, room=room)
    
    print(f"[GROUP_MESSAGE] sender={sender_id} | group={group_id} | mensaje_id={mensaje['id']} | miembros={len(members)}")


@socketio.on("mark_as_read")
def on_mark_as_read(data):
    """Marca un mensaje como leído"""
    if not isinstance(data, dict):
        emit("error", {"message": "Payload inválido"})
        return
    
    message_id = data.get("message_id")
    user_id = data.get("user_id")
    
    if not message_id or not user_id:
        emit("error", {"message": "message_id y user_id son requeridos"})
        return
    
    success = mark_message_read(message_id, user_id)
    
    if success:
        emit("message_read_confirmed", {
            "message_id": message_id,
            "user_id": str(user_id),
            "timestamp": str(__import__('datetime').datetime.utcnow())
        })
        print(f"[MESSAGE_READ] mensaje={message_id} | usuario={user_id}")


@socketio.on("typing")
def on_typing(data):
    """Notifica que alguien está escribiendo"""
    if not isinstance(data, dict):
        emit("error", {"message": "Payload inválido"})
        return
    
    sender_id = data.get("sender_id")
    recipient_id = data.get("recipient_id")
    group_id = data.get("group_id")
    
    if not sender_id:
        emit("error", {"message": "sender_id es requerido"})
        return
    
    if group_id:
        # Notificación grupal
        room = f"group_{group_id}"
        emit("user_typing", {
            "user_id": str(sender_id),
            "group_id": str(group_id),
            "timestamp": str(__import__('datetime').datetime.utcnow())
        }, room=room, skip_sid=request.sid)
        print(f"[TYPING_GROUP] user_id={sender_id} | group_id={group_id}")
    elif recipient_id:
        # Notificación individual
        emit("user_typing", {
            "user_id": str(sender_id),
            "recipient_id": str(recipient_id),
            "timestamp": str(__import__('datetime').datetime.utcnow())
        }, room=str(recipient_id))
        print(f"[TYPING] user_id={sender_id} | recipient_id={recipient_id}")


@socketio.on("stop_typing")
def on_stop_typing(data):
    """Notifica que alguien dejó de escribir"""
    if not isinstance(data, dict):
        emit("error", {"message": "Payload inválido"})
        return
    
    sender_id = data.get("sender_id")
    recipient_id = data.get("recipient_id")
    group_id = data.get("group_id")
    
    if not sender_id:
        emit("error", {"message": "sender_id es requerido"})
        return
    
    if group_id:
        # Notificación grupal
        room = f"group_{group_id}"
        emit("user_stopped_typing", {
            "user_id": str(sender_id),
            "group_id": str(group_id),
            "timestamp": str(__import__('datetime').datetime.utcnow())
        }, room=room, skip_sid=request.sid)
    elif recipient_id:
        # Notificación individual
        emit("user_stopped_typing", {
            "user_id": str(sender_id),
            "recipient_id": str(recipient_id),
            "timestamp": str(__import__('datetime').datetime.utcnow())
        }, room=str(recipient_id))


@socketio.on("get_online_users")
def on_get_online_users():
    """Obtiene lista de usuarios en línea"""
    online_users = list(connected_users.keys())
    emit("online_users", {
        "users": online_users,
        "total": len(online_users),
        "timestamp": str(__import__('datetime').datetime.utcnow())
    })
    print(f"[GET_ONLINE_USERS] total={len(online_users)}")


@socketio.on("get_chat_history")
def on_get_chat_history(data):
    """Obtiene el historial de mensajes de una sala"""
    if not isinstance(data, dict):
        emit("error", {"message": "Payload inválido"})
        return
    
    user_a_id = data.get("user_a_id")
    user_b_id = data.get("user_b_id")
    group_id = data.get("group_id")
    limit = data.get("limit", 50)
    
    sala = None
    
    if group_id:
        sala = get_or_create_group_chat(group_id)
    elif user_a_id and user_b_id:
        sala = get_or_create_direct_chat(user_a_id, user_b_id)
    
    if not sala:
        emit("error", {"message": "No se pudo obtener la sala de chat"})
        return
    
    mensajes = get_recent_messages(sala['id'], limit)
    
    emit("chat_history", {
        "sala_uuid": sala['sala_uuid'],
        "messages": mensajes
    })
    
    print(f"[CHAT_HISTORY] sala_id={sala['id']} | mensajes={len(mensajes)}")


if __name__ == "__main__":
    socketio.run(
        app,
        host=HOST,
        port=PORT,
        debug=FLASK_ENV == "development"
    )
