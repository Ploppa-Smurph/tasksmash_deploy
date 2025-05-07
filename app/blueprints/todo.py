# app/blueprints/todo.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from app.extensions import db
from app.models import User, Todo # Import necessary models
from flask_login import login_required, current_user
from app.utils.achievements import evaluate_achievements, award_achievement # Import from utils
from app.forms import EditTaskForm # Import relevant form

todo_bp = Blueprint('todo', __name__, url_prefix='/todo') # Optional url prefix

@todo_bp.route("/add", methods=["POST"]) # Matches original route, maybe change prefix later
@login_required
def add_todo():
    content = request.form.get("content")
    if not content or len(content) > 200: # Basic validation
        flash("Task content is required and must be max 200 characters.", "error")
        return redirect(url_for("main.dashboard")) # Redirect to main dashboard

    new_todo = Todo(content=content, user_id=current_user.id)
    db.session.add(new_todo)
    try:
        db.session.commit()
        flash("Task added!", "success")
        evaluate_achievements(current_user) # Evaluate after commit
        db.session.commit() # Commit again if achievements were added
    except Exception as e:
        db.session.rollback()
        flash("Error adding task.", "error")
        current_app.logger.error(f"Add task error: {e}")

    return redirect(url_for("main.dashboard"))

@todo_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_todo(id):
    # Consider using first_or_404 for cleaner not found handling
    task = Todo.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    # The above query ensures user owns the task

    form = EditTaskForm(obj=task) # Pre-populate form
    if form.validate_on_submit():
        task.content = form.content.data
        task.edit_count += 1
        try:
            db.session.commit()
            flash("Task updated!", "success")
            # Check achievement after successful commit
            if task.edit_count >= 3:
                 evaluate_achievements(current_user) # Let evaluate handle the specific check
                 db.session.commit() # Commit again if achievement added
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash("Error updating task.", "error")
            current_app.logger.error(f"Edit task error: {e}")
            
    # If GET or validation failed
    return render_template("edit.html", task=task, form=form)

@todo_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_todo(id):
    task = Todo.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    # Query ensures user owns the task

    try:
        # Need to handle related comments if necessary, cascade should handle it based on model setup
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting task.", "error")
        current_app.logger.error(f"Delete task error: {e}")

    return redirect(url_for("main.dashboard"))

@todo_bp.route('/complete/<int:task_id>', methods=['POST']) # Renamed for clarity
@login_required
def complete_task(task_id):
    task = Todo.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    # Query ensures user owns the task

    if task.completed:
        flash("Task already marked as complete.", "info")
    else:
        task.completed = True
        try:
            db.session.commit()
            flash("Task marked as complete!", "success")
            evaluate_achievements(current_user) # Check achievements after commit
            db.session.commit() # Commit again if achievement added
        except Exception as e:
            db.session.rollback()
            flash("Error completing task.", "error")
            current_app.logger.error(f"Complete task error: {e}")

    return redirect(url_for('main.dashboard'))

# Route to view a single task might fit better here than in comments blueprint
@todo_bp.route("/view/<int:task_id>")
@login_required
def view_task(task_id):
    task = Todo.query.options(db.joinedload(Todo.user),
                              db.joinedload(Todo.comments).joinedload(Comment.user),
                              db.joinedload(Todo.comments).joinedload(Comment.replies))\
                     .get_or_404(task_id)
                     
    # Basic permission check (can current user view this task?)
    # Example: Only owner or follower can view? Or all logged-in users?
    # Add more sophisticated checks if needed. Here, we just require login.

    # Prepare comments/replies in a structured way if needed for the template
    # Or handle nesting directly in the template.
    top_level_comments = [c for c in task.comments if c.parent_id is None]

    return render_template("task.html", task=task, comments=top_level_comments) # Pass only top-level comments maybe?