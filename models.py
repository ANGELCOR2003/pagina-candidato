from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.String(20), nullable=False)
    resumen = db.Column(db.Text, nullable=False)
    tag = db.Column(db.String(50), default="Actualidad")
    imagen = db.Column(db.String(200), default="placeholder-news.jpg")

    media_type = db.Column(db.String(20), nullable=True)
    media_path = db.Column(db.String(255), nullable=True)
    media_url  = db.Column(db.String(500), nullable=True)



class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    celular = db.Column(db.String(40), nullable=True)
    mensaje = db.Column(db.Text, nullable=False)
    es_voluntario = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    comentario = db.Column(db.Text, nullable=False)
    aprobado = db.Column(db.Boolean, default=True)  # por ahora true para que aparezcan
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
