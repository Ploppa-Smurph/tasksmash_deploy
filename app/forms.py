# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField # Added TextAreaField, BooleanField
from wtforms.fields import DateField # For Date input
from wtforms.validators import DataRequired, Email, Length, Optional, URL # Added URL validator

class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    """Form for user registration."""
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class AddTaskForm(FlaskForm):
    """Form for adding a new task."""
    content = TextAreaField('Task Content', validators=[DataRequired(), Length(max=200)])
    due_date = DateField('Due Date (Optional)', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Add Task')

class EditTaskForm(FlaskForm):
    """Form for editing an existing task."""
    content = TextAreaField('Task Content', validators=[DataRequired(), Length(max=200)])
    due_date = DateField('Due Date (Optional)', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Update Task')

# <<< --- NEW FORM --- >>>
class EditProfileForm(FlaskForm):
    """Form for users to edit their profile information."""
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    bio = TextAreaField('Bio (Optional)', validators=[Optional(), Length(max=250)])
    avatar_url = StringField('Avatar URL (Optional)', validators=[Optional(), URL(), Length(max=200)])
    profile_is_public = BooleanField('Make Profile Publicly Visible', default=True)
    submit = SubmitField('Update Profile')
# <<< --- END NEW FORM --- >>>
