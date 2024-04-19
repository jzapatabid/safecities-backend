import datetime
from typing import Dict
from uuid import uuid4

import jwt


def encode_jwt_token(body: Dict, secret: str, expiration: datetime.timedelta) -> str:
    utc_now = datetime.datetime.utcnow()
    body.update(**{
        "iat": utc_now,
        "exp": utc_now + expiration,
        "uuid": str(uuid4())
    })
    encoded_jwt = jwt.encode(body, secret, algorithm="HS256")
    print("TOKEN: " + encoded_jwt)
    return encoded_jwt


def decode_jwt_token(encoded_jwt: str, secret: str) -> Dict:
    return jwt.decode(encoded_jwt, secret, algorithms=["HS256"], options={"verify_exp": False})
