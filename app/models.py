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
    todos = db.relationship('Todo', backref='user', lazy=True)
    comments = db.relationship('Comment', back_populates='user', cascade="all, delete-orphan")
    user_achievements = db.relationship('UserAchievement', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_achievement(self, achievement_name):
        return any(ua.achievement.name == achievement_name for ua in self.user_achievements)

# To-Do Model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    edit_count = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', back_populates='task', cascade="all, delete-orphan")

# Comment Model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

    user = db.relationship('User', back_populates='comments')
    task = db.relationship('Todo', back_populates='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

# Followers Model
class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followee_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    follower = db.relationship('User', foreign_keys=[follower_id], backref='followed_users')
    followee = db.relationship('User', foreign_keys=[followee_id], backref='followers')

# Achievement Models
class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)

    achievement = db.relationship('Achievement')

# Initial Achievements to Seed
achievements = [
    Achievement(name='Task Initiator', description='Created 10 tasks'),
    Achievement(name='Goal Crusher', description='Completed 5 tasks'),
    Achievement(name='Comment Commander', description='Posted your first comment'),
    Achievement(name='Task Master', description='Created 50 tasks'),
    Achievement(name='Finisher', description='Completed 25 tasks'),
    Achievement(name='Perfectionist', description='Completed all your tasks'),
    Achievement(name='Chatterbox', description='Left 10 comments'),
    Achievement(name='Reply Ruler', description='Left 5 replies'),
    Achievement(name='Friendly Follower', description='Followed 1 user'),
    Achievement(name='Social Butterfly', description='Followed 5 users'),
    Achievement(name='Popular Pick', description='A task of yours got 5 comments'),
    Achievement(name='Empty Inbox', description='You have no incomplete tasks'),
    Achievement(name='Procrastinator', description='You edited the same task 3 times')
]
