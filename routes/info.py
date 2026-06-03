from flask import Blueprint, render_template

info_bp = Blueprint("info", __name__)


@info_bp.route("/guide")
def guide():
    return render_template("guide.html")


@info_bp.route("/methodology")
def methodology():
    return render_template("methodology.html")
