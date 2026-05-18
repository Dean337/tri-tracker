from flask import Blueprint, render_template

predictor_bp = Blueprint("predictor", __name__)


@predictor_bp.route("/predictor")
def predictor():
    return render_template("predictor.html")
