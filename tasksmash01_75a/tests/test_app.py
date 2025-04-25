import json
from app.models import Achievement
from run import db

def seed_database():
    """
    Mimics the database seeding logic.
    Adds a list of Achievement records to the database if they don't already exist.
    """
    achievements = [
        {"name": "Task Initiator", "description": "Created 10 tasks"},
        {"name": "Goal Crusher", "description": "Completed 5 tasks"},
        {"name": "Comment Commander", "description": "Posted your first comment"},
        {"name": "Task Master", "description": "Created 50 tasks"},
        {"name": "Finisher", "description": "Completed 25 tasks"},
        {"name": "Perfectionist", "description": "Completed all your tasks"},
        {"name": "Chatterbox", "description": "Left 10 comments"},
        {"name": "Reply Ruler", "description": "Left 5 replies"},
        {"name": "Friendly Follower", "description": "Followed 1 user"},
        {"name": "Social Butterfly", "description": "Followed 5 users"},
        {"name": "Popular Pick", "description": "A task of yours got 5 comments"},
        {"name": "Empty Inbox", "description": "You have no incomplete tasks"},
        {"name": "Procrastinator", "description": "You edited the same task 3 times"}
    ]
    
    for ach in achievements:
        if not Achievement.query.filter_by(name=ach["name"]).first():
            new_achievement = Achievement(name=ach["name"], description=ach["description"])
            db.session.add(new_achievement)
    db.session.commit()

def test_database_seeding(test_app):
    """
    Verifies that the database seeding works as expected.
    Steps:
      1. Clear the database.
      2. Confirm the Achievements table is empty.
      3. Run seed_database() and verify exactly 13 achievements exist.
    """
    with test_app.app_context():
        db.drop_all()
        db.create_all()
        initial_count = Achievement.query.count()
        assert initial_count == 0, "Database should be empty before seeding."
        
        seed_database()
        
        seeded_count = Achievement.query.count()
        assert seeded_count == 13, f"Expected 13 achievements, found {seeded_count}."

def test_index_route(client):
    """
    Tests the home (index) route:
      1. Performs a GET request to '/'.
      2. Confirms a 200 OK status code.
      3. Checks for a key substring in the response.
      
    NOTE: The original test expected "Welcome" but your rendered page does not have it.
          For example, your h1 says "TaskSmash". Adjust the substring accordingly.
    """
    response = client.get('/')
    assert response.status_code == 200, "Index route did not return 200 OK."
    
    # Check for a substring that actually appears—here we look for "TaskSmash".
    assert b"TaskSmash" in response.data, "Expected 'TaskSmash' not found in index page."

def test_achievements_api(client):
    """
    Tests the /api/achievements endpoint:
      1. Reinitialize the database and seed achievements.
      2. Sends a GET request to '/api/achievements'.
      3. Verifies a 200 OK status and that the JSON response is a list of at least 13 items.
    
    Make sure that your app/api.py registers this endpoint.
    """
    with client.application.app_context():
        db.drop_all()
        db.create_all()
        seed_database()
    
    response = client.get('/api/achievements')
    assert response.status_code == 200, "API endpoint /api/achievements did not return 200 OK."
    
    data = response.get_json()
    assert isinstance(data, list), "API response is not a JSON list."
    assert len(data) >= 13, "API response does not contain the expected number of achievements."

def test_config_values(test_app):
    """
    Checks specific configuration parameters:
      1. Ensures that SECRET_KEY is set.
      2. Verifies that the test configuration sets SQLALCHEMY_DATABASE_URI to an in-memory database.
      
    NOTE: If your app was created using a production config then the in-memory override may not take effect.
    """
    secret_key = test_app.config.get("SECRET_KEY")
    assert secret_key is not None, "SECRET_KEY configuration is missing."
    
    db_uri = test_app.config.get("SQLALCHEMY_DATABASE_URI")
    assert "sqlite:///:memory:" in db_uri, "SQLALCHEMY_DATABASE_URI should be using the in-memory database for testing."