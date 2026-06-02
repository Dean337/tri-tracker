from flask import Blueprint, render_template
from utils import login_required

predictor_bp = Blueprint("predictor", __name__)


@predictor_bp.route("/predictor")
@login_required
def predictor():
    return render_template("predictor.html")
