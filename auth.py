import os
from functools import wraps
from flask import request, abort
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

if not GOOGLE_CLIENT_ID:
    print("⚠️ WARNING: GOOGLE_CLIENT_ID no está configurado en el entorno.")


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header:
            abort(401, description="No se envió encabezado Authorization.")

        if not auth_header.startswith("Bearer "):
            abort(401, description="Formato de Authorization inválido (debe ser Bearer <token>).")

        token = auth_header.split(" ")[1]

        try:
            # Verificar token con Google
            id_info = id_token.verify_oauth2_token(
                token,
                GoogleRequest(),
                GOOGLE_CLIENT_ID
            )
        except Exception as e:
            abort(401, description=f"Token inválido: {str(e)}")

        # Si todo bien → continuar
        return f(*args, **kwargs)

    return decorated

