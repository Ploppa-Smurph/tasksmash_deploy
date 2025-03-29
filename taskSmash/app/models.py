from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    # Relationships
    todos = db.relationship('Todo', backref='user', lazy=True)  # Links User to Todo
    comments = db.relationship('Comment', back_populates='user', cascade="all, delete-orphan")  # Links User to Comment

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# To-Do Model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship with comments
        # Relationship with Comment using back_populates
    comments = db.relationship('Comment', back_populates='task', cascade="all, delete-orphan")

# Comment Model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign keys to the user and the task
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)
    
    # Self-referential foreign key for nested comments (replies)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

    # Relationships
    user = db.relationship('User', back_populates='comments')
    task = db.relationship('Todo', back_populates='comments')
    # Relationship to access replies: a comment can have many child comments
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

# Followers Model
class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followee_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    
    # Relationships
    follower = db.relationship('User', foreign_keys=[follower_id], backref='followed_users')
    followee = db.relationship('User', foreign_keys=[followee_id], backref='followers')