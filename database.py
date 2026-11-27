from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

# 1. Tabla intermedia para Seguidores (Muchos a Muchos)
seguidores = db.Table('seguidores',
    db.Column('follower_id', db.String(100), db.ForeignKey('usuarios.id')),
    db.Column('followed_id', db.String(100), db.ForeignKey('usuarios.id'))
)

# 2. Tabla intermedia para Clases Favoritas (Muchos a Muchos)
favoritos = db.Table('favoritos',
    db.Column('usuario_id', db.String(100), db.ForeignKey('usuarios.id')),
    db.Column('clase_id', db.String(100), db.ForeignKey('clases.id'))
)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.String(100), primary_key=True) # ID de Google
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    picture = db.Column(db.String(255))
    role = db.Column(db.String(20), default='student')
    bio = db.Column(db.Text)
    
    # Relaciones
    clases_creadas = db.relationship('Clase', backref='instructor', lazy=True)
    
    # Relación de seguidores (Self-referential)
    # El backref='followers' permite llamar a user.followers
    following = db.relationship(
        'Usuario', secondary=seguidores,
        primaryjoin=(seguidores.c.follower_id == id),
        secondaryjoin=(seguidores.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'
    )

    # Relación para clases favoritas
    clases_favoritas = db.relationship(
        'Clase', 
        secondary=favoritos, 
        backref='usuarios_que_les_gusta' # Esto soluciona el AttributeError en clases.py
    )

class Clase(db.Model):
    __tablename__ = 'clases'
    id = db.Column(db.String(100), primary_key=True)
    publisherId = db.Column(db.String(100), db.ForeignKey('usuarios.id'), nullable=False)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    style = db.Column(db.String(50))
    discipline = db.Column(db.String(50))
    subdiscipline = db.Column(db.String(80))
    startTime = db.Column(db.String(10))
    endTime = db.Column(db.String(10))
    difficulty = db.Column(db.String(50))
    thumbnailUrl = db.Column(db.String(255))
    videoUrl = db.Column(db.String(255))
    duration = db.Column(db.Integer)
    publishDate = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    
    # --- MODELOS PARA FRAGMENTACIÓN VERTICAL (VISTAS) ---

class ClaseFeed(db.Model):
    __tablename__ = 'vista_clase_feed'
    
    id = db.Column(db.String(36), primary_key=True)
    # 1. Asegúrate de que el ForeignKey apunte a 'usuarios' (plural)
    publisherId = db.Column(db.String(36), db.ForeignKey('usuarios.id'))
    name = db.Column(db.String(255))
    style = db.Column(db.String(50))
    difficulty = db.Column(db.String(50))
    thumbnailUrl = db.Column(db.String(255))
    publishDate = db.Column(db.DateTime)

    # 2. Obligamos a SQLAlchemy a entender la relación con 'primaryjoin'
    instructor = db.relationship(
        'Usuario', 
        primaryjoin="ClaseFeed.publisherId == Usuario.id",
        foreign_keys=[publisherId],
        lazy='joined'
    )

class ClaseDetalle(db.Model):
    __tablename__ = 'vista_clase_detalle'
    id = db.Column(db.String(36), primary_key=True)
    description = db.Column(db.Text)
    videoUrl = db.Column(db.String(255))
    duration = db.Column(db.Integer)
