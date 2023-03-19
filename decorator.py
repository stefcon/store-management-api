from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt;
from flask import Response, request
from flask import jsonify


def role_check(role):
    def inner_role(function):

        @wraps(function)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if "roles" in claims and role in claims["roles"]:
                return function(*args, **dict(**kwargs))
            else:
                message = jsonify(msg="Missing Authorization Header")
                message.status_code = 401
                return message

        return decorator

    return inner_role
