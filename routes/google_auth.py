# routes/google_auth.py

from flask import Blueprint, request, jsonify
import requests
import os
from flask_jwt_extended import create_access_token
from database import db, Usuario  # Importamos SQLAlchemy y el Modelo

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

google = Blueprint("google_auth", __name__, url_prefix="/auth")

@google.route("/google-login", methods=["POST"])
def google_login():
    data = request.json

    if not data or "id_token" not in data:
        return jsonify({"error": "Missing id_token"}), 400

    id_token_str = data["id_token"]

    # 1. Validar token con Google
    try:
        resp = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token_str}",
            timeout=10
        )
        
        if resp.status_code != 200:
            return jsonify({"error": "Invalid token from Google"}), 401
        
        payload = resp.json()
    except Exception as e:
        return jsonify({"error": f"Error verificando token: {str(e)}"}), 500

    # 2. Validar el CLIENT_ID (Seguridad)
    aud = payload.get("aud")
    
    # --- DEPURACIÓN: Asegúrate de que estos prints tengan 4 espacios de sangría ---
    print(f"DEBUG: Token AUD: {aud}")
    print(f"DEBUG: Servidor CLIENT_ID: {GOOGLE_CLIENT_ID}")

    if aud != GOOGLE_CLIENT_ID:
        return jsonify({"error": "Token was not issued for this server"}), 403

    user_id = payload.get("sub")  # ID único de Google
    email = payload.get("email")
    name = payload.get("name")
    picture = payload.get("picture")

    if not user_id or not email:
        return jsonify({"error": "Invalid payload from Google"}), 400

    # -------------------------------------------------------
    # LÓGICA DE BASE DE DATOS (MySQL)
    # -------------------------------------------------------
    
    # Buscamos si el usuario ya existe en MySQL
    usuario_existente = Usuario.query.get(user_id)
    
    is_new_user = False 

    if not usuario_existente:
        # CREAR NUEVO USUARIO EN MYSQL
        is_new_user = True
        
        nuevo_usuario = Usuario(
            id=user_id,
            email=email,
            name=name,
            username=None, # Se definirá en el setup-initial de usuarios.py
            picture=picture,
            role="student",
            bio=None
        )
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit() # Se guarda en Maestro y se replica al Esclavo
            print(f"✅ Usuario nuevo registrado en MySQL: {email}")
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al registrar usuario en la base de datos"}), 500
    else:
        # Usuario ya existe, podríamos actualizar su foto o nombre si cambiaron en Google
        usuario_existente.name = name
        usuario_existente.picture = picture
        db.session.commit()
        print(f"ℹ️ Usuario recurrente: {email}")

    # 3. Crear el JWT para la sesión de la App
    try:
        # Usamos el user_id de Google como identidad del token
        access_token = create_access_token(identity=user_id)
    except Exception as e:
        return jsonify({"error": f"Failed to create access token: {str(e)}"}), 500

    # 4. Devolver la respuesta compatible con tu Frontend en Kotlin
    return jsonify({
        "accessToken": access_token,
        "id": user_id,
        "email": email,
        "name": name,
        "picture": picture,
        "is_new_user": is_new_user
    }), 200
