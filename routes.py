# pylint:disable=line-too-long

routes = {
    "home": "/",
    "city_problems": "/city-problems",
    "maps": "/<int:city_id>/<int:problem_id>/maps",
    "problem_causes": "/<int:city_id>/<int:problem_id>/causes",
    "problem_and_cause": "/city/<string:city_id>/problem/<string:problem_id>/cause",
    "cause": "/city/<string:city_id>/cause/<string:cause_id>",
    "problem_cause": "/<int:city_id>/<int:problem_id>/cause/<int:cause_id>",
    "problem_priorization": "/<int:city_id>/<int:problem_id>",
    "cause_facts": "/city/<string:city_id>/problem/<string:problem_id>/cause/<string:cause_id>/facts",
    "login": "/login",
    "signup": "/signup",
    "change_password": "/change-password",
    "swagger": "/docs",
}
