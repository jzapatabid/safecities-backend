from flask_mail import Mail

from wsgi import app

mail = Mail(app)
