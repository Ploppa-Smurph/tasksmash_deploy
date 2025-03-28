from flask import render_template, request, redirect, url_for, flash, session, current_app
from app import app, db
from app.models import User, Todo, Comment
from app.mail import send_mailgun_email
import jwt
from datetime import datetime, timedelta
from app.forms import LoginForm, RegisterForm, EditTaskForm  # if you have these defined

# Home route
@app.route("/")
def landing_page():
    return render_template("home.html")

# Index route
@app.route("/index", methods=["GET", "POST"])
def home():
    login_form = LoginForm()
    register_form = RegisterForm()
    return render_template("index.html", login_form=login_form, register_form=register_form)

# Login route
# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()  # Add this to define the login form
    register_form = RegisterForm()  # Add this to define the register form
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Attempt to find the user by username
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session["username"] = username
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")
            # Pass the flag and the forms to the template
            return render_template("index.html", login_form=login_form, register_form=register_form, show_create_account=True)
    
    # Pass forms when rendering the template without POST
    return render_template("index.html", login_form=login_form, register_form=register_form, show_create_account=False)


# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Handle registration
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        existing_user_by_username = User.query.filter_by(username=username).first()
        existing_user_by_email = User.query.filter_by(email=email).first()
        
        if existing_user_by_username or existing_user_by_email:
            flash("Username or email already exists.", "error")
            return render_template("register.html", form=form)
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created successfully!", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html", form=form)


# Logout route
@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("user_id", None)
    return redirect(url_for("home"))

# Password reset request route
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


# Password reset route
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
        return redirect(url_for("home"))
    return render_template("resetPassword.html", token=token)

# Dashboard route to show user's tasks
@app.route("/dashboard")
def dashboard():
    if "username" in session:
        user_id = session["user_id"]
        tasks = Todo.query.filter_by(user_id=user_id).all()
        return render_template("dashboard.html", tasks=tasks)
    return redirect(url_for("home"))

# Route to add a new to-do
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

# Route to edit an existing to-do
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_todo(id):
    if "username" in session:
        task = Todo.query.get_or_404(id)
        if task.user_id == session["user_id"]:
            form = EditTaskForm(obj=task)
            if form.validate_on_submit():
                task.content = form.content.data
                db.session.commit()
                return redirect(url_for("dashboard"))
            return render_template("edit.html", task=task, form=form)
    return redirect(url_for("home"))

# Route to delete a to-do
@app.route("/delete/<int:id>")
def delete_todo(id):
    if "username" in session:
        todo = Todo.query.get_or_404(id)
        if todo.user_id == session["user_id"]:
            db.session.delete(todo)
            db.session.commit()
        return redirect(url_for("dashboard"))
    return redirect(url_for("home"))

# Route to add a comment to a task
@app.route("/comment/<int:task_id>", methods=["POST"])
def add_comment(task_id):
    if "username" in session:
        content = request.form.get("comment")
        user_id = session["user_id"]
        new_comment = Comment(content=content, task_id=task_id, user_id=user_id)
        db.session.add(new_comment)
        db.session.commit()
    return redirect(url_for("dashboard"))

# Route to view a task and its comments
@app.route("/task/<int:task_id>")
def view_task(task_id):
    if "username" in session:
        task = Todo.query.get_or_404(task_id)
        comments = Comment.query.filter_by(task_id=task_id).all()
        return render_template("task.html", task=task, comments=comments)
    return redirect(url_for("home"))