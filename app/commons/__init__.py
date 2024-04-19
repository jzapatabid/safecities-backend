from apiflask import APIBlueprint

bp = APIBlueprint("api", __name__, url_prefix="/api")

from . import controllers
