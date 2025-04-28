from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_login import LoginManager


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Initialize the LoginManager and attach it to the app
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # where to redirect for login if not authenticated

# Import models so that they are registered with SQLAlchemy
from app import routes, models

@login_manager.user_loader
def load_user(user_id):
    # This function tells Flask-Login how to load a user
    # Make sure to convert the user_id to int if needed.
    from app.models import User
    return User.query.get(int(user_id))
