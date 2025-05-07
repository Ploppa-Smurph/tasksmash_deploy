# app/blueprints/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, login_user, logout_user, current_user
from app.extensions import db, login_manager # Use extensions
from app.models import User
from app.forms import LoginForm, RegisterForm
from app.mail import send_mailgun_email
from flask_login import login_user, current_user, logout_user
import jwt
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# --- Login/Logout/Register ---
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard")) # Redirect to main blueprint's dashboard

    login_form = LoginForm()
    # You might not need register_form here if login page doesn't show registration parts
    # register_form = RegisterForm()

    if login_form.validate_on_submit(): # Use form validation
        user = User.query.filter_by(username=login_form.username.data).first()
        if user and user.check_password(login_form.password.data):
            login_user(user)
            flash("You have been logged in successfully!", "success")
            # Redirect to dashboard after successful login
            next_page = request.args.get('next') # Handle redirect after login
            return redirect(next_page or url_for("main.dashboard")) # Use main.dashboard
        else:
            flash("Invalid username or password.", "error")
    # Pass only the needed form
    return render_template("login.html", login_form=login_form) # Pass form to template

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
         # Redirect logged-in users away from register page
        return redirect(url_for('main.dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        existing_user_by_username = User.query.filter_by(username=form.username.data).first()
        existing_user_by_email = User.query.filter_by(email=form.email.data).first()

        if existing_user_by_username:
             flash("Username already exists.", "error")
        elif existing_user_by_email:
             flash("Email address already registered.", "error")
        else:
            new_user = User(username=form.username.data, email=form.email.data)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            try:
                db.session.commit()
                flash("Account created successfully! Please login.", "success")
                return redirect(url_for("auth.login")) # Redirect to auth blueprint's login
            except Exception as e:
                db.session.rollback()
                flash("An error occurred during registration. Please try again.", "error")
                current_app.logger.error(f"Registration error: {e}") # Log the error

    # If GET request or validation fails
    return render_template("register.html", form=form)


@auth_bp.route("/logout", methods=["POST"]) # POST is safer for logout
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.landing_page")) # Redirect to main blueprint's landing

# --- Password Reset ---
@auth_bp.route("/reset_request", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                token = jwt.encode(
                    {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=1)},
                    current_app.config["SECRET_KEY"],
                    algorithm="HS256"
                )
                # IMPORTANT: url_for needs the blueprint name now!
                reset_url = url_for("auth.reset_password", token=token, _external=True)
                
                # Check Mailgun config before attempting send
                if not all([current_app.config.get("MAILGUN_DOMAIN"), current_app.config.get("MAILGUN_API_KEY"), current_app.config.get("SENDER_EMAIL")]):
                     flash("Email configuration is incomplete. Cannot send reset link.", "error")
                     current_app.logger.error("Mailgun not configured for password reset.")
                else:
                     send_mailgun_email(
                         recipient=email,
                         subject="Password Reset Request - TaskSmash",
                         body=f"Click the link to reset your password: {reset_url}"
                     )
                     flash("Password reset link sent if the email address is registered!", "success")
                return redirect(url_for('auth.login')) # Redirect back to login after request
            except Exception as e:
                 flash("An error occurred. Please try again later.", "error")
                 current_app.logger.error(f"Password reset request error: {e}")
        else:
            # Still flash success-like message to prevent user enumeration
            flash("Password reset link sent if the email address is registered!", "success")
            return redirect(url_for('auth.login'))
    return render_template("resetRequest.html")


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        user_id = payload.get("user_id")
        user = User.query.get_or_404(user_id) # Get user or 404
    except jwt.ExpiredSignatureError:
        flash("The password reset link has expired.", "warning")
        return redirect(url_for("auth.reset_request"))
    except (jwt.InvalidTokenError, jwt.DecodeError):
        flash("Invalid or corrupted password reset link.", "error")
        return redirect(url_for("auth.reset_request"))

    if request.method == "POST":
        new_password = request.form.get("password")
        # Add password validation (e.g., length) here if desired
        if not new_password or len(new_password) < 6:
             flash("Password must be at least 6 characters long.", "error")
             # Re-render the form, don't redirect yet
             return render_template("resetPassword.html", token=token)
        
        user.set_password(new_password)
        try:
            db.session.commit()
            flash("Your password has been reset successfully! Please login.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
             db.session.rollback()
             flash("An error occurred resetting your password. Please try again.", "error")
             current_app.logger.error(f"Password reset error: {e}")

    # If GET request or POST validation failed
    return render_template("resetPassword.html", token=token)