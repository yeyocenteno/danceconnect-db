# routes/events.py

from flask import Blueprint, request, jsonify, abort
from database import db, Evento
from utils import generar_uuid
from auth_helpers import requires_auth

events_bp = Blueprint('events', __name__, url_prefix='/eventos')

# 1. GET /eventos (Listar todos)
@events_bp.route('/', methods=['GET'])
def get_all_events():
    eventos = Evento.query.all()
    return jsonify([e.as_dict() for e in eventos])

# 2. GET /eventos/<id> (Detalle)
@events_bp.route('/<string:event_id>', methods=['GET'])
def get_event_by_id(event_id):
    evento = Evento.query.get(event_id)
    if not evento:
        return abort(404, description="Evento no encontrado")
    return jsonify(evento.as_dict())

# 3. POST /eventos (Crear)
@events_bp.route('/', methods=['POST'])
@requires_auth
def create_event():
    data = request.json
    nuevo_evento = Evento(
        id=generar_uuid(),
        title=data.get('title'),
        description=data.get('description'),
        date=data.get('date'),
        price=data.get('price'),
        imageUrl=data.get('imageUrl')
    )
    db.session.add(nuevo_evento)
    db.session.commit()
    return jsonify({"mensaje": "Evento creado", "id": nuevo_evento.id}), 201

# 4. PUT /eventos/<id> (Actualizar)
@events_bp.route('/<string:event_id>', methods=['PUT'])
@requires_auth
def update_event(event_id):
    data = request.json
    evento = Evento.query.get(event_id)
    if not evento:
        return abort(404, description="Evento no encontrado")
    
    # Actualizar campos
    for key, value in data.items():
        if hasattr(evento, key):
            setattr(evento, key, value)
            
    db.session.commit()
    return jsonify({"mensaje": "Evento actualizado"})

# 5. DELETE /eventos/<id> (Eliminar)
@events_bp.route('/<string:event_id>', methods=['DELETE'])
@requires_auth
def delete_event(event_id):
    evento = Evento.query.get(event_id)
    if not evento:
        return abort(404, description="Evento no encontrado")
    
    db.session.delete(evento)
    db.session.commit()
    return jsonify({"mensaje": "Evento eliminado"})
