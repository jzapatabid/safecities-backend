from http import HTTPStatus
from typing import Dict

from flask import make_response

from . import bp
from .auth_config import auth_token
from .schemas.activate_user_schema import ActivateUserRequestSchema, UPDATE_PASSWORD_WITH_TOKEN_EXAMPLE
from .schemas.change_password_request_schema import ChangePasswordRequestSchema
from .schemas.create_user_schema import SignUpSchema
from .schemas.forgot_password_schema import ForgotPasswordSchema
from .schemas.login_user_schema import LoginSchema
from .schemas.pagination_req_schema import UserListRequestSchema
from .schemas.resend_invitation_schema import ResendInvitationSchema
from .schemas.reset_password_request_schema import ResetPasswordRequestSchema
from .services import signin_user, activate_user, login_user, list_users, send_email_to_restart_password, \
    update_user_password_with_token, update_user_password_with_previous_password, resend_invitation, list_all_users
from apiflask import HTTPTokenAuth

auth = HTTPTokenAuth()


# @admin_only()
@bp.post('/signup')
@bp.input(SignUpSchema, "json")
@bp.auth_required(auth_token)
def signup_controller(body: Dict):
    signin_user(body)
    return make_response(
        {
            "code": HTTPStatus.CREATED,
            "message": "An email has been sent to activate the account",
            "data": {}
        },
        HTTPStatus.CREATED
    )


@bp.post("/login")
@bp.input(LoginSchema, "json")
def login_controller(body: Dict):
    if token := login_user(body):
        return make_response(
            {
                "code": HTTPStatus.OK,
                "message": "Logged successfully",
                # "data": {"token": token}
                "data": token
            },
            HTTPStatus.OK
        )

    return make_response(
        {
            "code": HTTPStatus.UNAUTHORIZED,
            "message": "User or password invalid",
        },
        HTTPStatus.UNAUTHORIZED
    )


@bp.post("/activate-account")
@bp.input(ActivateUserRequestSchema, "json", example=UPDATE_PASSWORD_WITH_TOKEN_EXAMPLE)
def activate_user_controller(body: Dict):
    activate_user(body)

    return make_response(
        {
            "code": HTTPStatus.OK,
            "message": 'User activated'
        },
        HTTPStatus.OK
    )


# @admin_only()
@bp.post("/send-activation-token")
@bp.input(ResendInvitationSchema, "json")
@bp.auth_required(auth_token)
def resend_invitation_controller(body: Dict):
    resend_invitation(body)
    return make_response(
        {
            "code": HTTPStatus.OK,
            "message": 'Invitation was resend'
        },
        HTTPStatus.OK
    )


@bp.post("/send-reset-password-token")
@bp.input(ForgotPasswordSchema, "json")
def request_token_to_restart_password_controller(body: Dict):
    # todo: talvez deberiamos notificar si el usuario esta activo
    send_email_to_restart_password(body["email"])
    return make_response(
        {
            "code": HTTPStatus.OK,
        },
        HTTPStatus.OK
    )


@bp.post("/reset-password")
@bp.input(ResetPasswordRequestSchema, "json", example=UPDATE_PASSWORD_WITH_TOKEN_EXAMPLE)
def update_user_password_with_token_controller(body: Dict):
    update_user_password_with_token(
        token=body["token"],
        new_password=body["password"]
    )
    return make_response(
        {
            "code": HTTPStatus.OK,
        },
        HTTPStatus.OK
    )


@bp.post("/change-password")
@bp.input(ChangePasswordRequestSchema, "json")
@bp.auth_required(auth_token)
def update_user_password_with_previous_password_controller(body: Dict):
    update_user_password_with_previous_password(
        user_id=int(auth.current_user["id"]),
        current_password=body["last_password"],
        new_password=body["new_password"]
    )
    return make_response(
        {
            "code": HTTPStatus.OK,
        },
        HTTPStatus.OK
    )


# @admin_only()
@bp.get("/users")
@bp.input(UserListRequestSchema, "query")
@bp.auth_required(auth_token)
def list_user_controller(query: Dict):
    pagination_res = list_users(query)
    return make_response(
        {
            "code": HTTPStatus.OK,
            "data": pagination_res.to_dict()
        },
        HTTPStatus.OK
    )


# @admin_only()
@bp.get("/users/all")
@bp.auth_required(auth_token)
def list_all_user_controller():
    user_list = list_all_users()
    return make_response(
        {
            "code": HTTPStatus.OK,
            "data": user_list
        },
        HTTPStatus.OK
    )
