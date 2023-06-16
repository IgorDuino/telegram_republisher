from flask import Flask, session, render_template, redirect, request, flash
from asgiref.wsgi import WsgiToAsgi
import settings
from userbot import client
import hashlib


app = Flask(__name__)
app.secret_key = settings.secret_key
asgi_app = WsgiToAsgi(app)


@app.route("/", methods=["GET"])
async def index():
    if not session.get("logged_in"):
        return render_template("login.html")
    return render_template("index.html")


@app.route("/", methods=["POST"])
async def login():
    if session.get("logged_in"):
        return redirect("/")
    if not request.form.get("password"):
        flash("Password is required", "error")
        return render_template("login.html", error="Password is required")
    if hashlib.sha256(request.form.get("password").encode()).hexdigest() != settings.secret_hash:
        flash("Invalid password", "error")
        return render_template("login.html", error="Invalid password")
    session["logged_in"] = True
    return redirect("/")


@app.route("/logout", methods=["GET"])
async def logout():
    session.pop("logged_in", None)
    return redirect("/")
