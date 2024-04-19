from apiflask import APIBlueprint



bp = APIBlueprint('auth', __name__, url_prefix="/auth")

from . import controllers
