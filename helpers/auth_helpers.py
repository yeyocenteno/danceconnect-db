import os
from functools import wraps
from flask import request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from models import Usuario  # Importamos el modelo Usuario para buscar en MySQL

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

def verify_google_token(token: str):
    """Verifica la firma del token con Google."""
    try:
        id_info = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        return id_info
    except Exception as e:
        print(f"Error validando token: {e}")
        return None

def requires_auth(func):
    """
    Decorator para proteger rutas y verificar que el usuario
    existe en nuestra base de datos MySQL.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization")

        if not auth or not auth.startswith("Bearer "):
            return jsonify({"error": "Missing Authorization header"}), 401

        token = auth.split(" ")[1]
        payload = verify_google_token(token)

        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        # 🚀 INTEGRACIÓN CON MYSQL:
        # Buscamos al usuario en MySQL usando el ID único de Google (sub)
        user_id = payload.get("sub")
        usuario = Usuario.query.get(user_id)

        if not usuario:
            return jsonify({"error": "Usuario no registrado en la base de datos"}), 403

        # Adjuntamos el objeto del usuario a la petición para usarlo en el código
        request.user = usuario

        return func(*args, **kwargs)
    return wrapper
