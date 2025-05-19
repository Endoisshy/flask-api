from main import app
from models import db
from models import User, Account, Transaction

with app.app_context():
    db.create_all()
