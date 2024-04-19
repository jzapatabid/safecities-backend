from http import HTTPStatus

from apiflask import HTTPError


class IncorrectPasswordError(HTTPError):
    # Use only when user is already logged in
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message = "Incorrect password"
    extra_data = dict()


class RepeatedPasswordError(HTTPError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message = "New password shouldn't be used previously"
    extra_data = dict()


class TokenUsedOrExpiredError(HTTPError):
    status_code = HTTPStatus.UNAUTHORIZED
    message = "Token used or expired"
    extra_data = dict()
