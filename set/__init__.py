from flask import Blueprint

set_bp = Blueprint("set", __name__, url_prefix="/sets")

from . import routes