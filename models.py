from extensions import db
from datetime import datetime
from passlib.hash import bcrypt
import uuid

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    full_name = db.Column(db.String)
    username = db.Column(db.String(32), unique=True, nullable=False)
    profile_picture_url = db.Column(db.String)
    kyc_status = db.Column(db.String, default="unverified")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, plaintext):
        self.password_hash = bcrypt.hash(plaintext)
    
    def check_password(self, plaintext):
        return bcrypt.verify(plaintext, self.password_hash)

class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    balance = db.Column(db.Numeric(precision=12, scale=2), nullable=False, default=0.00)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("accounts", lazy=True))


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    receiver_account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    amount = db.Column(db.Numeric(precision=12, scale=2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    description = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("Account", foreign_keys=[sender_account_id], backref="outgoing_transactions")
    receiver = db.relationship("Account", foreign_keys=[receiver_account_id], backref="incoming_transactions")


