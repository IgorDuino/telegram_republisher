from flask import Blueprint, render_template, redirect, flash, url_for

from models import RecipientChannel, DonorChannel

from web.utils import login_required


bp = Blueprint("donor", __name__)


@bp.route("/donor/<int:id>", methods=["GET"])
@login_required
async def donor_page(id: int):
    donor = await DonorChannel.get_or_none(id=id)
    if not donor:
        flash("Канал не найден", "error")
        return redirect(url_for("index"))

    await donor.fetch_related("recipient_channel")
    return render_template("donor.html", donor=donor)


@bp.route("/donor/<int:id>", methods=["DELETE"])
@bp.route("/donor/delete/<int:id>", methods=["POST"])
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
        return redirect(url_for("donor.donor_page", id=id))

    await donor.delete()

    flash("Канал-донор успешно удален", "success")
    return redirect(url_for("index"))


@bp.route("/donor/<int:id>/toggle", methods=["POST"])
@login_required
async def toggle_donor(id: int):
    donor = await DonorChannel.get_or_none(id=id)
    if not donor:
        flash("Канал не найден", "error")
        return redirect(url_for("index"))

    donor.is_active = not donor.is_active
    await donor.save()

    flash(
        "Пересылка востановлена" if donor.is_active else "Пересылка отключена",
        "success" if donor.is_active else "warning",
    )

    return redirect(url_for("index"))
