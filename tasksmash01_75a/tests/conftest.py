import os
import sys
import pytest

# Insert the project root into sys.path so that run.py can be found.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db

@pytest.fixture
def test_app():
    """
    Creates and configures a new app instance dedicated to testing.
    Although we try to override configurations (like TESTING and SQLALCHEMY_DATABASE_URI),
    note that since the SQLAlchemy instance was bound when the app was created, the
    test database URI may not take effect. Instead, we force a fresh database
    by dropping all tables and recreating them.
    """
    app.config['TESTING'] = True
    # Optionally update; but note this might have no effect if db has been initialized.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.drop_all()
        db.create_all()  # Create an empty version of the database.
        yield app  # Provide the app to tests.
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    """
    Provides a test client to simulate HTTP requests.
    """
    return test_app.test_client()