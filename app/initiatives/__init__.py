from apiflask import APIBlueprint

bp = APIBlueprint('initiatives', __name__, url_prefix="/initiatives")

from . import controllers
