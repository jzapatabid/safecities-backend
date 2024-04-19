import os

from apiflask import APIFlask
from flask import send_from_directory

from .auth import bp as auth_bp
from .causes import bp as causes_bp
from .initiatives import bp as initiatives_bp
from .initiatives import bp as initiatives_bp
from .plan import bp as plan_bp
from .problems import bp as problems_bp
from .commons import bp as common_bp

app = APIFlask(__name__, template_folder="auth/templates/")

app.register_blueprint(auth_bp)
app.register_blueprint(problems_bp)
app.register_blueprint(causes_bp)
app.register_blueprint(initiatives_bp)
app.register_blueprint(plan_bp)

app.register_blueprint(common_bp)

from . import commands

app.config.from_object("config.DevelopmentConfig")

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
