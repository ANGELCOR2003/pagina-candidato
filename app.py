from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from datetime import datetime, date
from werkzeug.utils import secure_filename
from models import db, News, Signup, Comment
from flask_migrate import Migrate
import os

app = Flask(__name__)

# -------------------------
# RUTAS Y SUBIDAS (UPLOADS)
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "mp4", "webm", "mov"}


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# -------------------------
# BASE DE DATOS
# -------------------------
DB_PATH = os.path.join(BASE_DIR, "app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = os.environ.get("SECRET_KEY", "cambia-esto-por-algo-seguro")

db.init_app(app)
migrate = Migrate(app, db)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# -------------------------
# DATOS FIJOS (LANDING)
# -------------------------
MANDAMIENTOS = [
    "Servir con honestidad y transparencia.",
    "Escuchar al ciudadano antes de decidir.",
    "Defender el orden, la seguridad y la paz.",
    "Promover oportunidades y trabajo digno.",
    "Cuidar los recursos públicos como propios.",
    "Luchar contra la corrupción sin excusas.",
    "Respetar la ley y fortalecer las instituciones.",
    "Impulsar educación, salud y bienestar.",
    "Valorar a la familia y la comunidad.",
    "Trabajar con resultados medibles y rendición de cuentas.",
]

TESTIMONIOS = [
    {
        "nombre": "María Q.",
        "cargo": "Vecina",
        "texto": "Me gustó el enfoque de orden y trabajo. Se siente una propuesta seria.",
    },
]

# -------------------------
# DESACTIVAR CACHE (DEV)
# -------------------------
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# -------------------------
# AUTH ADMIN
# -------------------------
def require_admin():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    return None


# -------------------------
# LANDING
# -------------------------
@app.route("/")
def index():
    # Noticias (últimas primero)
    noticias = News.query.order_by(News.id.desc()).all()

    # Comentarios aprobados (últimos 10 para testimonios)
    comments = (
        Comment.query.filter_by(aprobado=True)
        .order_by(Comment.id.desc())
        .limit(10)
        .all()
    )

    # Si tu template usa dicts, lo convertimos a dicts (más seguro)
    noticias_payload = [
    {
        "id": n.id,
        "titulo": n.titulo,
        "fecha": n.fecha,
        "resumen": n.resumen,
        "imagen": n.imagen,
        "tag": n.tag,
        "media_type": getattr(n, "media_type", None),
        "media_path": getattr(n, "media_path", None),
        "media_url": getattr(n, "media_url", None),
    }
    for n in noticias
]

    comentarios_payload = [
        {
            "nombre": c.nombre,
            "comentario": c.comentario,
        }
        for c in comments
    ]

    return render_template(
        "index.html",
        testimonios=TESTIMONIOS,
        comentarios=comentarios_payload,
        noticias=noticias_payload,
        mandamientos=MANDAMIENTOS,
    )


# -------------------------
# QUIÉN SOY
# -------------------------
@app.route("/quien-soy")
def quien_soy():
    return render_template("quien_soy.html")

# -------------------------
# NOTICIA (DETALLE)
# -------------------------
@app.route("/noticia/<int:noticia_id>")
def noticia_detalle(noticia_id):
    noticia = News.query.get_or_404(noticia_id)

    # Más noticias (excluye la actual)
    otras = (
        News.query
        .filter(News.id != noticia_id)
        .order_by(News.id.desc())
        .all()
    )

    noticia_payload = {
        "id": noticia.id,
        "titulo": noticia.titulo,
        "fecha": noticia.fecha,
        "resumen": noticia.resumen,
        "imagen": noticia.imagen,
        "tag": noticia.tag,
        "media_type": getattr(noticia, "media_type", None),
        "media_path": getattr(noticia, "media_path", None),
        "media_url": getattr(noticia, "media_url", None),
    }

    otras_payload = [
        {
            "id": n.id,
            "titulo": n.titulo,
            "fecha": n.fecha,
            "resumen": n.resumen,
            "imagen": n.imagen,
            "tag": n.tag,
            "media_type": getattr(n, "media_type", None),
            "media_path": getattr(n, "media_path", None),
            "media_url": getattr(n, "media_url", None),
        }
        for n in otras
    ]

    return render_template(
        "noticia_detalle.html",
        noticia=noticia_payload,
        otras=otras_payload,
    )


# -------------------------
# CONTACTO / INSCRIPCIONES
# -------------------------
@app.route("/contact", methods=["POST"])
def contact():
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()
    celular = request.form.get("celular", "").strip()
    mensaje = request.form.get("mensaje", "").strip()
    es_voluntario = request.form.get("es_voluntario") == "on"

    if not nombre or not email or not mensaje:
        flash("Por favor completa nombre, correo y mensaje.", "error")
        return redirect(url_for("index") + "#contacto")

    s = Signup(
        nombre=nombre,
        email=email,
        celular=celular,
        mensaje=mensaje,
        es_voluntario=es_voluntario,
    )
    db.session.add(s)
    db.session.commit()

    flash("¡Mensaje enviado! Registrado correctamente.", "success")
    return redirect(url_for("index") + "#contacto")


# -------------------------
# COMENTARIOS (VER + DEJAR)
# -------------------------
@app.route("/comentarios", methods=["GET", "POST"])
def comentarios():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        comentario = request.form.get("comentario", "").strip()

        if not nombre or not comentario:
            flash("Completa tu nombre y el comentario.", "error")
            return redirect(url_for("comentarios"))

        # en producción: aprobado=False y que admin lo apruebe
        c = Comment(nombre=nombre, comentario=comentario, aprobado=True)
        db.session.add(c)
        db.session.commit()

        flash("¡Comentario enviado!", "success")
        return redirect(url_for("comentarios"))

    comments = Comment.query.order_by(Comment.id.desc()).all()

    # Para no romper tu template actual:
    payload = []
    for c in comments:
        created = getattr(c, "created_at", None)
        fecha_str = created.strftime("%Y-%m-%d %H:%M:%S") if created else ""
        payload.append(
            {
                "id": c.id,
                "nombre": c.nombre,
                "comentario": c.comentario,
                "fecha": fecha_str,
                "aprobado": getattr(c, "aprobado", True),
            }
        )

    return render_template("comments.html", comments=payload)


# -------------------------
# ADMIN LOGIN / LOGOUT
# -------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Clave incorrecta.", "error")
        return redirect(url_for("admin_login"))

    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))


# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route("/admin")
def admin_dashboard():
    r = require_admin()
    if r:
        return r

    stats = {
        "news": News.query.count(),
        "signups": Signup.query.count(),
        "comments": Comment.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


# -------------------------
# ADMIN: NOTICIAS
# -------------------------
@app.route("/admin/noticias")
def admin_news_list():
    r = require_admin()
    if r:
        return r

    news_sorted = News.query.order_by(News.id.desc()).all()
    return render_template("admin/news_list.html", news=news_sorted)


@app.route("/admin/noticias/nueva", methods=["GET", "POST"])
def admin_news_new():
    r = require_admin()
    if r:
        return r

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        fecha = request.form.get("fecha", "").strip()
        resumen = request.form.get("resumen", "").strip()
        tag = request.form.get("tag", "").strip() or "Actualidad"

        # Fecha automática si no mandan
        if not fecha:
            fecha = datetime.now().strftime("%Y-%m-%d")

        media_url = (request.form.get("media_url", "") or "").strip() or None
        media_file = request.files.get("media_file")

        if not titulo or not resumen:
            flash("Completa título y resumen.", "error")
            return redirect(url_for("admin_news_new"))

        media_type = None
        media_path = None

        # 1) Si sube archivo, gana el archivo
        if media_file and media_file.filename:
            if not allowed_file(media_file.filename):
                flash(
                    "Archivo no permitido. Usa png/jpg/jpeg/webp/gif o mp4/webm/mov.",
                    "error",
                )
                return redirect(url_for("admin_news_new"))

            filename = secure_filename(media_file.filename)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stamp}_{filename}"

            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            media_file.save(save_path)

            ext = filename.rsplit(".", 1)[1].lower()
            media_type = "video" if ext in {"mp4", "webm", "mov"} else "image"
            media_path = f"uploads/{filename}"
            media_url = None  # si hay archivo, ignora link

        # 2) Si no hay archivo, usa link
        elif media_url:
            media_type = "link"

        n = News(
            titulo=titulo,
            fecha=fecha,
            resumen=resumen,
            tag=tag,
            imagen="placeholder-news.jpg",
            media_type=media_type,
            media_path=media_path,
            media_url=media_url,
        )
        db.session.add(n)
        db.session.commit()

        flash("Noticia creada.", "success")
        return redirect(url_for("admin_news_list"))

    return render_template("admin/news_form.html", mode="new", item=None)


@app.route("/admin/noticias/<int:item_id>/editar", methods=["GET", "POST"])
def admin_news_edit(item_id):
    r = require_admin()
    if r:
        return r

    item = News.query.get_or_404(item_id)

    if request.method == "POST":
        # -------- campos normales --------
        item.titulo = request.form.get("titulo", "").strip()
        item.fecha = request.form.get("fecha", "").strip()
        item.resumen = request.form.get("resumen", "").strip()
        item.tag = request.form.get("tag", "").strip() or "Actualidad"

        # (opcional) si todavía usas el campo imagen viejo en tu template
        item.imagen = request.form.get("imagen", "").strip() or "placeholder-news.jpg"

        if not item.titulo or not item.fecha or not item.resumen:
            flash("Completa título, fecha y resumen.", "error")
            return redirect(url_for("admin_news_edit", item_id=item_id))

        # -------- media (archivo o link) --------
        # input type="file" name="media_file"
        media_file = request.files.get("media_file")

        # input type="url" name="media_url"
        media_url = (request.form.get("media_url", "") or "").strip() or None

        # 1) Si subió archivo, gana el archivo (ignora link)
        if media_file and media_file.filename:
            if not allowed_file(media_file.filename):
                flash(
                    "Archivo no permitido. Usa png/jpg/webp/gif o mp4/webm/mov.",
                    "error",
                )
                return redirect(url_for("admin_news_edit", item_id=item_id))

            filename = secure_filename(media_file.filename)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stamp}_{filename}"

            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            media_file.save(save_path)

            ext = filename.rsplit(".", 1)[1].lower()
            item.media_type = "video" if ext in {"mp4", "webm", "mov"} else "image"
            item.media_path = f"uploads/{filename}"
            item.media_url = None

        # 2) Si no subió archivo pero puso link, guardamos link
        elif media_url:
            item.media_type = "link"
            item.media_url = media_url
            item.media_path = None

        # 3) Si no subió nada ni link: no tocamos media (se queda como está)

        db.session.commit()
        flash("Noticia actualizada.", "success")
        return redirect(url_for("admin_news_list"))

    # GET
    return render_template("admin/news_form.html", mode="edit", item=item)
    return render_template("admin/news_form.html", mode="edit", item=item)


@app.route("/admin/noticias/<int:item_id>/eliminar", methods=["POST"])
def admin_news_delete(item_id):
    r = require_admin()
    if r:
        return r

    item = News.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()

    flash("Noticia eliminada.", "success")
    return redirect(url_for("admin_news_list"))


# -------------------------
# ADMIN: INSCRITOS
# -------------------------
@app.route("/admin/inscritos")
def admin_signups():
    r = require_admin()
    if r:
        return r

    signups_sorted = Signup.query.order_by(Signup.id.desc()).all()
    return render_template("admin/signups.html", signups=signups_sorted)


# -------------------------
# ADMIN: COMENTARIOS
# -------------------------
@app.route("/admin/comentarios")
def admin_comments():
    r = require_admin()
    if r:
        return r

    comments_sorted = Comment.query.order_by(Comment.id.desc()).all()
    return render_template("admin/comments_list.html", comments=comments_sorted)


@app.route("/admin/comentarios/<int:cid>/toggle", methods=["POST"])
def admin_comment_toggle(cid):
    r = require_admin()
    if r:
        return r

    c = Comment.query.get_or_404(cid)
    c.aprobado = not c.aprobado
    db.session.commit()

    flash("Estado actualizado.", "success")
    return redirect(url_for("admin_comments"))


@app.route("/admin/comentarios/<int:cid>/eliminar", methods=["POST"])
def admin_comment_delete(cid):
    r = require_admin()
    if r:
        return r

    c = Comment.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()

    flash("Comentario eliminado.", "success")
    return redirect(url_for("admin_comments"))


if __name__ == "__main__":
    app.run(debug=True)


    