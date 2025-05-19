from flask import Blueprint

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")

from . import routes