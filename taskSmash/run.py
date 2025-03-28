from app import app, db

if __name__ == '__main__':
    # Initialize the database 
    with app.app_context():
         db.drop_all()  # Drop all tables (for development purposes only)
         db.create_all()  
    app.run(debug=True)