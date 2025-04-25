# app/api.py
from flask import jsonify
from app import app  # Import the app instance from app/__init__.py
from app.models import Achievement

@app.route('/api/achievements', methods=['GET'])
def api_achievements():
    """
    Returns a JSON list of all achievements.
    """
    achievements = Achievement.query.all()
    data = [
        {"id": ach.id, "name": ach.name, "description": ach.description}
        for ach in achievements
    ]
    return jsonify(data)