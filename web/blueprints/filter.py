from flask import Blueprint, render_template, redirect, request, flash, url_for

from models import Filter, RecipientChannel, DonorChannel, FilterScope, FilterAction

from web.utils import login_required


bp = Blueprint("filter", __name__)


@bp.route("/filter/<int:id>", methods=["GET"])
@login_required
async def filter_page(id: int):
    filter = await Filter.get_or_none(id=id)
    if not filter:
        flash("Фильтр не найден", "error")
        return redirect(url_for("index"))

    return render_template("filter.html", filter=filter)


@bp.route("/filter/<int:id>", methods=["DELETE"])
@bp.route("/filter/delete/<int:id>", methods=["POST"])
@login_required
async def delete_filter(id: int):
    filter = await Filter.get_or_none(id=id)
    if not filter:
        flash("Фильтр не найден", "error")
        return redirect(url_for("index"))

    await filter.delete()
    flash("Фильтр успешно удален", "success")
    return redirect(url_for("index"))


@bp.route("/filter/add/", methods=["GET"])
@login_required
async def add_filter_page():
    recipients = await RecipientChannel.all()
    donors = await DonorChannel.all().prefetch_related("recipient_channel")

    return render_template("add_filter.html", recipients=recipients, donors=donors)


@bp.route("/filter/add/", methods=["POST"])
@login_required
async def add_filter():
    try:
        scope = FilterScope(request.form.get("scope"))
        action = FilterAction(request.form.get("action"))
        pattern = request.form["pattern"]
        replace_with = request.form.get("replace_with")
        name = request.form["name"]
        is_regex = (request.form.get("is_regex") in ["true", "1"]) if request.form.get("is_regex") else False

    except (ValueError, TypeError):
        flash("Данные некорректны или заполнены не все поля", "error")
        return redirect(url_for("index"))

    if scope == FilterScope.RECIPIENT:
        recipient_id = request.form.get("recipient_id")
        recipient = await RecipientChannel.get_or_none(id=recipient_id)
        if not recipient:
            flash("Канал-получатель не найден", "error")
            return redirect(url_for("index"))

        filter = await Filter.create(
            name=name,
            scope=scope,
            action=action,
            pattern=pattern,
            replace_with=replace_with,
            is_regex=is_regex,
            recipient_channel=recipient,
        )

        flash("Фильтр успешно добавлен", "success")
        return redirect(url_for("recipient.recipient_page", id=recipient_id))

    elif scope == FilterScope.DONOR:
        donor_id = request.form.get("donor_id")
        donor = await DonorChannel.get_or_none(id=donor_id)
        if not donor:
            flash("Канал-донор не найден", "error")
            return redirect(url_for("index"))

        filter = await Filter.create(
            name=name,
            scope=scope,
            action=action,
            pattern=pattern,
            replace_with=replace_with,
            is_regex=is_regex,
            donor_channel=donor,
        )

        flash("Фильтр успешно добавлен", "success")
        return redirect(url_for("donor.donor_page", id=donor_id))

    filter = await Filter.create(
        name=name,
        scope=scope,
        action=action,
        pattern=pattern,
        replace_with=replace_with,
        is_regex=is_regex,
    )

    flash("Фильтр успешно добавлен", "success")
    return redirect(url_for("index"))


@bp.route("/filter/<int:id>/toggle", methods=["POST"])
@login_required
async def toggle_filter(id: int):
    filter = await Filter.get_or_none(id=id)
    if not filter:
        flash("Фильтр не найден", "error")
        return redirect(url_for("index"))

    filter.is_active = not filter.is_active
    await filter.save()

    flash(
        "Фильтр востановлен" if filter.is_active else "Фильтр отключен",
        "success" if filter.is_active else "warning",
    )

    return redirect(url_for("index"))
