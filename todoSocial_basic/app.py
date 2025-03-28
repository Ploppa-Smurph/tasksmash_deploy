from flask import Flask, request, render_template, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from forms import EditTaskForm, LoginForm, RegisterForm
from dotenv import load_dotenv
import jwt
import requests
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = 'superSecretKey'

# Load environment variables from .env file
load_dotenv()

# SQLAlchemy setup
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Mailgun Configuration (Replace these with your Mailgun credentials)
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)

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
    comments = db.relationship('Comment', backref='task', lazy=True, cascade="all, delete-orphan")

# Comment Model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    task_id = db.Column(db.Integer, db.ForeignKey('todo.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='comments')

# Followers Model
class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followee_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    # Relationships to help navigate followers and followees easily
    follower = db.relationship('User', foreign_keys=[follower_id], backref='following')
    followee = db.relationship('User', foreign_keys=[followee_id], backref='followers')

# Initialize the database
with app.app_context():
    # db.drop_all()  # Drop all tables (for development purposes)
    db.create_all()

# Mailgun email-sending function
def send_mailgun_email(recipient, subject, body):
    """Send an email using Mailgun."""
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"Password Reset <{SENDER_EMAIL}>",
            "to": recipient,
            "subject": subject,
            "text": body
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    return response

# Password Reset Request Route
@app.route("/reset_request", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            token = jwt.encode(
                {
                    'user_id': user.id,
                    'exp': datetime.utcnow() + timedelta(hours=1)
                },
                app.secret_key,
                algorithm="HS256"
            )
            reset_url = url_for("reset_password", token=token, _external=True)
            response = send_mailgun_email(
                recipient=email,
                subject="Password Reset Request",
                body=f"Click the following link to reset your password:\n{reset_url}"
            )
            if response.status_code == 200:
                flash("A password reset link has been sent to your email.")
            else:
                flash("Failed to send password reset email. Please try again.")
        else:
            flash("No account found with that email.")
        return redirect(url_for("home"))
    return render_template("resetRequest.html")

# Reset Password Route
@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except jwt.ExpiredSignatureError:
        flash("The reset link has expired.")
        return redirect(url_for("reset_request"))
    except jwt.InvalidTokenError:
        flash("Invalid reset link.")
        return redirect(url_for("reset_request"))

    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        new_password = request.form.get("password")
        user.set_password(new_password)
        db.session.commit()
        flash("Your password has been reset successfully!")
        return redirect(url_for("home"))
    return render_template("resetPassword.html", token=token)

# Home Route
@app.route("/", methods=["GET", "POST"])
def home():
    login_form = LoginForm()
    register_form = RegisterForm()
    return render_template("index.html", login_form=login_form, register_form=register_form)

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session["username"] = username
        session["user_id"] = user.id
        return redirect(url_for("dashboard"))
    else:
        flash("Invalid username or password")
        return redirect(url_for("home"))

# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():  # Validate the form
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Check if the username or email already exists
        existing_user_by_username = User.query.filter_by(username=username).first()
        existing_user_by_email = User.query.filter_by(email=email).first()

        if existing_user_by_username:
            flash("Username already exists. Please choose another.", "error")
        elif existing_user_by_email:
            flash("An account already exists with this email. Please login or reset your password.", "error")
        else:
            # Create a new user
            new_user = User(username=username, email=email)
            new_user.set_password(password)  # Assume this hashes the password securely
            db.session.add(new_user)
            db.session.commit()

            # Log the user in after successful registration
            session["username"] = username
            session["user_id"] = new_user.id
            return redirect(url_for("dashboard"))

    # Render the registration form with error messages (if any)
    return render_template("register.html", form=form)

# Dashboard Route (To-Do List)
@app.route("/dashboard")
def dashboard():
    if "username" in session:
        user_id = session["user_id"]
        # Fetch all tasks with their comments
        tasks = Todo.query.filter_by(user_id=user_id).all()

        # Debug: Print tasks and their comments
        for task in tasks:
            print(f"Task ID: {task.id}, Content: {task.content}, Created: {task.created}")
            for comment in task.comments:
                print(f" - Comment: {comment.content}, Created: {comment.created}")        
        return render_template("dashboard.html", tasks=tasks)
    return redirect(url_for("home"))

# Add To-Do Route
@app.route("/add", methods=["POST"])
def add_todo():
    if "username" in session:
        content = request.form.get("content")
        user_id = session["user_id"]
        new_todo = Todo(content=content, user_id=user_id)
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return redirect(url_for("home"))

# Edit To-Do Route
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_todo(id):
    if "username" in session:
        task = Todo.query.get_or_404(id)
        if task.user_id == session["user_id"]:  # Ensure the user owns the task
            form = EditTaskForm(obj=task)  # Pre-populate the form with the task's content
            
            if form.validate_on_submit():
                task.content = form.content.data
                db.session.commit()
                return redirect(url_for("dashboard"))
            
            return render_template("edit.html", task=task, form=form)
    return redirect(url_for("home"))

# Delete Task Route
@app.route("/delete/<int:id>")
def delete_todo(id):
    if "username" in session:
        todo = Todo.query.get_or_404(id)
        if todo.user_id == session["user_id"]:  # Ensure the user owns the task
            db.session.delete(todo)  # Cascade deletes comments
            db.session.commit()
        return redirect(url_for("dashboard"))
    return redirect(url_for("home"))

# Add Comment Route
@app.route("/comment/<int:task_id>", methods=["POST"])
def add_comment(task_id):
    if "username" in session:
        content = request.form.get("comment")
        user_id = session["user_id"]
        new_comment = Comment(content=content, task_id=task_id, user_id=user_id)
        db.session.add(new_comment)
        db.session.commit()
    return redirect(url_for("dashboard"))  

# View Task with Comments
@app.route("/task/<int:task_id>")
def view_task(task_id):
    if "username" in session:
        task = Todo.query.get_or_404(task_id)
        comments = Comment.query.filter_by(task_id=task_id).all()
        return render_template("task.html", task=task, comments=comments)
    return redirect(url_for("home"))

# Logout Route
@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("user_id", None)
    return redirect(url_for("home"))

# Run the App
if __name__ == '__main__':
    app.run(debug=True)
