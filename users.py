from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models import User, Account
from extensions import db
from marshmallow import Schema, fields, validate, ValidationError
from flasgger import swag_from
import re


EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$"
)

users_bp = Blueprint('users', __name__)

class RegistrationSchema(Schema):
    email = fields.String(required=True, validate=[
        validate.Length(max=255),
        validate.Regexp(EMAIL_REGEX, error="Invalid email format.")
    ])
    password = fields.String(required=True, validate=validate.And(
    validate.Length(min=12, max=128),
    validate.Regexp(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).+$',
                    error="Password must contain uppercase, lowercase, digit, and special character.")))

    full_name = fields.String(
        required=True,
        validate=[
            validate.Length(min=2, max=100),
            validate.Regexp(
                r"^[A-Za-z\s'-]+$",
                error="Full name may only contain letters, spaces, hyphens, and apostrophes."
            )
        ]
    )

    username = fields.String(
    required=True,
    validate=[
        validate.Length(min=3, max=32),
        validate.Regexp(r"^[a-zA-Z0-9_]+$", error="Username must be alphanumeric with optional underscores.")
    ]
)

registration_schema = RegistrationSchema()

class LoginSchema(Schema):
    email = fields.String(required=True, validate=[
        validate.Length(max=255),
        validate.Regexp(EMAIL_REGEX, error="Invalid email format.")
    ])
    password = fields.String(required=True)

login_schema = LoginSchema()

@users_bp.route('/login', methods=['POST'])
@swag_from('docs/users/login.yml')
def login():
    try:
        data = login_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    email = data["email"].strip().lower()
    password = data["password"]

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "kyc_status": user.kyc_status
        }
    }), 200


@users_bp.route('/register', methods=['POST'])
@swag_from('docs/users/register.yml', methods=['POST'])
def register():
    try:
        data = registration_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    email = data["email"].strip().lower()
    password = data["password"]
    full_name = data.get("full_name")
    username = data["username"].strip().lower()

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 400


    user = User.query.filter_by(email=email).first()
    # Here there could be a small chance of a race condition
    # if we were to just use db.session.commit() it could possibly try to commit duplicates
    # that would return a DB error to the user.
    # We fix this by wrapping the commit in a try block that handles the exception
    if not user:
        new_user = User(email=email, full_name=full_name, username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        new_account = Account(user_id=new_user.id, balance=100000.0) # Giving the test accounts a balance for example
        db.session.add(new_account)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    # Doing it this way with the same response for successful and failed registration avoids
    # revealing valid login user enumeration. In production this would be setup with email verification
    # and an email would only be sent if the user does not already exist. For the sake of this brief example API
    # we'll assume that those measures are already in place.

    return jsonify({"message": "A verification email has been sent to your provided email address"}), 200

@users_bp.route('/currentuser', methods=['GET'])
@jwt_required()
@swag_from('docs/users/currentuser.yml')
def current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "kyc_status": user.kyc_status
    })
