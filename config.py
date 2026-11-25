# config.py

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env (si existe)
# Esto es esencial para el desarrollo local.
load_dotenv() 

class Config:
    """Clase base de configuración"""
    
    # 1. Configuración de la Aplicación Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-M0Ca')
    """Clave secreta utilizada para firmar sesiones y cookies. ¡Cámbiala en producción!"""
    
    # 2. Rutas y Almacenamiento
    # Ruta donde se almacenan los archivos JSON (simulando un sistema de archivos persistente)
    NFS_PATH = os.environ.get("NFS_PATH", "nfs_data")
    
    # 3. Autenticación de Google OAuth
    # ID del cliente de Google para la verificación de tokens
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    
    # 4. Integración con Spotify
    SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
    
    # 5. Configuración de Servidor
    # Host y Puerto para la ejecución local (accesible desde la red local)
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('PORT', 5000))

class DevelopmentConfig(Config):
    """Configuración para desarrollo."""
    DEBUG = True
    # Si la ruta NFS_PATH no existe, la crea
    if not os.path.exists(Config.NFS_PATH):
        os.makedirs(Config.NFS_PATH)

class ProductionConfig(Config):
    """Configuración para producción."""
    DEBUG = False
    TESTING = False
    # Aquí puedes añadir logging o configuraciones de seguridad específicas
    # Asegúrate de que SECRET_KEY esté definida en el entorno de producción.
    

# Diccionario para seleccionar la configuración
config_by_name = dict(
    dev=DevelopmentConfig,
    prod=ProductionConfig
)

# ----------------------------------------------------------------------
# SUGERENCIA: Puedes cargar la configuración en app.py así:
# ----------------------------------------------------------------------
# from config import config_by_name
# app.config.from_object(config_by_name['dev']) # Usa 'prod' en producción
