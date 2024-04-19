import abc
import os

from dotenv import load_dotenv

load_dotenv()

DB_USER = os.environ["DB_USER"]
DB_PWD = os.environ["DB_PWD"]
DB_URL = os.environ["DB_URL"]
DB_NAME = os.environ["DB_NAME"]
DB_PORT = int(os.environ["DB_PORT"])

RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
RABBITMQ_PORT = int(os.environ["RABBITMQ_PORT"])
RABBITMQ_USER = os.environ["RABBITMQ_USER"]
RABBITMQ_PASSWORD = os.environ["RABBITMQ_PASSWORD"]


class BaseConfig(abc.ABC):
    API_TITLE = "Stores REST API"
    API_VERSION = "v1"

    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PWD}@{DB_URL}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True
    }

    CELERY = dict(
        broker_url=f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}",
        # result_backend="redis://localhost",
        task_ignore_result=True,
    )

    MAIL_SERVER = os.environ["MAIL_SERVER"]
    MAIL_PORT = int(os.environ["MAIL_PORT"])
    MAIL_USE_TLS = bool(int(os.environ.get("MAIL_USE_TLS", 0)))
    MAIL_USE_SSL = bool(int(os.environ.get("MAIL_USE_SSL", 0)))
    MAIL_SUPPRESS_SEND = bool(int(os.environ.get("MAIL_SUPPRESS_SEND", 0)))

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    SERVER_NAME_ = os.environ["SERVER_NAME"]
    BACKOFFICE_PHONE_NUMBER = os.getenv("BACKOFFICE_PHONE_NUMBER", "000000000000")
    BACKOFFICE_PHONE_ANNEX = os.getenv("BACKOFFICE_PHONE_ANNEX", "0000")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    SECRET_KEY = 'SECRET_KEY'


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    SECRET_KEY = 'SECRET_KEY'


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    # SECRET_KEY = os.environ["SECRET_KEY"]
