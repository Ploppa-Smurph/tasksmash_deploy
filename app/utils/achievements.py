# app/utils/achievements.py
from flask import flash
from app.extensions import db # Use extensions
from app.models import Achievement, UserAchievement # Use models directly

def award_achievement(user, name):
    """Awards an achievement to a user if not already awarded."""
    # Check if user already has this achievement
    if user.has_achievement(name):
        return # Already has it

    achievement = Achievement.query.filter_by(name=name).first()
    if achievement:
        new_award = UserAchievement(user_id=user.id, achievement_id=achievement.id)
        db.session.add(new_award)
        # Commit happens in the calling function or after evaluate_achievements completes
        flash(f'Achievement Unlocked: {achievement.name} — {achievement.description}', 'achievement')
        return True # Indicate an award was potentially added
    return False

def evaluate_achievements(user):
    """Checks conditions and awards achievements. Commits at the end if any were awarded."""
    # Import models needed for counts here
    from app.models import Todo, Comment, Follow

    awarded_new = False # Flag to track if we need to commit

    # --- Calculate counts ---
    task_count = Todo.query.filter_by(user_id=user.id).count()
    completed_count = Todo.query.filter_by(user_id=user.id, completed=True).count()
    incomplete_count = Todo.query.filter_by(user_id=user.id, completed=False).count()
    comment_count = Comment.query.filter_by(user_id=user.id).count()
    reply_count = Comment.query.filter_by(user_id=user.id).filter(Comment.parent_id.isnot(None)).count()
    followers_count = Follow.query.filter_by(follower_id=user.id).count() # Users followed by current_user

    # --- Award logic (call award_achievement) ---
    if task_count >= 10:
        awarded_new = award_achievement(user, 'Task Initiator') or awarded_new
    if task_count >= 50:
        awarded_new = award_achievement(user, 'Task Master') or awarded_new
    if completed_count >= 5:
        awarded_new = award_achievement(user, 'Goal Crusher') or awarded_new
    if completed_count >= 25:
        awarded_new = award_achievement(user, 'Finisher') or awarded_new
    if task_count > 0 and completed_count == task_count:
        awarded_new = award_achievement(user, 'Perfectionist') or awarded_new
    if incomplete_count == 0 and task_count > 0:
        awarded_new = award_achievement(user, 'Empty Inbox') or awarded_new

    if comment_count >= 1:
        awarded_new = award_achievement(user, 'Comment Commander') or awarded_new
    if comment_count >= 10:
        awarded_new = award_achievement(user, 'Chatterbox') or awarded_new
    if reply_count >= 5:
        awarded_new = award_achievement(user, 'Reply Ruler') or awarded_new

    if followers_count >= 1:
        awarded_new = award_achievement(user, 'Friendly Follower') or awarded_new
    if followers_count >= 5:
        awarded_new = award_achievement(user, 'Social Butterfly') or awarded_new

    # Check for popular pick (could be optimized)
    if not user.has_achievement('Popular Pick'):
        user_tasks = Todo.query.filter_by(user_id=user.id).options(db.joinedload(Todo.comments)).all()
        for task in user_tasks:
            if len(task.comments) >= 5:
                awarded_new = award_achievement(user, 'Popular Pick') or awarded_new
                break # Only award once

    # Procrastinator check (needs edit_count on Todo model)
    if Todo.query.filter(Todo.user_id == user.id, Todo.edit_count >= 3).first():
         awarded_new = award_achievement(user, 'Procrastinator') or awarded_new

    # --- Commit if any new achievements were added ---
    if awarded_new: # Only commit if award_achievement returned True at least once
        try:
            db.session.commit()
            print("Achievement commit successful.") # Simple print for now
        except Exception as e:
            db.session.rollback()
            # Log the error using Flask's logger if possible
            try:
                 # Check if app context is available (might not be if called from background task)
                 current_app.logger.error(f"Error committing achievement awards: {e}", exc_info=True)
            except RuntimeError:
                 # Fallback if no app context
                 print(f"ERROR committing achievement awards (no app context): {e}")