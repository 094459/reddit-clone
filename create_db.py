from app import app, db
from models import User, Society, Post, Comment, Vote, Message, Report
from werkzeug.security import generate_password_hash
from datetime import datetime

# Create database tables
with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        password_hash=generate_password_hash('adminpassword'),
        created_at=datetime.utcnow(),
        is_admin=True
    )
    
    # Create test user
    test_user = User(
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('password'),
        created_at=datetime.utcnow()
    )
    
    # Add users to database
    db.session.add(admin)
    db.session.add(test_user)
    db.session.commit()
    
    # Create test society
    test_society = Society(
        name='TestSociety',
        description='This is a test society for development purposes.',
        created_at=datetime.utcnow(),
        creator_id=admin.id
    )
    
    # Add society to database
    db.session.add(test_society)
    db.session.commit()
    
    # Add admin as moderator
    test_society.moderators.append(admin)
    
    # Add test user as subscriber
    test_society.subscribers.append(test_user)
    
    # Create test post
    test_post = Post(
        title='Welcome to TestSociety',
        content='This is the first post in our test society. Feel free to comment!',
        created_at=datetime.utcnow(),
        user_id=admin.id,
        society_id=test_society.id
    )
    
    # Add post to database
    db.session.add(test_post)
    db.session.commit()
    
    # Create test comment
    test_comment = Comment(
        content='This is a test comment on the first post.',
        created_at=datetime.utcnow(),
        user_id=test_user.id,
        post_id=test_post.id
    )
    
    # Add comment to database
    db.session.add(test_comment)
    db.session.commit()
    
    print("Database created successfully with test data!")