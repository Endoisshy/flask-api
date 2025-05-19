from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, get_jwt
from flasgger import swag_from
from models import db, Account, Transaction, User
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, update
from marshmallow import Schema, fields, ValidationError, validate
from datetime import timedelta
from decimal import Decimal
import uuid
import re


USERNAME_REGEX = r"^[A-Za-z0-9_]{3,30}$"

transactions_bp = Blueprint('transactions', __name__)

class TransferSchema(Schema):
    recipient_username = fields.String(
        required=True,
        validate=validate.Regexp(USERNAME_REGEX, error="Invalid username format.")
    )
    amount = fields.Float(required=True, validate=validate.Range(min=0.01))


@transactions_bp.route('/one-time-token', methods=['POST'])
@jwt_required()
@swag_from('docs/transactions/one_time_token.yml', methods=['POST'])
def generate_one_time_token():
    user_id = get_jwt_identity()
    one_time_token = create_access_token(
        identity=user_id,
        expires_delta=timedelta(minutes=2),
        additional_claims={"one_time": True}
    )
    return jsonify({"one_time_token": one_time_token}), 200

@transactions_bp.route('/balance', methods=['GET'])
@jwt_required()
@swag_from('docs/transactions/balance.yml')
def get_balance():
    user_id = get_jwt_identity()
    account = Account.query.filter_by(user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    return jsonify({'balance': str(account.balance)})

@transactions_bp.route('/transfer', methods=['POST'])
@jwt_required()
@swag_from('docs/transactions/transfer.yml')
def transfer():
    claims = get_jwt()
    if not claims.get("one_time"):
        return jsonify({"error": "One-time token required"}), 401 
        # two minute JWT for sensitive function

    user_id = get_jwt_identity()
    try:
        raw_data = request.get_json()
        data = TransferSchema().load(raw_data)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    amount = Decimal(str(data['amount']))
    recipient_username = data['recipient_username'].strip().lower()

    try:
        with db.session.begin_nested():
            # Lock sender's account
            sender_account = db.session.execute(
                select(Account).where(Account.user_id == user_id).with_for_update()
            ).scalar_one_or_none()

            if not sender_account:
                return jsonify({'error': 'Sender account not found'}), 404
            if sender_account.balance < amount:
                return jsonify({'error': 'Insufficient funds'}), 400

            # Get recipient user
            recipient_user = db.session.execute(
                select(User).where(User.username == recipient_username)
            ).scalar_one_or_none()

            if not recipient_user:
                return jsonify({'error': 'Recipient not found'}), 404
            
            if recipient_user.id == user_id:
                return jsonify({'error': 'Cannot transfer to self'}), 400

            # Lock recipient's account
            recipient_account = db.session.execute(
                select(Account).where(Account.user_id == recipient_user.id).with_for_update()
            ).scalar_one_or_none()

            if not recipient_account:
                return jsonify({'error': 'Recipient account not found'}), 404

            sender_account.balance -= amount
            recipient_account.balance += amount

            transaction = Transaction(
                sender_account_id=sender_account.id,
                receiver_account_id=recipient_account.id,
                amount=amount,
                currency="USD",
                status="pending"
            )
            db.session.add(transaction)

        db.session.commit()
        return jsonify({'message': 'Transfer successful'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Transaction failed'}), 500

