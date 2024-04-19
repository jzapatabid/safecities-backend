from apiflask import HTTPTokenAuth

from .utils import decode_jwt_token

auth_token = HTTPTokenAuth()


@auth_token.verify_token
def verify_token(token):
    if token:
        token_dict = decode_jwt_token(token, "super-secret")
        # todo: please uncomment me
        # if datetime.datetime.utcnow() > datetime.datetime.utcfromtimestamp(token_dict["exp"]):
        #     raise ValidationError({"token": ["Bearer Token expired"]})
        return token_dict
