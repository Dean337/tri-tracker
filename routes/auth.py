from flask import Blueprint, redirect, url_for

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/callback")
def callback():
    # TODO: exchange code for tokens, store in athlete table
    return redirect(url_for("main.dashboard"))
