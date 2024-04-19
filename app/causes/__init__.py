from apiflask import APIBlueprint

bp = APIBlueprint('causes', __name__, url_prefix="/causes")

from . import controllers
