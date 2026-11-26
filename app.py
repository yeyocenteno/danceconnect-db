import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from sqlalchemy import text

# 1. IMPORTAR EL MODELO Y LA CONFIGURACIÓN
from database import db
from shared import TABLAS, path_for
from utils import leer_json

# ---------- Crear app ----------
app = Flask(__name__)
CORS(app)

# 2. Configuración de base de datos
database_uri = os.getenv("DATABASE_URL")

if not database_uri:
    raise RuntimeError(
        "No se encontró la variable DATABASE_URL"
    )

# Railway puede proporcionar mysql://.
# SQLAlchemy utilizará PyMySQL.
if database_uri.startswith("mysql://"):
    database_uri = database_uri.replace(
        "mysql://",
        "mysql+pymysql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]

# 3. INICIALIZAR EXTENSIONES
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# 4. IMPORTAR Y REGISTRAR BLUEPRINTS
from routes.google_auth import google
from routes.classes import classes_bp
from routes.playlists import playlists_bp
from routes.usuarios import usuarios_bp

app.register_blueprint(google, url_prefix="/auth")
app.register_blueprint(classes_bp, url_prefix="/classes")
app.register_blueprint(playlists_bp, url_prefix="/playlists")
app.register_blueprint(usuarios_bp, url_prefix="/usuarios")

# 5. CREACIÓN AUTOMÁTICA DE TABLAS
with app.app_context():
    db.create_all()

# ---------- Rutas base ----------

@app.get("/")
def index():
    return jsonify({
        "status": "online",
        "database": "configured",
        "endpoints": ["/classes", "/usuarios", "/auth", "/playlists"]
    })

@app.get("/<tabla>")
def get_tabla(tabla):
    if tabla not in TABLAS:
        return jsonify({"error": "Tabla no existe"}), 404
    path = path_for(tabla)
    data = leer_json(path)
    return jsonify(data)


@app.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))

        return jsonify({
            "status": "ok",
            "database_connected": True
        }), 200

    except Exception:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "database_connected": False
        }), 503
        
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode
    )
        
