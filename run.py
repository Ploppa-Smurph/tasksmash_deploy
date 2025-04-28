from app import app, db
from app.models import Achievement, Follow, User
from app import db


if __name__ == '__main__':
    with app.app_context():
        #db.drop_all()  # Optional: Only for development
        db.create_all()

        # Seed achievements
        achievements = [
            Achievement(name='Task Initiator', description='Created 10 tasks'),
            Achievement(name='Goal Crusher', description='Completed 5 tasks'),
            Achievement(name='Comment Commander', description='Posted your first comment'),
            Achievement(name='Task Master', description='Created 50 tasks'),
            Achievement(name='Finisher', description='Completed 25 tasks'),
            Achievement(name='Perfectionist', description='Completed all your tasks'),
            Achievement(name='Chatterbox', description='Left 10 comments'),
            Achievement(name='Reply Ruler', description='Left 5 replies'),
            Achievement(name='Friendly Follower', description='Followed 1 user'),
            Achievement(name='Social Butterfly', description='Followed 5 users'),
            Achievement(name='Popular Pick', description='A task of yours got 5 comments'),
            Achievement(name='Empty Inbox', description='You have no incomplete tasks'),
            Achievement(name='Procrastinator', description='You edited the same task 3 times')
        ]

        for ach in achievements:
            if not Achievement.query.filter_by(name=ach.name).first():
                db.session.add(ach)
        db.session.commit()
        print("Achievements seeded!")

        users = User.query.all()
        print(users)

        users = User.query.all()
        for user in users:
            print(user.id, user.username)

            follows = Follow.query.all()
            for follow in follows:
                print(follow.follower_id, "follows", follow.followee_id)

    app.run(debug=True)
