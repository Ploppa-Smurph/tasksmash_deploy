# app/blueprints/todo.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Todo, Comment # Ensure Comment is imported
from app.utils.achievements import evaluate_achievements # Removed award_achievement as it's handled within evaluate
from app.forms import EditTaskForm

# Define the blueprint
todo_bp = Blueprint('todo', __name__, url_prefix='/todo')

# --- ToDo Routes ---

@todo_bp.route("/add", methods=["POST"])
@login_required
def add_todo():
    """Adds a new task for the current user."""
    content = request.form.get("content")
    if not content or len(content) > 200: # Basic validation
        flash("Task content is required and must be max 200 characters.", "error")
        return redirect(url_for("main.dashboard")) # Redirect to main dashboard

    new_todo = Todo(content=content, user_id=current_user.id)
    db.session.add(new_todo)
    try:
        db.session.commit()
        flash("Task added!", "success")
        # Evaluate achievements after successful commit
        evaluate_achievements(current_user)
    except Exception as e:
        db.session.rollback()
        flash("Error adding task.", "error")
        current_app.logger.error(f"Add task error: {e}")

    return redirect(url_for("main.dashboard"))

@todo_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_todo(id):
    """Edits an existing task owned by the current user."""
    # Get the task or return 404, ensuring the current user owns it
    task = Todo.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    form = EditTaskForm(obj=task) # Pre-populate form with task data
    if form.validate_on_submit():
        task.content = form.content.data
        task.edit_count += 1
        try:
            db.session.commit() # Commit changes first
            flash("Task updated!", "success")
            # Evaluate achievements after successful commit
            evaluate_achievements(current_user)
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash("Error updating task.", "error")
            current_app.logger.error(f"Edit task error: {e}")

    # Render the edit form on GET request or if validation fails
    return render_template("edit.html", task=task, form=form)

@todo_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_todo(id):
    """Deletes a task owned by the current user."""
    task = Todo.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    try:
        # Cascade delete should handle related comments based on model relationship settings
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted.", "success")
        # Optionally, re-evaluate achievements if deleting affects completion stats
        # evaluate_achievements(current_user)
    except Exception as e:
        db.session.rollback()
        flash("Error deleting task.", "error")
        current_app.logger.error(f"Delete task error: {e}")

    return redirect(url_for("main.dashboard"))

@todo_bp.route('/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    """Marks a task owned by the current user as complete."""
    task = Todo.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    if task.completed:
        flash("Task already marked as complete.", "info")
    else:
        task.completed = True
        try:
            db.session.commit() # Commit completion first
            flash("Task marked as complete!", "success")
            # Evaluate achievements after successful commit
            evaluate_achievements(current_user)
        except Exception as e:
            db.session.rollback()
            flash("Error completing task.", "error")
            current_app.logger.error(f"Complete task error: {e}")

    return redirect(url_for('main.dashboard'))


@todo_bp.route("/view/<int:task_id>")
@login_required
def view_task(task_id):
    """Displays the details page for a single task."""
    # Eager load necessary relationships for the template, excluding dynamic 'replies'
    task = Todo.query.options(
                db.joinedload(Todo.user),                           # Eager load the task's author
                db.joinedload(Todo.comments).joinedload(Comment.user) # Eager load comments and their authors
            ).get_or_404(task_id)

    # Add permission checks here if needed (e.g., only owner or followers can view?)
    # if task.user_id != current_user.id and not current_user_is_following(task.user_id):
    #     abort(403) # Example permission check

    # Get top-level comments and sort them (replies will be loaded dynamically in template)
    top_level_comments = sorted(
        [c for c in task.comments if c.parent_id is None],
        key=lambda x: x.created_at # Sort by creation time
    )

    # Note: The template will need to handle iterating through comment.replies,
    # which will trigger additional queries due to lazy='dynamic'.
    return render_template("task.html", task=task, comments=top_level_comments)

