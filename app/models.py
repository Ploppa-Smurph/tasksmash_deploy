# app/models.py
from .extensions import db
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint # Import UniqueConstraint

# User Model
class User(db.Model, UserMixin):
    __tablename__ = 'user' # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True) # Added index
    email = db.Column(db.String(100), unique=True, nullable=False, index=True) # Added index
    password_hash = db.Column(db.String(256), nullable=False)

    bio = db.Column(db.String(250), nullable=True)
    avatar_url = db.Column(db.String(200), nullable=True)
    profile_is_public = db.Column(db.Boolean, default=True, nullable=False)
    member_since = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    todos = db.relationship('Todo', backref='author', lazy='dynamic', cascade="all, delete-orphan") # Changed backref to 'author'
    comments = db.relationship('Comment', back_populates='user', cascade="all, delete-orphan", lazy='dynamic')
    user_achievements = db.relationship('UserAchievement', backref='user', lazy='dynamic', cascade="all, delete-orphan")

    followed = db.relationship(
        'Follow',
        foreign_keys='Follow.follower_id',
        backref=db.backref('follower_user', lazy='joined'), # Clarified backref name
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    followers = db.relationship(
        'Follow',
        foreign_keys='Follow.followee_id',
        backref=db.backref('followee_user', lazy='joined'), # Clarified backref name
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_achievement(self, achievement_name):
        """Checks if the user has a specific achievement by name."""
        return db.session.query(UserAchievement.id)\
            .join(UserAchievement.achievement)\
            .filter(UserAchievement.user_id == self.id, Achievement.name == achievement_name)\
            .first() is not None

    def follow(self, user_to_follow):
        if not self.is_following(user_to_follow) and self != user_to_follow:
            f = Follow(follower_id=self.id, followee_id=user_to_follow.id)
            db.session.add(f)
            return f
        return None

    def unfollow(self, user_to_unfollow):
        f = self.followed.filter_by(followee_id=user_to_unfollow.id).first()
        if f:
            db.session.delete(f)
            return f
        return None

    def is_following(self, user_to_check):
        return self.followed.filter_by(followee_id=user_to_check.id).first() is not None

    def get_public_todos(self):
        """Returns todos that should be visible on a public profile."""
        if self.profile_is_public:
            return self.todos.order_by(Todo.created_at.desc())
        # Return an empty query if profile is private or no todos
        return Todo.query.filter_by(id=-1) # Effectively an empty query

# To-Do Model
class Todo(db.Model):
    __tablename__ = 'todo' # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True) # Added index
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_todo_user_id'), nullable=False) # Added FK name
    completed = db.Column(db.Boolean, default=False, nullable=False)
    edit_count = db.Column(db.Integer, default=0, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    # is_public = db.Column(db.Boolean, default=True, nullable=False) # For task-level privacy

    # Changed backref name on Todo from 'user' to 'author' to avoid conflict if User has a 'user' field.
    # The 'author' backref is on the User.todos relationship.
    comments = db.relationship('Comment', back_populates='task', cascade="all, delete-orphan", lazy='dynamic')

    @property
    def is_overdue(self):
        if self.due_date and not self.completed:
            return self.due_date < date.today()
        return False

# Comment Model
class Comment(db.Model):
    __tablename__ = 'comment' # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True) # Added index
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_comment_user_id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('todo.id', name='fk_comment_task_id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id', name='fk_comment_parent_id'), nullable=True)

    user = db.relationship('User', back_populates='comments')
    task = db.relationship('Todo', back_populates='comments')
    replies = db.relationship('Comment', backref=db.backref('parent_comment', remote_side=[id]), lazy='dynamic', cascade="all, delete-orphan")

# Followers Model
class Follow(db.Model):
    __tablename__ = 'follow'
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_follow_follower_id'), primary_key=True)
    followee_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_follow_followee_id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensures a user cannot follow another user more than once
    __table_args__ = (UniqueConstraint('follower_id', 'followee_id', name='uq_follower_followee'),)

# Achievement Models
class Achievement(db.Model):
    __tablename__ = 'achievement'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True) # Added index
    description = db.Column(db.String(255), nullable=False)

class UserAchievement(db.Model):
    __tablename__ = 'user_achievement'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_userachievement_user_id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id', name='fk_userachievement_achievement_id'), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)

    achievement = db.relationship('Achievement', backref=db.backref('user_awards', lazy='dynamic')) # Added backref

    # Ensures a user cannot get the same achievement multiple times
    __table_args__ = (UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement'),)


# Initial Achievements to Seed (Single source of truth for definitions)
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
