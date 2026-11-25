import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

# 1. IMPORTAR EL MODELO Y LA CONFIGURACIÓN
from database import db
from shared import (
    TABLAS, GOOGLE_CLIENT_ID, JWT_SECRET_KEY, path_for
)
from utils import leer_json, guardar_json

# ---------- Crear app ----------
app = Flask(__name__)
CORS(app)

# 2. CONFIGURACIÓN DE BASE DE DATOS (CONEXIÓN AL MAESTRO)
# Usamos la IP del contenedor maestro que verificamos antes
# app.py
# Cambia '172.18.0.2' por '127.0.0.1' (o la IP de tu servidor si no es local)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:DanceConnect2026!@127.0.0.1:3306/danceconnect_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY

# 3. INICIALIZAR EXTENSIONES
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# 4. IMPORTAR Y REGISTRAR BLUEPRINTS
# Asegúrate de que los archivos estén en la carpeta /routes
from routes.google_auth import google
from routes.classes import classes_bp
from routes.playlists import playlists_bp
from routes.usuarios import usuarios_bp

app.register_blueprint(google, url_prefix="/auth")
app.register_blueprint(classes_bp, url_prefix="/classes")
app.register_blueprint(playlists_bp, url_prefix="/playlists")
app.register_blueprint(usuarios_bp, url_prefix="/usuarios")

# 5. CREACIÓN AUTOMÁTICA DE TABLAS
# Esto crea las tablas en el Maestro (y se replican al Esclavo) al iniciar
with app.app_context():
    db.create_all()

# ---------- Rutas base ----------

@app.get("/")
def index():
    return jsonify({
        "status": "online",
        "database": "connected to master (172.18.0.2)",
        "endpoints": ["/classes", "/usuarios", "/auth", "/playlists"]
    })

# Mantenemos tus rutas dinámicas para compatibilidad con JSON mientras migramos
@app.get("/<tabla>")
def get_tabla(tabla):
    if tabla not in TABLAS:
        return jsonify({"error": "Tabla no existe"}), 404
    path = path_for(tabla)
    data = leer_json(path)
    return jsonify(data)

@app.get("/health")
def health():
    return jsonify({"status": "ok", "database_connected": True}), 200

if __name__ == "__main__":
    # Ejecutamos en 0.0.0.0 para que sea accesible desde tu red local
    app.run(host="0.0.0.0", port=5000, debug=True)
