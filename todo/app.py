# imports
from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# toDo App
app = Flask(__name__)

# create and drop in database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo_db.db"
db = SQLAlchemy(app)

# create database model
class ToDo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    complete = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)

# return task to database
    def __repr__(self):
        return f"<Task {self.id}>"

# decorator for 'route' to web pages
# Home page of app -- methods for GET & POST
@app.route("/", methods=["GET", "POST"])
def index():

    # add a task 
    if request.method == "POST":
        task_content = request.form["content"]
        new_task = ToDo(content=task_content)
        try: 
            db.session.add(new_task)
            db.session.commit()
            return redirect("/")
        except Exception as e:
            print(f"ERROR: {e}")
            return f"ERROR: {e}"

    # see current tasks
    else: 
        tasks = ToDo.query.order_by(ToDo.created).all()
        return render_template("index.html", tasks=tasks)

# delete task
@app.route("/delete/<int:id>")
def delete(id:int):
    delete_task = ToDo.query.get_or_404(id)
    try: 
        db.session.delete(delete_task)
        db.session.commit()
        return redirect("/")
    except Exception as e:
        return f"ERROR: {e}"
    
# edit task
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id:int):
    task = ToDo.query.get_or_404(id)
    if request.method == "POST":
        task.content = request.form["content"]
        try:
            db.session.commit()
            return redirect("/")
        except Exception as e:
            return f"ERROR: {e}"
    else:
        return render_template("edit.html", task=task)

# run app & turn on debug mode
if __name__ == "__main__":
    
# context manager / context management
    with app.app_context():
        db.create_all()
    app.run(debug=True)