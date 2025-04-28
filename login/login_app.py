from flask import Flask, request, render_template, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secretive_Key"

# SQL Alchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# creation of database object
db = SQLAlchemy(app)

# database model structure - creates a single row for the database
# each user is a row consisting of id, username, password columns
class User(db.Model):
    # class variables (creating columns for each row)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)

    # method to set password
    # takes password variable we created above and hashes the password 
    def set_password(self, password):
        self.password_hash = generate_password_hash(password) 

    # method to check password that is entered    
    # returns boolean value of true / false
    def check_password(self, password):
        # takes 2 arguments, compares password_hash and password
        return check_password_hash(self.password_hash, password)


@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))

    return render_template("index.html")

# login route
@app.route("/login", methods=["POST"])
def login():
    # get username and password from form
    username = request.form.get("username")
    password = request.form.get("password")

    # check if username exists - if user exists then create unique session
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session["username"] = username
        return redirect(url_for("dashboard"))
    # otherwise show index / home page
    else: 
        return render_template("index.html")

# register route
@app.route("/register", methods=["POST"])
def register():
    # get username and password from form
    username = request.form.get("username")
    password = request.form.get("password")
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template("index.html", error="User Currently in Session. Please Check Username.")

    # else - create new user, then add and commit to database
    else: 
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for("dashboard"))

# dashboard route
@app.route("/dashboard")
def dashboard():
    if "username" in session:
        return render_template("dashboard.html", user={"username": session["username"]})
    return redirect(url_for("home"))

# logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))

# run the app & create the initial database / update upon refresh
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)