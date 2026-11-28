from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db, Usuario, Clase

# Definición del Blueprint para Usuarios
usuarios_bp = Blueprint('usuarios', __name__)

MAX_FAVORITE_DISCIPLINES = 2


def _parse_favorite_disciplines(raw_value):
    if not raw_value:
        return []
    return [
        item.strip()
        for item in str(raw_value).split("|")
        if item.strip()
    ][:MAX_FAVORITE_DISCIPLINES]


def _serialize_favorite_disciplines(styles):
    if not isinstance(styles, list):
        return None
    cleaned = [
        str(s).strip()
        for s in styles
        if str(s).strip()
    ][:MAX_FAVORITE_DISCIPLINES]
    return "|".join(cleaned) if cleaned else None


# ----------------------------------------------------
# 1. GET /usuarios/me (Obtener perfil del usuario logueado)
# ----------------------------------------------------
@usuarios_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_profile():
    user_id = get_jwt_identity()

    # Buscamos directamente en la base de datos por ID
    user_profile = Usuario.query.get(user_id)

    if user_profile:
        # Extraemos las listas de IDs usando las relaciones del ORM
        follower_ids = [follower.id for follower in user_profile.followers]
        following_ids = [followed.id for followed in user_profile.following]
        favorite_class_ids = [clase.id for clase in user_profile.clases_favoritas]

        # Obtenemos las clases reales publicadas por este usuario
        clases_publicadas = Clase.query.filter_by(publisherId=user_id).all()
        posts_data = [
            {
                "id": clase.id,
                "imageUrl": clase.thumbnailUrl or "https://via.placeholder.com/300"
            } for clase in clases_publicadas
        ]

        response_data = {
            "id": user_profile.id,
            "name": user_profile.name,
            "username": user_profile.username or user_profile.name or "Usuario",
            "email": user_profile.email,
            "profileImageUrl": user_profile.picture or "https://via.placeholder.com/150",
            "bio": user_profile.bio or "",
            "followerCount": len(follower_ids),
            "followingCount": len(following_ids),
            "postCount": len(clases_publicadas),
            "favoriteStyles": _parse_favorite_disciplines(user_profile.favorite_styles),
            "favorite_class_ids": favorite_class_ids,
            "posts": posts_data
        }

        return jsonify(response_data), 200

    return jsonify({"error": "Perfil no encontrado"}), 404


# ----------------------------------------------------
# 2. PUT /usuarios/me (Actualizar perfil del usuario logueado)
# ----------------------------------------------------
@usuarios_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user_profile():
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True)

    if not payload:
        return jsonify({"error": "JSON inválido"}), 400

    usuario = Usuario.query.get(user_id)
    if not usuario:
        return abort(404, description="Usuario no encontrado para actualizar")

    if 'name' in payload:
        usuario.name = payload['name']
    if 'username' in payload:
        existente = Usuario.query.filter(
            Usuario.username == payload['username'],
            Usuario.id != user_id
        ).first()
        if existente:
            return jsonify({"error": "El nombre de usuario ya existe"}), 409
        usuario.username = payload['username']
    if 'bio' in payload:
        usuario.bio = payload['bio']
    if 'picture' in payload:
        usuario.picture = payload['picture']
    if 'favoriteStyles' in payload:
        usuario.favorite_styles = _serialize_favorite_disciplines(payload['favoriteStyles'])

    db.session.commit()

    return jsonify({
        "mensaje": "Perfil actualizado",
        "user": {
            "id": usuario.id,
            "name": usuario.name,
            "username": usuario.username,
            "bio": usuario.bio,
            "favoriteStyles": _parse_favorite_disciplines(usuario.favorite_styles)
        }
    }), 200


# ----------------------------------------------------
# 3. DELETE /usuarios/me (Eliminar perfil del usuario logueado)
# ----------------------------------------------------
@usuarios_bp.route('/me', methods=['DELETE'])
@jwt_required()
def delete_current_user():
    user_id = get_jwt_identity()
    usuario = Usuario.query.get(user_id)

    if usuario:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"mensaje": f"Usuario {user_id} eliminado exitosamente de MySQL"}), 200

    return abort(404, description="Usuario no encontrado para eliminar")


# ----------------------------------------------------
# 4. POST /usuarios/me/favorites (Añadir un favorito)
# ----------------------------------------------------
@usuarios_bp.route('/me/favorites', methods=['POST'])
@jwt_required()
def add_favorite_class():
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}

    class_id = payload.get("class_id")
    if not class_id:
        return jsonify({"error": "Falta el ID de la clase (class_id)"}), 400

    usuario = Usuario.query.get(user_id)
    clase = Clase.query.get(class_id)

    if not usuario:
        return abort(404, description="Usuario no encontrado")
    if not clase:
        return abort(404, description="Clase no encontrada")

    if clase not in usuario.clases_favoritas:
        usuario.clases_favoritas.append(clase)
        db.session.commit()
        return jsonify({"mensaje": "Clase añadida a favoritos", "class_id": class_id}), 200
    else:
        return jsonify({"mensaje": "Clase ya es favorita"}), 200


# ----------------------------------------------------
# 5. DELETE /usuarios/me/favorites (Eliminar un favorito)
# ----------------------------------------------------
@usuarios_bp.route('/me/favorites', methods=['DELETE'])
@jwt_required()
def remove_favorite_class():
    user_id = get_jwt_identity()
    class_id = request.args.get("class_id")

    if not class_id:
        return jsonify({"error": "Falta el ID de la clase (class_id)"}), 400

    usuario = Usuario.query.get(user_id)
    clase = Clase.query.get(class_id)

    if not usuario or not clase:
        return abort(404, description="Usuario o clase no encontrados")

    if clase in usuario.clases_favoritas:
        usuario.clases_favoritas.remove(clase)
        db.session.commit()
        return jsonify({"mensaje": "Clase eliminada de favoritos", "class_id": class_id}), 200

    return jsonify({"mensaje": "Clase no estaba en favoritos"}), 200


# ----------------------------------------------------
# 6. GET /usuarios/<user_id> (Ver perfil público de otro usuario)
# ----------------------------------------------------
@usuarios_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
def get_public_profile(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id == user_id:
        return jsonify({
            "isOwnProfile": True,
            "redirect": "/usuarios/me"
        }), 200

    target_user = Usuario.query.get(user_id)
    if not target_user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    current_user = Usuario.query.get(current_user_id)
    is_following = target_user in current_user.following if current_user else False

    clases_publicadas = Clase.query.filter_by(publisherId=user_id).all()
    user_posts = [
        {
            "id": c.id,
            "name": c.name,
            "style": c.style,
            "thumbnailUrl": c.thumbnailUrl
        } for c in clases_publicadas
    ]

    response_data = {
        "id": target_user.id,
        "name": target_user.name,
        "username": target_user.username or target_user.name or "Usuario",
        "profileImageUrl": target_user.picture or "https://via.placeholder.com/150",
        "bio": target_user.bio or "",
        "followerCount": target_user.followers.count(),
        "followingCount": target_user.following.count(),
        "postCount": len(clases_publicadas),
        "favoriteStyles": _parse_favorite_disciplines(target_user.favorite_styles),
        "isFollowing": is_following,
        "isOwnProfile": False,
        "posts": user_posts
    }

    return jsonify(response_data), 200


# ----------------------------------------------------
# 7. POST /usuarios/<target_id>/follow (Seguir usuario)
# ----------------------------------------------------
@usuarios_bp.route('/<target_id>/follow', methods=['POST'])
@jwt_required()
def follow_user(target_id):
    current_user_id = get_jwt_identity()

    if current_user_id == target_id:
        return jsonify({"error": "No puedes seguirte a ti mismo"}), 400

    me = Usuario.query.get(current_user_id)
    target = Usuario.query.get(target_id)

    if not me or not target:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if target not in me.following:
        me.following.append(target)
        db.session.commit()
        return jsonify({"mensaje": "Ahora sigues a este usuario"}), 200
    else:
        return jsonify({"mensaje": "Ya sigues a este usuario"}), 200


# ----------------------------------------------------
# 8. DELETE /usuarios/<target_id>/follow (Dejar de seguir)
# ----------------------------------------------------
@usuarios_bp.route('/<target_id>/follow', methods=['DELETE'])
@jwt_required()
def unfollow_user(target_id):
    current_user_id = get_jwt_identity()

    me = Usuario.query.get(current_user_id)
    target = Usuario.query.get(target_id)

    if not me or not target:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if target in me.following:
        me.following.remove(target)
        db.session.commit()
        return jsonify({"mensaje": "Has dejado de seguir al usuario"}), 200

    return jsonify({"mensaje": "No hubo cambios"}), 200


# ----------------------------------------------------
# 9. PUT /usuarios/setup-initial (Guardar Username y Disciplinas)
# ----------------------------------------------------
@usuarios_bp.route("/setup-initial", methods=["PUT"])
@jwt_required()
def setup_initial():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    new_username = (data.get("username") or "").strip()
    new_styles = data.get("favoriteStyles")

    if (
        not new_username
        or not isinstance(new_styles, list)
        or len(new_styles) < 1
        or len(new_styles) > MAX_FAVORITE_DISCIPLINES
    ):
        return jsonify({"error": "Faltan username o disciplinas (entre 1 y 2)"}), 400

    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    username_existente = Usuario.query.filter(
        Usuario.username == new_username,
        Usuario.id != user_id
    ).first()
    if username_existente:
        return jsonify({"error": "El nombre de usuario ya existe. Por favor, elige otro."}), 409

    usuario.username = new_username
    usuario.favorite_styles = _serialize_favorite_disciplines(new_styles)
    db.session.commit()

    return jsonify({
        "message": "Configuración inicial guardada con éxito",
        "username": new_username,
        "favoriteStyles": _parse_favorite_disciplines(usuario.favorite_styles)
    }), 200


# ----------------------------------------------------
# 10. GET /usuarios/search (Buscar usuarios por username)
# ----------------------------------------------------
@usuarios_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    query = request.args.get('query', '').strip()

    if not query:
        return jsonify([]), 200

    usuarios_filtrados = Usuario.query.filter(Usuario.username.ilike(f"%{query}%")).all()

    results = [
        {
            "id": u.id,
            "username": u.username,
            "profile_image_url": u.picture or "https://via.placeholder.com/150"
        } for u in usuarios_filtrados
    ]

    return jsonify(results), 200
