from apiflask import APIBlueprint

bp = APIBlueprint('problems', __name__, url_prefix="/problems")

from . import controllers