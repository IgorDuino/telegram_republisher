from flask import Flask, session, render_template, redirect, request, flash
from web.utils import login_required

import hashlib

from asgiref.wsgi import WsgiToAsgi

from models import RecipientChannel, Filter, FilterScope

import settings

import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)

app = Flask(__name__)
app.secret_key = settings.secret_key
app.template_folder = "templates"
app.debug = settings.debug
asgi_app = WsgiToAsgi(app)


from web.blueprints.donor import bp as donor_bp

app.register_blueprint(donor_bp)

from web.blueprints.recipient import bp as recipient_bp

app.register_blueprint(recipient_bp)

from web.blueprints.filter import bp as filter_bp

app.register_blueprint(filter_bp)


@app.route("/", methods=["GET"])
@login_required
async def index():
    recipients = await RecipientChannel.all().prefetch_related("filters").order_by("-id")
    for recipient in recipients:
        await recipient.fetch_related("donor_channels__filters")
    global_filters = await Filter.filter(scope=FilterScope.GLOBAL).order_by("-id")
    return render_template("index.html", recipients=recipients, global_filters=global_filters)


@app.route("/login", methods=["GET"])
async def login_page():
    if session.get("logged_in"):
        return redirect("/")
    return render_template("login.html")


@app.route("/login", methods=["POST"])
async def login():
    if session.get("logged_in"):
        return redirect("/")
    if not request.form.get("password"):
        flash("Введите пароль", "error")
        return render_template("login.html", error="Password is required")
    if hashlib.sha256(request.form.get("password").encode()).hexdigest() != settings.secret_hash:
        flash("Неверный пароль", "error")
        return render_template("login.html", error="Invalid password")
    session["logged_in"] = True
    return redirect("/")


@app.route("/logout", methods=["GET"])
@login_required
async def logout():
    session.pop("logged_in", None)
    return redirect("/")
