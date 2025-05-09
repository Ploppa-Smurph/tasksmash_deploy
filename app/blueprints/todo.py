# app/blueprints/todo.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Todo, Comment # Ensure Comment is imported
from app.utils.achievements import evaluate_achievements
# Updated form imports: AddTaskForm is new, EditTaskForm was already there
from app.forms import AddTaskForm, EditTaskForm

# Define the blueprint
todo_bp = Blueprint('todo', __name__, url_prefix='/todo')

# --- ToDo Routes ---

@todo_bp.route("/add", methods=["GET", "POST"]) # Changed to allow GET for displaying form if needed elsewhere
@login_required
def add_todo():
    """Adds a new task for the current user using AddTaskForm."""
    # Note: This route now primarily handles the POST from AddTaskForm.
    # The form itself would typically be rendered on another page (e.g., dashboard).
    # If you want this route to also render the form on GET, you'd add:
    # if request.method == 'GET':
    #     form = AddTaskForm()
    #     return render_template('add_task_page.html', form=form) # Example template

    form = AddTaskForm() # Instantiate the form

    if form.validate_on_submit(): # Process form data on POST
        content = form.content.data
        due_date = form.due_date.data # This will be a Python date object or None

        new_todo = Todo(
            content=content,
            user_id=current_user.id,
            due_date=due_date # Assign the due_date
        )
        db.session.add(new_todo)
        try:
            db.session.commit()
            flash("Task added!", "success")
            evaluate_achievements(current_user)
        except Exception as e:
            db.session.rollback()
            flash("Error adding task.", "error")
            current_app.logger.error(f"Add task error: {e}")
        return redirect(url_for("main.dashboard"))
    
    # If form validation fails on POST, or if it were a GET request to a dedicated add task page
    # It's common to redirect back to the dashboard where the form might be,
    # or render a specific 'add_task.html' template with form errors.
    # For now, if validation fails, we'll flash errors and redirect to dashboard.
    # WTForms automatically flashes errors if your template is set up to display them.
    if form.errors:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                flash(f"Error in {getattr(form, fieldName).label.text}: {err}", "error")
    return redirect(url_for("main.dashboard"))


@todo_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_todo(id):
    """Edits an existing task owned by the current user."""
    task = Todo.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    # Pass task's current due_date to the form if it exists, WTForms handles None correctly
    form = EditTaskForm(obj=task)

    if form.validate_on_submit():
        task.content = form.content.data
        task.due_date = form.due_date.data # Get due_date from the form
        task.edit_count += 1
        try:
            db.session.commit()
            flash("Task updated!", "success")
            evaluate_achievements(current_user)
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash("Error updating task.", "error")
            current_app.logger.error(f"Edit task error: {e}")
            
    return render_template("edit.html", task=task, form=form)


@todo_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_todo(id):
    """Deletes a task owned by the current user."""
    task = Todo.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    try:
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted.", "success")
        # evaluate_achievements(current_user) # Consider if deleting tasks affects achievements
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
            db.session.commit()
            flash("Task marked as complete!", "success")
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
    task = Todo.query.options(
                db.joinedload(Todo.user),
                db.joinedload(Todo.comments).joinedload(Comment.user)
            ).get_or_404(task_id)

    top_level_comments = sorted(
        [c for c in task.comments if c.parent_id is None],
        key=lambda x: x.created_at
    )
    return render_template("task.html", task=task, comments=top_level_comments)
