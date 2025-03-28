from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    
    # Relationships
    todos = db.relationship('Todo', backref='user', lazy=True)  # Links User to Todo
    comments = db.relationship('Comment', backref='user', lazy=True)  # Links User to Comment

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# To-Do Model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship with comments
    comments = db.relationship('Comment', backref='todo', lazy=True, cascade="all, delete-orphan")


# Comment Model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    task_id = db.Column(db.Integer, db.ForeignKey('todo.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Followers Model
class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followee_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    follower = db.relationship('User', foreign_keys=[follower_id], backref='following')
    followee = db.relationship('User', foreign_keys=[followee_id], backref='followers')