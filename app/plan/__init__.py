from apiflask import APIBlueprint

bp = APIBlueprint('plan', __name__, url_prefix="/plan")

from . import controllers