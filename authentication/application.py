import re
import json
from flask import Flask, request, Response
from configuration import Configuration
from models import database, User, UserRole
from sqlalchemy import and_
from decorator import role_check
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

PASSWORD_REG_NUM = r'\d'
PASSWORD_REG_LOWER = r'[a-z]'
PASSWORD_REG_UPPER = r'[A-Z]'
EMAIL_REG = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


def error_message(msg: str, status: int = 400):
    json_message = {
        "message": msg
    }
    return Response(json.dumps(json_message), status=status)


def token_message(access_token: str, refresh_token: str, status: int = 200):
    json_message = {
        "accessToken": access_token,
        "refreshToken": refresh_token
    }
    return Response(json.dumps(json_message), status=status)


def refresh_token_message(access_token: str, status: int = 200):
    json_message = {
        "accessToken": access_token
    }
    return Response(json.dumps(json_message), status=status)


@application.route("/register", methods=["POST"])
def register():
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    is_customer = request.json.get("isCustomer", None)

    # field missing check
    email_empty = len(email) == 0
    password_empty = len(password) == 0
    forename_empty = len(forename) == 0
    surname_empty = len(surname) == 0
    is_customer_empty = is_customer is None

    if forename_empty:
        return error_message("Field forename is missing.")
    elif surname_empty:
        return error_message("Field surname is missing.")
    elif email_empty:
        return error_message("Field email is missing.")
    elif password_empty:
        return error_message("Field password is missing.")
    elif is_customer_empty:
        return error_message("Field isCustomer is missing.")

    # email format check
    if not re.match(EMAIL_REG,email) or len(email)>256:
        return error_message("Invalid email.")

    # password format check
    if re.search(PASSWORD_REG_NUM, password) is None or re.search(PASSWORD_REG_LOWER, password) is None or re.search(
            PASSWORD_REG_UPPER, password) is None or len(password) > 256 or len(password) < 8:
        return error_message("Invalid password.")

    # email already exists check
    if len(User.query.filter(User.email == email).all()) != 0:
        return error_message("Email already exists.")

    if is_customer:
        user = User(email=email, password=password, forename=forename, surname=surname, roles=UserRole.customer)  # roles="customer"
    else:
        user = User(email=email, password=password, forename=forename, surname=surname, roles=UserRole.storekeeper) # roles="storekeeper"
    database.session.add(user)
    database.session.commit()

    return Response("", status=200)


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    # empty fields check
    email_empty = len(email) == 0
    password_empty = len(password) == 0

    if email_empty:
        return error_message("Field email is missing.")
    elif password_empty:
        return error_message("Field password is missing.")

    # email format check
    if not re.match(EMAIL_REG,email) or len(email)>256:
        return error_message("Invalid email.")

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    # user doesn't exist
    if not user:
        return error_message("Invalid credentials.")

    additional_claims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": str(user.roles)  # user.roles.split()  # list of roles
    }

    access_token = create_access_token(identity=user.email, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=user.email, additional_claims=additional_claims)

    # return Response ( accessToken, status = 200 )
    return token_message(access_token=access_token, refresh_token=refresh_token)


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refresh_claims = get_jwt()

    additional_claims = {
        "forename": refresh_claims["forename"],
        "surname": refresh_claims["surname"],
        "roles": refresh_claims["roles"]
    }

    return refresh_token_message(access_token=create_access_token(identity=identity,
                                                                  additional_claims=additional_claims))


@application.route("/delete", methods=["POST"])
@role_check("admin")
def remove_user():
    email = request.json.get("email", "")

    # field missing check
    email_empty = len(email) == 0

    if email_empty:
        return error_message("Field email is missing.")

    # email format check
    if not re.match(EMAIL_REG, email) or len(email) > 256:
        return error_message("Invalid email.")

    user = User.query.filter(User.email == email).first()
    if not user:
        return error_message("Unknown user.")
    database.session.delete(user)
    database.session.commit()
    return Response("", status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0")
