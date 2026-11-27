from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db, Clase, Usuario, ClaseFeed, ClaseDetalle
from utils import generar_uuid
import datetime

classes_bp = Blueprint('classes', __name__, url_prefix='/classes')


def _serialize_class_summary(c):
    return {
        'id': str(c.id),
        'publisherId': str(c.publisherId or ""),
        'publisherUsername': c.instructor.username if c.instructor else "Usuario Desconocido",
        'publisherImageUrl': c.instructor.picture if c.instructor else "",
        'publishDate': c.publishDate.strftime('%Y-%m-%d') if c.publishDate else "",
        'title': c.name or "Sin título",
        'style': c.style or "",
        'discipline': c.discipline or "",
        'subdiscipline': c.subdiscipline,
        'startTime': c.startTime,
        'endTime': c.endTime,
        'time': c.startTime or "",
        'difficulty': c.difficulty or "",
        'date': c.publishDate.strftime('%Y-%m-%d') if c.publishDate else "",
        'imageUrl': c.thumbnailUrl or "https://via.placeholder.com/300",
        'instructorName': c.instructor.name if c.instructor else "Instructor Desconocido",
        'isAvailable': True
    }


# ----------------------------------------------------
# 1. GET /classes/ (FEED GENERAL)
# ----------------------------------------------------
@classes_bp.route('/', methods=['GET'], strict_slashes=False)
def get_all_classes():
    clases_feed = Clase.query.all()
    results = [_serialize_class_summary(c) for c in clases_feed]
    return jsonify(results), 200


# ----------------------------------------------------
# 2. GET /classes/<id> (Detalle)
# ----------------------------------------------------
@classes_bp.route('/<string:class_id>', methods=['GET'])
def get_class_by_id(class_id):
    c = Clase.query.get(class_id)
    if not c:
        return abort(404, description="Clase no encontrada")

    data = {
        'id': str(c.id or ""),
        'publisherId': str(c.publisherId or ""),
        'publisherUsername': str(c.instructor.username if c.instructor else "Usuario Desconocido"),
        'publisherImageUrl': str(c.instructor.picture if c.instructor else ""),
        'publishDate': str(c.publishDate.strftime('%Y-%m-%d') if c.publishDate else ""),
        'title': str(c.name or "Sin título"),
        'description': str(c.description or ""),
        'style': str(c.style or ""),
        'discipline': str(c.discipline or ""),
        'subdiscipline': c.subdiscipline,
        'startTime': c.startTime,
        'endTime': c.endTime,
        'time': str(c.startTime or ""),
        'difficulty': str(c.difficulty or ""),
        'imageUrl': str(c.thumbnailUrl or ""),
        'videoUrl': str(c.videoUrl or ""),
        'duration': int(c.duration) if c.duration is not None else 0,
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
    current_user_id = get_jwt_identity()
    clases_db = Clase.query.filter_by(publisherId=current_user_id).all()

    results = []
    for c in clases_db:
        results.append({
            'id': c.id,
            'publisherId': c.publisherId,
            'title': c.name,
            'style': c.style,
            'discipline': c.discipline or "",
            'subdiscipline': c.subdiscipline,
            'startTime': c.startTime,
            'endTime': c.endTime,
            'time': c.startTime or "",
            'difficulty': c.difficulty,
            'imageUrl': c.thumbnailUrl,
            'description': c.description,
            'totalFavorites': len(c.usuarios_que_les_gusta)
        })

    return jsonify(results), 200


# ----------------------------------------------------
# 4. POST /classes/ (Crear clase en MySQL)
# ----------------------------------------------------
@classes_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
def create_class():
    current_user_id = get_jwt_identity()
    client_data = request.get_json(silent=True)

    if not client_data:
        return jsonify({"error": "JSON inválido"}), 400

    # Disciplina obligatoria (con respaldo a 'style' por compatibilidad)
    discipline = (client_data.get('discipline') or client_data.get('style') or "").strip()
    subdiscipline = (client_data.get('subdiscipline') or "").strip() or None
    effective_style = (client_data.get('style') or subdiscipline or discipline).strip()

    if not client_data.get('title') or not discipline or not client_data.get('difficulty') or not client_data.get('imageUrl'):
        return jsonify({"error": "Faltan campos requeridos: title, discipline, difficulty, imageUrl"}), 400

    start_time = (client_data.get('startTime') or client_data.get('time') or "").strip() or None
    end_time = (client_data.get('endTime') or "").strip() or None

    if start_time and end_time and end_time < start_time:
        return jsonify({"error": "endTime no puede ser anterior a startTime"}), 400

    instructor = Usuario.query.get(current_user_id)
    if not instructor:
        return jsonify({"error": "El usuario autenticado no existe en la base de datos"}), 404

    nueva_clase = Clase(
        id=generar_uuid(),
        publisherId=current_user_id,
        name=client_data['title'],
        description=client_data.get('description', "Aprende los mejores pasos en esta clase..."),
        style=effective_style,
        discipline=discipline,
        subdiscipline=subdiscipline,
        startTime=start_time,
        endTime=end_time,
        duration=client_data.get('duration', 60),
        difficulty=client_data['difficulty'],
        videoUrl=client_data.get('videoUrl', ""),
        thumbnailUrl=client_data['imageUrl'],
        publishDate=datetime.datetime.utcnow()
    )

    db.session.add(nueva_clase)
    db.session.commit()

    response_data = {
        'id': nueva_clase.id,
        'publisherId': nueva_clase.publisherId,
        'publisherUsername': instructor.username or instructor.name,
        'publisherImageUrl': instructor.picture or "",
        'publishDate': nueva_clase.publishDate.strftime('%Y-%m-%d'),
        'title': nueva_clase.name,
        'style': nueva_clase.style,
        'discipline': nueva_clase.discipline,
        'subdiscipline': nueva_clase.subdiscipline,
        'startTime': nueva_clase.startTime,
        'endTime': nueva_clase.endTime,
        'time': nueva_clase.startTime or "",
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

    if clase.publisherId != current_user_id:
        return abort(403, description="No tienes permiso para editar esta clase.")

    if 'title' in payload:
        clase.name = payload['title']
    if 'description' in payload:
        clase.description = payload['description']
    if 'style' in payload:
        clase.style = payload['style']
    if 'discipline' in payload:
        clase.discipline = payload['discipline']
    if 'subdiscipline' in payload:
        clase.subdiscipline = payload['subdiscipline'] or None
    if 'startTime' in payload:
        clase.startTime = payload['startTime'] or None
    if 'endTime' in payload:
        clase.endTime = payload['endTime'] or None
    if 'difficulty' in payload:
        clase.difficulty = payload['difficulty']
    if 'imageUrl' in payload:
        clase.thumbnailUrl = payload['imageUrl']
    if 'videoUrl' in payload:
        clase.videoUrl = payload['videoUrl']
    if 'duration' in payload:
        clase.duration = payload['duration']

    db.session.commit()
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

    if clase.publisherId != current_user_id:
        return abort(403, description="No tienes permiso para eliminar esta clase.")

    db.session.delete(clase)
    db.session.commit()

    return jsonify({"mensaje": f"Clase {class_id} eliminada de forma permanente"}), 200
