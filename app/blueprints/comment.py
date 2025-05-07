# app/blueprints/comment.py
from flask import Blueprint, request, redirect, url_for, flash, current_app
from app.extensions import db
from app.models import Comment, Todo # Import necessary models
from flask_login import login_required, current_user
from app.utils.achievements import evaluate_achievements # Import from utils

comment_bp = Blueprint('comment', __name__, url_prefix='/comment') # Optional prefix

# Route for adding a comment (perhaps from the task page or dashboard)
# Note: Original routes had /comment/<task_id> and /comment/task/<task_id>
# Let's consolidate to one endpoint for adding comments to a task
@comment_bp.route("/add/<int:task_id>", methods=["POST"])
@login_required
def add_comment(task_id):
    task = Todo.query.get_or_404(task_id) # Ensure task exists
    content = request.form.get("content") # Check form name used in template ('content' or 'comment'?)

    if not content:
        flash("Comment cannot be empty.", "error")
        # Redirect back to where the comment was made, maybe the task view?
        # Or just dashboard if form was only there. Requires knowing the source.
        return redirect(request.referrer or url_for("main.dashboard"))

    new_comment = Comment(content=content, task_id=task_id, user_id=current_user.id)
    db.session.add(new_comment)
    try:
        db.session.commit()
        flash("Comment added!", "success")
        evaluate_achievements(current_user) # Check achievements after commit
        db.session.commit() # Commit again if achievement added
    except Exception as e:
        db.session.rollback()
        flash("Error adding comment.", "error")
        current_app.logger.error(f"Add comment error: {e}")

    # Redirect intelligently - back to task view page if possible
    return redirect(url_for("todo.view_task", task_id=task_id))

@comment_bp.route("/reply/<int:comment_id>", methods=["POST"])
@login_required
def add_comment_reply(comment_id):
    parent_comment = Comment.query.get_or_404(comment_id)
    reply_content = request.form.get("reply") # Check form name

    if not reply_content:
        flash("Reply cannot be empty.", "error")
        return redirect(request.referrer or url_for("main.dashboard"))

    reply = Comment(
        content=reply_content,
        user_id=current_user.id,
        task_id=parent_comment.task_id,
        parent_id=parent_comment.id
    )
    db.session.add(reply)
    try:
        db.session.commit()
        flash("Your reply has been added.", "success")
        evaluate_achievements(current_user) # Check achievements
        db.session.commit() # Commit again if needed
    except Exception as e:
        db.session.rollback()
        flash("Error adding reply.", "error")
        current_app.logger.error(f"Add reply error: {e}")

    # Redirect back to the task page where the comment was made
    return redirect(url_for("todo.view_task", task_id=parent_comment.task_id))

# Note: The route GET /task/<task_id> was moved to the todo blueprint as it shows task details.
# The route POST /comment/task/<task_id> was consolidated into POST /comment/add/<task_id>