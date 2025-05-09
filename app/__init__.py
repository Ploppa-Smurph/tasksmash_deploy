# app/__init__.py
import os
from flask import Flask
from config import Config # Assumes config.py is in root
from .extensions import db, login_manager, migrate # Import from extensions
from datetime import datetime # <<<--- ADDED IMPORT

# It's generally cleaner to define blueprint instances in their respective files (e.g., app/blueprints/main.py)
# and import the instances here, rather than importing the entire routes module if it gets large.


def create_app(config_class=Config):
    """Application Factory Function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db) # Initialize Flask-Migrate

    # Configure Flask-Login
    # IMPORTANT: Update 'main.login' if your login route ends up in a different blueprint (e.g., 'auth.login')
    login_manager.login_view = 'auth.login' # Assuming you'll create an 'auth' blueprint for login/register
    login_manager.login_message_category = 'info'
    login_manager.login_message = u"Please log in to access this page." # Optional: Custom message

    @login_manager.user_loader
    def load_user(user_id):
        """Flask-Login user loader callback."""
        from .models import User # Import here to avoid potential circular imports at module level
        # Use .get() for primary key lookup, handles None if ID invalid before int conversion
        return db.session.get(User, int(user_id)) # Updated to use db.session.get (SQLAlchemy 2.x)

    # Register Blueprints
    # You will need to create these blueprint files (e.g., app/blueprints/main.py, app/blueprints/auth.py)
    # and define the blueprint instances (e.g., main_bp, auth_bp) within them.
    # Use try-except blocks to handle cases where blueprints might not exist yet during refactoring.
    try:
        from .blueprints.main import main_bp
        app.register_blueprint(main_bp)
    except ImportError:
        app.logger.warning("Main blueprint not found or could not be imported.")

    try:
        from .blueprints.auth import auth_bp
        app.register_blueprint(auth_bp) # Assuming auth routes are at /auth based on login_view
    except ImportError:
        app.logger.warning("Auth blueprint not found or could not be imported.")

    try:
        from .blueprints.todo import todo_bp
        app.register_blueprint(todo_bp, url_prefix='/todo') # Add prefix if desired
    except ImportError:
        app.logger.warning("Todo blueprint not found or could not be imported.")

    try:
        from .blueprints.comment import comment_bp
        app.register_blueprint(comment_bp, url_prefix='/comment') # Add prefix if desired
    except ImportError:
        app.logger.warning("Comment blueprint not found or could not be imported.")


    # --- Register app-wide request handlers ---
    @app.after_request
    def add_no_cache_headers(response):
        """Add headers to prevent caching."""
        # This function was previously in routes.py. Registering it here.
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # --- CLI Commands ---
    # Define the internal logic
    def seed_achievements_command_internal():
        """Internal logic for seeding achievements."""
        # Import models needed only within this function scope
        from .models import Achievement, achievements as achievements_to_seed
        from sqlalchemy.exc import SQLAlchemyError # Import specific exception

        try:
            existing_achievement_names = {ach.name for ach in Achievement.query.all()}
            new_achievements_added = 0
            achievements_updated = 0 # Track updates separately

            for ach_data in achievements_to_seed: # Assuming ach_data are Achievement instances from models.py
                if ach_data.name not in existing_achievement_names:
                    # Detach from any previous session if necessary, or create new instance
                    # Since they are defined globally in models.py, using them directly *might* be okay,
                    # but creating new ones from their data might be safer if issues arise.
                    # For now, let's assume adding the instance directly is fine.
                    db.session.add(ach_data)
                    new_achievements_added += 1
                    print(f"Adding achievement: {ach_data.name}")
                else:
                    # Check if update is needed
                    existing_ach = Achievement.query.filter_by(name=ach_data.name).first()
                    if existing_ach and existing_ach.description != ach_data.description:
                        existing_ach.description = ach_data.description
                        achievements_updated += 1 # Count as processed for commit check
                        print(f"Updating description for achievement: {ach_data.name}")

            if new_achievements_added > 0 or achievements_updated > 0:
                db.session.commit()
                print(f"Achievements processed: {new_achievements_added} added, {achievements_updated} updated.")
            else:
                print("Achievements already up-to-date.")
            print("Achievement seeding process complete.")

        except SQLAlchemyError as e: # Catch potential database errors
            db.session.rollback() # Rollback on error
            print(f"Error during achievement seeding: {e}")
            app.logger.error(f"Achievement seeding error: {e}", exc_info=True)
        except Exception as e: # Catch other unexpected errors
             db.session.rollback()
             print(f"Unexpected error during achievement seeding: {e}")
             app.logger.error(f"Unexpected achievement seeding error: {e}", exc_info=True)


    # Register the CLI command
    @app.cli.command("seed-achievements")
    def seed_achievements_cli():
        """CLI command to seed/update achievements defined in models.py."""
        # Flask CLI provides app context automatically when running this command
        seed_achievements_command_internal()

    # --- ADD CONTEXT PROCESSOR --- <<<--- ADDED SECTION
    @app.context_processor
    def inject_now():
        """Inject current datetime into all templates."""
        return {'now': datetime.utcnow()} # Use utcnow() for consistency
    # -----------------------------

    # No need to explicitly import models here if blueprints import them,
    # as SQLAlchemy/Migrate will discover them through the imports when
    # the app context is created.

    return app
