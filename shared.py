import os
import json
import time
import requests
import base64
import config

# Directorio base
DATA_DIR = config.Config.NFS_PATH

# Crear carpeta data si no existe
os.makedirs(DATA_DIR, exist_ok=True)

# Tablas disponibles
TABLAS = {
    "usuarios": "usuarios",
    "clases": "clases",
    "eventos": "eventos",
    "playlists": "playlists",
    "videos": "videos",
    "seguidores": "seguidores"
}


# Credenciales cargadas por systemd a través de EnvironmentFile
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Asegúrate de cambiar "TU_CLAVE_JWT_SECRETA_Y_LARGA_AQUI_2025" por una cadena aleatoria
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "0397c3e367d0d37f0eba7babcf146053271668f4e0ea009763ad04ac6038b3d3")


def path_for(tabla: str):
    """Devuelve la ruta completa del archivo JSON para una tabla."""
    return os.path.join(DATA_DIR, f"{tabla}.json")


def load_json(tabla: str):
    """Lee un archivo JSON. Si no existe, devuelve lista vacía."""
    ruta = path_for(tabla)
    if not os.path.exists(ruta):
        return []

    with open(ruta, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_json(tabla: str, data):
    """Guarda datos en un archivo JSON."""
    ruta = path_for(tabla)
    with open(ruta, "w") as f:
        json.dump(data, f, indent=4)


# ---------- SPOTIFY TOKEN ----------
_spotify_token_cache = {
    "access_token": None,
    "expires_at": 0
}

def _spotify_get_token():
    """Obtiene y almacena en caché el token de Spotify."""
    global _spotify_token_cache

    if (_spotify_token_cache["access_token"] and time.time() < _spotify_token_cache["expires_at"]):
        return _spotify_token_cache["access_token"]

    # 1. URL OFICIAL
    url = "https://accounts.spotify.com/api/token"
    
    # DEBUG: Verifica si tienes las credenciales cargadas
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print(f"ERROR CRÍTICO: SPOTIFY_CLIENT_ID o SECRET están vacíos. Revisa tu .env")
        return None

    # 2. Autenticación
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    payload = {"grant_type": "client_credentials"}

    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            print(f"DEBUG: Respuesta error Spotify: {resp.text}")
            return None
            
        data = resp.json()
        _spotify_token_cache["access_token"] = data["access_token"]
        _spotify_token_cache["expires_at"] = time.time() + data["expires_in"]
        
        return _spotify_token_cache["access_token"]
        
    except Exception as e:
        print(f"Error crítico en _spotify_get_token: {e}")
        return None
