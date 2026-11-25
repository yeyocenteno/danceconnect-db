from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db, Clase, Usuario, ClaseFeed, ClaseDetalle
from utils import generar_uuid
import datetime
import json
# import redis

# Definición del Blueprint para las clases
classes_bp = Blueprint('classes', __name__, url_prefix='/classes')

# Redis deshabilitado temporalmente: conectaba al Nodo 2 por Tailscale (100.84.246.110)
# redis_client = redis.Redis(
#     host='100.84.246.110', # <-- LA IP DE TU COMPAÑERO
#     port=6379,
#     db=0,
#     decode_responses=True
# )

# ----------------------------------------------------
# 1. GET /classes/ (FEED FRAGMENTADO CON CAPA NOSQL)
# ----------------------------------------------------
@classes_bp.route('/', methods=['GET'])
def get_all_classes():
    # Caché Redis comentada temporalmente para evitar TimeoutError si el Nodo 2 no responde
    # try:
    #     # Intentamos buscar el Feed fragmentado en la caché de Redis (NoSQL)
    #     cached_feed = redis_client.get('danceconnect_feed')
    #     if cached_feed:
    #         print(">>> [NOSQL] Datos recuperados desde Redis en Nodo 2")
    #         return jsonify(json.loads(cached_feed)), 200
    # except redis.ConnectionError:
    #     print(">>> [ADVERTENCIA] NoSQL inaccesible. Usando fallback.")

    # Consultamos directamente la vista fragmentada en MySQL (Nodo 1)
    print(">>> [MYSQL] Datos consultados desde Vista Fragmentada")
    clases_feed = ClaseFeed.query.all()
    
    results = []
    for c in clases_feed:
        results.append({
            'id': str(c.id),
            'publisherId': str(c.publisherId or ""),
            'publisherUsername': c.instructor.username if c.instructor else "Usuario Desconocido",
            'publisherImageUrl': c.instructor.picture if c.instructor else "",
            'publishDate': c.publishDate.strftime('%Y-%m-%d') if c.publishDate else "",
            'title': c.name or "Sin título",
            'style': c.style or "",
            'difficulty': c.difficulty or "",
            'date': c.publishDate.strftime('%Y-%m-%d') if c.publishDate else "",
            'imageUrl': c.thumbnailUrl or "https://via.placeholder.com/300",
            'instructorName': c.instructor.name if c.instructor else "Instructor Desconocido",
            'isAvailable': True
        })

    # Guardado en caché Redis comentado temporalmente
    # try:
    #     redis_client.setex('danceconnect_feed', 3600, json.dumps(results))
    # except redis.ConnectionError:
    #     pass

    return jsonify(results), 200

# ----------------------------------------------------
# 2. GET /classes/<id> (Detalle - Blindaje total)
# ----------------------------------------------------
@classes_bp.route('/<string:class_id>', methods=['GET'])
def get_class_by_id(class_id):
    # Intentamos obtener la clase. Si no existe, error 404.
    c = Clase.query.get(class_id)
    if not c:
        return abort(404, description=f"Clase no encontrada")
    
    # CONSTRUCCIÓN BLINDADA:
    # Convertimos explícitamente todo a str(). Si es None, será "" (string vacío).
    # Esto evita el NullPointerException en la app Android.
    
    data = {
        'id': str(c.id or ""),
        'publisherId': str(c.publisherId or ""),
        'publisherUsername': str(c.instructor.username if c.instructor else "Usuario Desconocido"),
        'publisherImageUrl': str(c.instructor.picture if c.instructor else ""),
        'publishDate': str(c.publishDate.strftime('%Y-%m-%d') if c.publishDate else ""),
        'title': str(c.name or "Sin título"),
        'description': str(c.description or ""),
        'style': str(c.style or ""),
        'difficulty': str(c.difficulty or ""),
        'imageUrl': str(c.thumbnailUrl or ""),
        'videoUrl': str(c.videoUrl or ""),
        'duration': int(c.duration) if c.duration is not None else 0, # Este es el único int, los demás son texto
        'date': str(c.publishDate.strftime('%Y-%m-%d') if c.publishDate else ""),
        'instructorName': str(c.instructor.name if c.instructor else "Instructor Desconocido"),
        'isAvailable': True,
        'totalFavorites': int(len(c.usuarios_que_les_gusta)) if hasattr(c, 'usuarios_que_les_gusta') else 0
    }
    
    return jsonify(data), 200

# ----------------------------------------------------
# 3. GET /classes/me (Clases del usuario logueado)
# ----------------------------------------------------
@classes_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_classes():
    """Retorna solo las clases publicadas por el usuario logueado (para su Perfil)."""
    current_user_id = get_jwt_identity()
    
    # Consulta directa filtrando por el ID del publicador
    clases_db = Clase.query.filter_by(publisherId=current_user_id).all()
    
    results = []
    for c in clases_db:
        results.append({
            'id': c.id,
            'publisherId': c.publisherId,
            'title': c.name,
            'style': c.style,
            'difficulty': c.difficulty,
            'imageUrl': c.thumbnailUrl,
            'description': c.description,
            'totalFavorites': len(c.usuarios_que_les_gusta)
        })
        
    return jsonify(results), 200

# ----------------------------------------------------
# 4. POST /classes/ (Crear clase en MySQL)
# ----------------------------------------------------
@classes_bp.route('/', methods=['POST'])
@jwt_required()
def create_class():
    current_user_id = get_jwt_identity()
    client_data = request.get_json(silent=True)
    
    if not client_data:
        return jsonify({"error": "JSON inválido"}), 400

    # Validar campos REQUERIDOS
    required_fields = ['title', 'style', 'difficulty', 'imageUrl']
    for field in required_fields:
        if field not in client_data:
            return jsonify({"error": f"Falta el campo requerido: {field}"}), 400

    # Buscamos al instructor en la DB para verificar que existe
    instructor = Usuario.query.get(current_user_id)
    if not instructor:
        return jsonify({"error": "El usuario autenticado no existe en la base de datos"}), 404

    # Instanciamos el objeto con el modelo SQLAlchemy
    nueva_clase = Clase(
        id=generar_uuid(),
        publisherId=current_user_id,
        name=client_data['title'],
        description=client_data.get('description', "Aprende los mejores pasos en esta clase..."),
        style=client_data['style'],
        duration=client_data.get('duration', 60),  # Valor por defecto en minutos
        difficulty=client_data['difficulty'],
        videoUrl=client_data.get('videoUrl', ""),
        thumbnailUrl=client_data['imageUrl'],
        publishDate=datetime.datetime.utcnow()
    )

    # Guardamos en el Maestro (Docker se encarga de replicarlo al esclavo)
    db.session.add(nueva_clase)
    db.session.commit()

    # Invalidación de caché Redis comentada temporalmente
    # try:
    #     redis_client.delete('danceconnect_feed')
    #     print(">>> [NOSQL] Caché invalidada por nueva clase")
    # except redis.ConnectionError:
    #     pass

    # Estructuramos la respuesta para mantener compatibilidad absoluta con Kotlin sin romper el parseo
    response_data = {
        'id': nueva_clase.id,
        'publisherId': nueva_clase.publisherId,
        'publisherUsername': instructor.username or instructor.name,
        'publisherImageUrl': instructor.picture or "",
        'publishDate': nueva_clase.publishDate.strftime('%Y-%m-%d'),
        'title': nueva_clase.name,
        'style': nueva_clase.style,
        'difficulty': nueva_clase.difficulty,
        'imageUrl': nueva_clase.thumbnailUrl,
        'description': nueva_clase.description,
        'instructorName': instructor.name,
        'totalFavorites': 0,
        'isAvailable': True
    }

    return jsonify(response_data), 201

# ----------------------------------------------------
# 5. PUT /classes/<id> (Actualizar clase)
# ----------------------------------------------------
@classes_bp.route('/<string:class_id>', methods=['PUT'])
@jwt_required()
def update_class(class_id):
    current_user_id = get_jwt_identity()
    payload = request.get_json(silent=True)
    
    if not payload:
        return jsonify({"error": "JSON inválido"}), 400

    clase = Clase.query.get(class_id)
    if not clase:
        return abort(404, description=f"Clase con ID {class_id} no encontrada para actualizar")

    # Sistema de seguridad: Verificar propiedad (dueño)
    if clase.publisherId != current_user_id:
        return abort(403, description="No tienes permiso para editar esta clase.")
    
    # Actualizamos únicamente los campos permitidos
    if 'title' in payload:
        clase.name = payload['title']
    if 'description' in payload:
        clase.description = payload['description']
    if 'style' in payload:
        clase.style = payload['style']
    if 'difficulty' in payload:
        clase.difficulty = payload['difficulty']
    if 'imageUrl' in payload:
        clase.thumbnailUrl = payload['imageUrl']
    if 'videoUrl' in payload:
        clase.videoUrl = payload['videoUrl']
    if 'duration' in payload:
        clase.duration = payload['duration']

    db.session.commit()  # Sincroniza los cambios con el Maestro
    return jsonify({"mensaje": "Clase actualizada exitosamente en MySQL"}), 200

# ----------------------------------------------------
# 6. DELETE /classes/<id> (Eliminar clase)
# ----------------------------------------------------
@classes_bp.route('/<string:class_id>', methods=['DELETE'])
@jwt_required()
def delete_class(class_id):
    current_user_id = get_jwt_identity()
    
    clase = Clase.query.get(class_id)
    if not clase:
        return abort(404, description=f"Clase con ID {class_id} no encontrada para eliminar")
        
    # Verificar propiedad (dueño)
    if clase.publisherId != current_user_id:
        return abort(403, description="No tienes permiso para eliminar esta clase.")
        
    # Eliminación física del registro
    db.session.delete(clase)
    db.session.commit()
    
    # Invalidación de caché Redis comentada temporalmente
    # try:
    #     redis_client.delete('danceconnect_feed')
    #     print(">>> [NOSQL] Caché invalidada por eliminación de clase")
    # except redis.ConnectionError:
    #     pass
    
    return jsonify({"mensaje": f"Clase {class_id} eliminada de forma permanente"}), 200
