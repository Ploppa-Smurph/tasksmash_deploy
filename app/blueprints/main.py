# app/blueprints/main.py
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, abort
from app.extensions import db
from app.models import User, Todo, Comment, Follow, Achievement, UserAchievement # Ensure all needed models are imported
from flask_login import login_required, current_user
from app.utils.achievements import evaluate_achievements
from app.forms import EditProfileForm # Import the new form

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def landing_page():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    user_id = current_user.id
    tasks = Todo.query.filter_by(user_id=user_id).order_by(Todo.created_at.desc()).all()
    followed_users_tasks = Todo.query.join(Follow, Follow.followee_id == Todo.user_id)\
                                     .filter(Follow.follower_id == user_id)\
                                     .options(db.joinedload(Todo.user), db.joinedload(Todo.comments).joinedload(Comment.user))\
                                     .order_by(Todo.created_at.desc())\
                                     .all()
    following_ids_subquery = db.session.query(Follow.followee_id).filter(Follow.follower_id == user_id).subquery()
    non_followed_users = User.query.filter(User.id != user_id)\
                                   .filter(User.id.notin_(following_ids_subquery))\
                                   .order_by(User.username)\
                                   .all()
    user_achievements_assoc = UserAchievement.query.filter_by(user_id=user_id)\
                                            .options(db.joinedload(UserAchievement.achievement))\
                                            .all()
    achievements_list = [ua.achievement for ua in user_achievements_assoc]
    all_tasks = Todo.query.options(db.joinedload(Todo.user), db.joinedload(Todo.comments).joinedload(Comment.user))\
                        .order_by(Todo.created_at.desc())\
                        .limit(50)\
                        .all()

    return render_template("dashboard.html",
                           tasks=tasks,
                           followed_users_tasks=followed_users_tasks,
                           non_followed_users=non_followed_users,
                           achievements=achievements_list,
                           all_tasks=all_tasks)

# --- Follow/Unfollow ---
@main_bp.route("/follow/<username>", methods=["POST"]) # Changed to username for consistency
@login_required
def follow_user(username):
    user_to_follow = User.query.filter_by(username=username).first_or_404()
    if user_to_follow == current_user:
        flash("You cannot follow yourself.", "warning")
        return redirect(request.referrer or url_for('main.dashboard'))

    if current_user.is_following(user_to_follow):
        flash(f"You are already following {user_to_follow.username}.", "info")
    else:
        current_user.follow(user_to_follow)
        try:
            db.session.commit()
            flash(f"You are now following {user_to_follow.username}!", "success")
            evaluate_achievements(current_user) # Evaluate after successful commit
        except Exception as e:
            db.session.rollback()
            flash("Could not follow user.", "error")
            current_app.logger.error(f"Follow error: {e}")
    return redirect(request.referrer or url_for('main.view_user_profile', username=username))

@main_bp.route("/unfollow/<username>", methods=['POST'])
@login_required
def unfollow_user(username):
    user_to_unfollow = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user_to_unfollow):
        current_user.unfollow(user_to_unfollow)
        try:
            db.session.commit()
            flash(f"You have unfollowed {user_to_unfollow.username}.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Could not unfollow user.", "error")
            current_app.logger.error(f"Unfollow error: {e}")
    else:
        flash(f"You were not following {user_to_unfollow.username}.", "info")
    return redirect(request.referrer or url_for('main.view_user_profile', username=username))


# --- Static Pages ---
@main_bp.route("/about")
def about():
    return render_template("about.html")

# --- App-wide Request Handler (defined in __init__.py and registered there) ---
# def add_no_cache_headers(response):
#     response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
#     response.headers["Pragma"] = "no-cache"
#     response.headers["Expires"] = "0"
#     return response


# <<< --- NEW PROFILE ROUTES --- >>>
@main_bp.route('/profile/<username>')
@login_required # Or remove if profiles can be viewed by non-logged-in users
def view_user_profile(username):
    """Displays a user's profile page."""
    user = User.query.filter_by(username=username).first_or_404()

    if not user.profile_is_public and user != current_user:
        # Optionally, allow admins to see private profiles
        # if not current_user.is_admin(): # Assuming you add an is_admin property/role
        flash("This user's profile is private.", "info")
        return redirect(url_for('main.dashboard')) # Or a generic "user not found" page

    # Fetch tasks for the profile (respecting task-level privacy if implemented)
    # Using the get_public_todos() method from the User model
    profile_tasks = user.get_public_todos().limit(20).all() # Added limit

    # Fetch achievements for the profile user
    user_achievements_assoc = UserAchievement.query.filter_by(user_id=user.id)\
                                            .options(db.joinedload(UserAchievement.achievement))\
                                            .all()
    profile_achievements = [ua.achievement for ua in user_achievements_assoc]

    return render_template('profile.html', 
                           profile_user=user, 
                           tasks=profile_tasks,
                           achievements=profile_achievements)

@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Allows the current user to edit their profile."""
    form = EditProfileForm(obj=current_user) # Pre-populate with current user's data

    if form.validate_on_submit():
        # Check if username or email is being changed and if it's unique
        new_username = form.username.data
        new_email = form.email.data

        username_taken = User.query.filter(User.username == new_username, User.id != current_user.id).first()
        email_taken = User.query.filter(User.email == new_email, User.id != current_user.id).first()

        if username_taken:
            flash('That username is already taken. Please choose a different one.', 'error')
        elif email_taken:
            flash('That email address is already registered. Please choose a different one.', 'error')
        else:
            current_user.username = new_username
            current_user.email = new_email
            current_user.bio = form.bio.data
            current_user.avatar_url = form.avatar_url.data
            current_user.profile_is_public = form.profile_is_public.data
            try:
                db.session.commit()
                flash('Your profile has been updated successfully!', 'success')
                return redirect(url_for('main.view_user_profile', username=current_user.username))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating your profile. Please try again.', 'error')
                current_app.logger.error(f"Edit profile error: {e}")
    
    elif request.method == 'POST': # If form validation failed
        flash('Please correct the errors below.', 'error')

    return render_template('edit_profile.html', form=form, title="Edit Your Profile")
# <<< --- END NEW PROFILE ROUTES --- >>>
