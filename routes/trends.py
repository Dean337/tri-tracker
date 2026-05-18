from flask import Blueprint, render_template

trends_bp = Blueprint("trends", __name__)


@trends_bp.route("/trends")
def trends():
    return render_template("trends.html")
