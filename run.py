# run.py (in your project root)
from app import create_app # Import the factory
# from app.extensions import db # Import db from extensions if you need to run db.create_all()

app = create_app()

if __name__ == '__main__':
    # For local development WITHOUT migrations, do:
    # with app.app_context():
    # from app.extensions import db # Import db here if not globally
    # db.create_all()
    # print("Local database tables created (if they didn't exist).")
    
    # It's better to use migrations locally too for consistency:
    # 1. flask db migrate -m "some change"
    # 2. flask db upgrade
    
    app.run(debug=True)