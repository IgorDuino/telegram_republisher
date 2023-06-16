from flask import Flask, session, render_template, redirect, request, flash, url_for
import hashlib

from asgiref.wsgi import WsgiToAsgi

from models import RecipientChannel, DonorChannel
from tortoise.query_utils import Prefetch

import settings

import pyrogram as tg
from userbot import client, get_admined_and_possible_donor_channels


app = Flask(__name__)
app.secret_key = settings.secret_key
app.template_folder = "templates"
app.debug = settings.debug
asgi_app = WsgiToAsgi(app)


from functools import wraps


def login_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Необходимо авторизоваться", "error")
            return redirect("/login")
        return await f(*args, **kwargs)

    return decorated_function


@app.route("/", methods=["GET"])
@login_required
async def index():
    recipients = await RecipientChannel.all().prefetch_related("donor_channels")
    return render_template("index.html", recipients=recipients)


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


@app.route("/add_recipient", methods=["GET"])
@login_required
async def add_recipient_page():
    admined_channels, possible_donor_channels = await get_admined_and_possible_donor_channels()

    return render_template(
        "add_recipient.html",
        admined_channels=admined_channels,
        possible_donor_channels=possible_donor_channels,
    )


@app.route("/add_recipient", methods=["POST"])
@login_required
async def add_recipient():
    if not (request.form.get("donor") and request.form.get("recipient")):
        flash("Заполните все обязательные поля", "error")
        return redirect(url_for("add_recipient_page"))

    donor_id = request.form.get("donor")
    recipient_id = request.form.get("recipient")
    if request.form.get("name"):
        name = request.form.get("name")
    else:
        name = (await client.get_chat(recipient_id)).title

    if donor_id == recipient_id:
        flash("Канал не может быть донором и получателем одновременно", "error")
        return redirect(url_for("add_recipient_page"))

    if await RecipientChannel.exists(channel_id=recipient_id):
        flash("Канал-получатель уже есть в базе", "error")
        return redirect(url_for("add_recipient_page"))

    donor_name = (await client.get_chat(donor_id)).title

    recipient_channel = await RecipientChannel.create(channel_id=recipient_id, name=name)
    donor_channel = await DonorChannel.create(channel_id=donor_id, name=donor_name, recipient_channel=recipient_channel)

    flash("Канал-получатель успешно добавлен", "success")
    return redirect(url_for("index"))


@app.route("/recipient/<int:id>", methods=["GET"])
@login_required
async def recipient_page(id: int):
    recipient = await RecipientChannel.get_or_none(id=id)
    if not recipient:
        flash("Канал не найден", "error")
        return redirect(url_for("index"))

    await recipient.fetch_related("donor_channels")
    return render_template("recipient.html", recipient=recipient)


@app.route("/recipient/<int:id>", methods=["DELETE"])
@app.route("/recipient/delete/<int:id>", methods=["POST"])
@login_required
async def delete_recipient(id: int):
    recipient = await RecipientChannel.get_or_none(id=id)
    if not recipient:
        flash("Канал не найден", "error")
        return redirect(url_for("index"))

    await recipient.delete()
    flash("Канал-получатель успешно удален", "success")
    return redirect(url_for("index"))


@app.route("/recipient/<int:id>/add_donor", methods=["GET", "POST"])
@login_required
async def recipient_add_donor(id: int):
    recipient = await RecipientChannel.get_or_none(id=id)
    if not recipient:
        flash("Канал не найден", "error")
        return redirect(url_for("index"))

    if request.method == "GET":
        _, possible_donor_channels = await get_admined_and_possible_donor_channels()

        return render_template(
            "add_donor.html",
            recipient=recipient,
            possible_donor_channels=possible_donor_channels,
        )

    if not request.form.get("donor"):
        flash("Заполните все обязательные поля", "error")
        return redirect(url_for("recipient_add_donor", id=id))

    donor_id = request.form.get("donor")

    if donor_id == recipient.channel_id:
        flash("Канал не может быть донором и получателем одновременно", "error")
        return redirect(url_for("recipient_add_donor", id=id))

    if await DonorChannel.exists(channel_id=donor_id, recipient_channel=recipient):
        flash("Канал-донор уже прикреплен к этому каналу-получателю", "error")
        return redirect(url_for("recipient_add_donor", id=id))

    donor_name = (await client.get_chat(donor_id)).title

    donor = await DonorChannel.create(channel_id=donor_id, name=donor_name, recipient_channel=recipient)

    flash("Канал-донор успешно добавлен", "success")
    return redirect(url_for("recipient_page", id=id))


@app.route("/donor/<int:id>", methods=["GET"])
@login_required
async def donor_page(id: int):
    donor = await DonorChannel.get_or_none(id=id)
    if not donor:
        flash("Канал не найден", "error")
        return redirect(url_for("index"))

    await donor.fetch_related("recipient_channel")
    return render_template("donor.html", donor=donor)


@app.route("/donor/<int:id>", methods=["DELETE"])
@app.route("/donor/delete/<int:id>", methods=["POST"])
@login_required
async def delete_donor(id: int):
    donor = await DonorChannel.get_or_none(id=id)
    if not donor:
        flash("Канал-донор не найден", "error")
        return redirect(url_for("index"))

    recipient: RecipientChannel = await donor.recipient_channel
    if len(await recipient.donor_channels) == 1:
        flash(
            "Канал-донор не может быть удален, так как он единственный. Для удаления сначала добавьте другой канал-донор или удалите канал-получатель целиком",
            "error",
        )
        return redirect(url_for("donor_page", id=id))

    await donor.delete()

    flash("Канал-донор успешно удален", "success")
    return redirect(url_for("index"))
