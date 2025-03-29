from flask import render_template, request, redirect, url_for, flash, session, current_app
from app import app, db
from app.models import User, Todo, Comment, Follow
from app.mail import send_mailgun_email
from flask_login import login_user, login_required, current_user, logout_user
import jwt
from datetime import datetime, timedelta
from app.forms import LoginForm, RegisterForm, EditTaskForm

# -----------------------------
# Password Reset Routes
# -----------------------------
@app.route("/reset_request", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            token = jwt.encode(
                {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=1)},
                current_app.config["SECRET_KEY"],
                algorithm="HS256"
            )
            reset_url = url_for("reset_password", token=token, _external=True)
            send_mailgun_email(
                recipient=email,
                subject="Password Reset Request",
                body=f"Click the link to reset your password: {reset_url}"
            )
            flash("Password reset link sent!", "success")
        else:
            flash("No user found with that email address.", "error")
    return render_template("resetRequest.html")


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
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
        return redirect(url_for("landing_page"))
    return render_template("resetPassword.html", token=token)

# -----------------------------
# To-Do Routes
# -----------------------------
@app.route("/add", methods=["POST"])
@login_required
def add_todo():
    content = request.form.get("content")
    new_todo = Todo(content=content, user_id=current_user.id)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_todo(id):
    task = Todo.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash("You do not have permission to edit this to-do.", "error")
        return redirect(url_for("dashboard"))
    form = EditTaskForm(obj=task)
    if form.validate_on_submit():
        task.content = form.content.data
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("edit.html", task=task, form=form)


@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_todo(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id != current_user.id:
        flash("You do not have permission to delete this to-do.", "error")
        return redirect(url_for("dashboard"))
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("dashboard"))

# -----------------------------
# Comment Routes
# -----------------------------
@app.route("/comment/<int:task_id>", methods=["POST"])
@login_required
def add_comment(task_id):
    content = request.form.get("comment")
    new_comment = Comment(content=content, task_id=task_id, user_id=current_user.id)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/task/<int:task_id>")
@login_required
def view_task(task_id):
    task = Todo.query.get_or_404(task_id)
    comments = Comment.query.filter_by(task_id=task_id).all()
    return render_template("task.html", task=task, comments=comments)

# -----------------------------
# Home, Login & Register Routes
# -----------------------------
@app.route("/")
def landing_page():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    
    login_form = LoginForm()
    register_form = RegisterForm()
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash("You have been logged in successfully!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")
            return render_template("login.html", login_form=login_form, register_form=register_form, show_create_account=True)
    
    return render_template("login.html", login_form=login_form, register_form=register_form, show_create_account=False)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET" and "keep_flash" not in request.args:
        session.pop('_flashes', None)
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        existing_user_by_username = User.query.filter_by(username=username).first()
        existing_user_by_email = User.query.filter_by(email=email).first()
        
        if existing_user_by_username or existing_user_by_email:
            flash("Username or email already exists.", "error")
            return redirect(url_for("register", keep_flash=1))
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully!", "success")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)

# -----------------------------
# Miscellaneous Routes
# -----------------------------
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("landing_page"))

# -----------------------------
# Comment Reply Route
# -----------------------------
@app.route("/add_comment_reply/<int:comment_id>", methods=["POST"])
@login_required
def add_comment_reply(comment_id):
    parent_comment = Comment.query.get_or_404(comment_id)
    reply_content = request.form.get("reply")
    if not reply_content:
        flash("Reply cannot be empty.", "error")
        return redirect(url_for("dashboard"))
    reply = Comment(
        content=reply_content,
        user_id=current_user.id,
        task_id=parent_comment.task_id,
        parent_id=parent_comment.id
    )
    db.session.add(reply)
    db.session.commit()
    flash("Your reply has been added.", "success")
    return redirect(url_for("dashboard"))

# -----------------------------
# Follow/Unfollow Routes
# -----------------------------
@app.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow_user(user_id):
    user_to_follow = User.query.get_or_404(user_id)
    existing_follow = Follow.query.filter_by(follower_id=current_user.id, followee_id=user_id).first()
    if not existing_follow:
        follow = Follow(follower_id=current_user.id, followee_id=user_id)
        db.session.add(follow)
        db.session.commit()
        flash(f"You are now following {user_to_follow.username}!", "success")
    else:
        flash(f"You are already following {user_to_follow.username}.", "info")
    return redirect(url_for("dashboard"))


@app.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow_user(user_id):
    follow = Follow.query.filter_by(follower_id=current_user.id, followee_id=user_id).first()
    if follow:
        db.session.delete(follow)
        db.session.commit()
        flash("You have unfollowed the user.", "success")
    else:
        flash("You were not following this user.", "info")
    return redirect(url_for("dashboard"))

# -----------------------------
# Dashboard Route
# -----------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = current_user.id
    tasks = Todo.query.filter_by(user_id=user_id).all()
    followed_users_tasks = Todo.query.join(Follow, Follow.followee_id == Todo.user_id).filter(Follow.follower_id == user_id).all()
    non_followed_users = User.query.filter(User.id != user_id).filter(
        ~User.id.in_(db.session.query(Follow.followee_id).filter(Follow.follower_id == user_id))
    ).all()
    return render_template("dashboard.html",
                           tasks=tasks,
                           followed_users_tasks=followed_users_tasks,
                           non_followed_users=non_followed_users)

# -----------------------------
# About Route
# -----------------------------
@app.route("/about")
def about():
    return render_template("about.html")