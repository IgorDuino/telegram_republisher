from flask import Blueprint, render_template, redirect, request, flash, url_for

from models import RecipientChannel, DonorChannel

from web.utils import login_required
from userbot import client, get_admined_and_possible_donor_channels


bp = Blueprint("recipient", __name__)


@bp.route("/add_recipient", methods=["GET"])
@login_required
async def add_recipient_page():
    admined_channels, possible_donor_channels = await get_admined_and_possible_donor_channels()

    return render_template(
        "add_recipient.html",
        admined_channels=admined_channels,
        possible_donor_channels=possible_donor_channels,
    )


@bp.route("/add_recipient", methods=["POST"])
@login_required
async def add_recipient():
    if not (request.form.get("donor") and request.form.get("recipient")):
        flash("Заполните все обязательные поля", "error")
        return redirect(url_for("recipient.add_recipient_page"))

    donor_id = request.form.get("donor")
    recipient_id = request.form.get("recipient")
    if request.form.get("name"):
        name = request.form.get("name")
    else:
        name = (await client.get_chat(recipient_id)).title

    if donor_id == recipient_id:
        flash("Канал не может быть донором и получателем одновременно", "error")
        return redirect(url_for("recipient.add_recipient_page"))

    if await RecipientChannel.exists(channel_id=recipient_id):
        flash("Канал-получатель уже есть в базе", "error")
        return redirect(url_for("recipient.add_recipient_page"))

    donor_name = (await client.get_chat(donor_id)).title

    recipient_channel = await RecipientChannel.create(channel_id=recipient_id, name=name)
    donor_channel = await DonorChannel.create(channel_id=donor_id, name=donor_name, recipient_channel=recipient_channel)

    flash("Канал-получатель успешно добавлен", "success")
    return redirect(url_for("index"))


@bp.route("/recipient/<int:id>", methods=["GET"])
@login_required
async def recipient_page(id: int):
    recipient = await RecipientChannel.get_or_none(id=id)
    if not recipient:
        flash("Канал не найден", "error")
        return redirect(url_for("index"))

    await recipient.fetch_related("donor_channels")
    return render_template("recipient.html", recipient=recipient)


@bp.route("/recipient/<int:id>", methods=["DELETE"])
@bp.route("/recipient/delete/<int:id>", methods=["POST"])
@login_required
async def delete_recipient(id: int):
    recipient = await RecipientChannel.get_or_none(id=id)
    if not recipient:
        flash("Канал не найден", "error")
        return redirect(url_for("index"))

    await recipient.delete()
    flash("Канал-получатель успешно удален", "success")
    return redirect(url_for("index"))


@bp.route("/recipient/<int:id>/add_donor", methods=["GET", "POST"])
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
        return redirect(url_for("recipient.recipient_add_donor", id=id))

    donor_id = request.form.get("donor")

    if donor_id == recipient.channel_id:
        flash("Канал не может быть донором и получателем одновременно", "error")
        return redirect(url_for("recipient.recipient_add_donor", id=id))

    if await DonorChannel.exists(channel_id=donor_id, recipient_channel=recipient):
        flash("Канал-донор уже прикреплен к этому каналу-получателю", "error")
        return redirect(url_for("recipient.recipient_add_donor", id=id))

    donor_name = (await client.get_chat(donor_id)).title

    donor = await DonorChannel.create(channel_id=donor_id, name=donor_name, recipient_channel=recipient)

    flash("Канал-донор успешно добавлен", "success")
    return redirect(url_for("recipient.recipient_page", id=id))


@bp.route("/recipient/<int:id>/toggle", methods=["POST"])
@login_required
async def toggle_recipient(id: int):
    recipient = await RecipientChannel.get_or_none(id=id)
    if not recipient:
        flash("Канал не найден", "error")
        return redirect(url_for("index"))

    recipient.is_active = not recipient.is_active
    await recipient.save()

    flash(
        "Пересылка востановлена" if recipient.is_active else "Пересылка отключена",
        "success" if recipient.is_active else "warning",
    )

    return redirect(url_for("index"))
