from flask import session, flash, redirect
from functools import wraps


def login_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Необходимо авторизоваться", "error")
            return redirect("/login")
        return await f(*args, **kwargs)

    return decorated_function
