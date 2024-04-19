from flask_cors import CORS
from flask_migrate import Migrate

from app import app
from app.auth import tasks as auth_tasks
from celery_builder import celery_init_app
from db import db

CORS(app)
app.config.from_object("config.DevelopmentConfig")
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!

# app.config.from_mapping(
#     CELERY=dict(
#         broker_url="amqp://guest:guest@localhost:5672",
#         # result_backend="redis://localhost",
#         task_ignore_result=True,
#     ),
# )
# app.config['MAIL_SERVER'] = 'localhost'
# app.config['MAIL_PORT'] = 1025
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = True

db.init_app(app)

migrate = Migrate(app, db)

print(auth_tasks)

celery_app = celery_init_app(app)

# import logging
#
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
