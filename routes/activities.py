from flask import Blueprint, render_template

activities_bp = Blueprint("activities", __name__)


@activities_bp.route("/activities")
def activities():
    return render_template("activities.html")


@activities_bp.route("/activities/<int:activity_id>")
def activity_detail(activity_id):
    return render_template("activity_detail.html", activity_id=activity_id)
