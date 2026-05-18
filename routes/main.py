from flask import Blueprint, render_template, redirect, url_for, session

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))
