from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

# Import models so that they are registered with SQLAlchemy
from app import models

# Import routes so that the route decorators add endpoints to your app
from app import routes