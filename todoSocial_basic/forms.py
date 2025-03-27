from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=4, max=50)]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    submit = SubmitField('Login')

from wtforms import EmailField  # Add EmailField to your imports

class RegisterForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=4, max=50)]
    )
    email = EmailField(  # Include the email field with proper validation
        'Email',
        validators=[DataRequired()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)]
    )
    submit = SubmitField('Register')

class EditTaskForm(FlaskForm):
    content = StringField(
        'Task Content',
        validators=[DataRequired(), Length(min=1, max=200, message="Task must be between 1 and 200 characters.")]
    )
    submit = SubmitField('Update Task')