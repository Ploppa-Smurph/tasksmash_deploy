# app/blueprints/main.py
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from app.extensions import db
from app.models import User, Todo, Comment, Follow, Achievement, UserAchievement
from flask_login import login_required, current_user
from app.utils.achievements import evaluate_achievements # Import from utils

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def landing_page():
    # If user is logged in, maybe redirect to dashboard?
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    user_id = current_user.id

    # User's own tasks
    tasks = Todo.query.filter_by(user_id=user_id).order_by(Todo.created_at.desc()).all()

    # Tasks from users the current user follows
    # Eager load user details to avoid N+1 queries in template
    followed_users_tasks = Todo.query.join(Follow, Follow.followee_id == Todo.user_id)\
                                     .filter(Follow.follower_id == user_id)\
                                     .options(db.joinedload(Todo.user), db.joinedload(Todo.comments).joinedload(Comment.user))\
                                     .order_by(Todo.created_at.desc())\
                                     .all()

    # Users the current user *is not* following (excluding self)
    following_ids_subquery = db.session.query(Follow.followee_id).filter(Follow.follower_id == user_id).subquery()
    non_followed_users = User.query.filter(User.id != user_id)\
                                   .filter(User.id.notin_(following_ids_subquery))\
                                   .order_by(User.username)\
                                   .all()

    # User's achievements
    user_achievements = UserAchievement.query.filter_by(user_id=user_id)\
                                            .options(db.joinedload(UserAchievement.achievement))\
                                            .all()
    # Extract just the Achievement objects for simpler template logic
    achievements_list = [ua.achievement for ua in user_achievements]

    # All tasks (consider pagination if this list gets large)
    # Eager load necessary relationships
    all_tasks = Todo.query.options(db.joinedload(Todo.user), db.joinedload(Todo.comments).joinedload(Comment.user))\
                        .order_by(Todo.created_at.desc())\
                        .limit(50)\
                        .all() # Added limit for performance

    return render_template("dashboard.html",
                           tasks=tasks,
                           followed_users_tasks=followed_users_tasks,
                           non_followed_users=non_followed_users,
                           achievements=achievements_list, # Pass the extracted list
                           all_tasks=all_tasks)

# --- Follow/Unfollow ---
@main_bp.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow_user(user_id):
    if user_id == current_user.id:
        flash("You cannot follow yourself.", "warning")
        return redirect(url_for('main.dashboard'))

    user_to_follow = User.query.get_or_404(user_id)
    existing_follow = Follow.query.filter_by(follower_id=current_user.id, followee_id=user_id).first()

    if not existing_follow:
        follow = Follow(follower_id=current_user.id, followee_id=user_id)
        db.session.add(follow)
        try:
            db.session.commit()
            flash(f"You are now following {user_to_follow.username}!", "success")
            evaluate_achievements(current_user) # Evaluate after successful commit
            db.session.commit() # Commit again if evaluate_achievements added UserAchievements
        except Exception as e:
            db.session.rollback()
            flash("Could not follow user.", "error")
            current_app.logger.error(f"Follow error: {e}")
    else:
        flash(f"You are already following {user_to_follow.username}.", "info")

    # Redirect back to dashboard or perhaps the user's profile page if you add one
    return redirect(url_for("main.dashboard"))

@main_bp.route("/unfollow/<int:user_id>", methods=['POST']) # Use POST for actions that change state
@login_required
def unfollow_user(user_id):
    follow = Follow.query.filter_by(follower_id=current_user.id, followee_id=user_id).first()
    if follow:
        db.session.delete(follow)
        try:
            db.session.commit()
            flash("You have unfollowed the user.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Could not unfollow user.", "error")
            current_app.logger.error(f"Unfollow error: {e}")
    else:
        flash("You were not following this user.", "info")

    return redirect(url_for("main.dashboard"))

# --- Static Pages ---
@main_bp.route("/about")
def about():
    return render_template("about.html")

# --- App-wide Request Handler ---
# Note: @app.after_request needs to be attached to the app instance in create_app
# You can define the function here and import/register it in create_app if preferred
# Or define it directly in create_app
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response