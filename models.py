from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy
db = SQLAlchemy()

# Association tables for many-to-many relationships
society_moderators = db.Table('society_moderators',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('society_id', db.Integer, db.ForeignKey('societies.id'))
)

society_bans = db.Table('society_bans',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('society_id', db.Integer, db.ForeignKey('societies.id')),
    db.Column('ban_time', db.DateTime, default=datetime.utcnow)
)

society_subscribers = db.Table('society_subscribers',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('society_id', db.Integer, db.ForeignKey('societies.id')),
    db.Column('subscribed_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    banned_until = db.Column(db.DateTime, nullable=True)
    ban_reason = db.Column(db.String(255), nullable=True)
    karma = db.Column(db.Integer, default=0)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    moderated_societies = db.relationship('Society', secondary=society_moderators, backref=db.backref('moderators', lazy='dynamic'))
    banned_societies = db.relationship('Society', secondary=society_bans, backref=db.backref('banned_users', lazy='dynamic'))
    subscribed_societies = db.relationship('Society', secondary=society_subscribers, lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def is_subscribed_to(self, society):
        """Check if user is subscribed to a society"""
        return self.subscribed_societies.filter_by(id=society.id).count() > 0
    
    def is_mod_of(self, society):
        """Check if user is a moderator of a society"""
        for mod_society in self.moderated_societies:
            if mod_society.id == society.id:
                return True
        return False
    
    def is_banned_from(self, society):
        """Check if user is banned from a society"""
        for banned_society in self.banned_societies:
            if banned_society.id == society.id:
                return True
        return False
        
    def is_banned(self):
        """Check if user is globally banned"""
        if self.banned_until is None:
            return False
        return self.banned_until > datetime.utcnow()
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_mod_of(self, society):
        return society in self.moderated_societies
    
    def is_banned_from(self, society):
        return society in self.banned_societies
    
    def is_banned(self):
        if self.banned_until is None:
            return False
        return self.banned_until > datetime.utcnow()

class Society(db.Model):
    __tablename__ = 'societies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_locked = db.Column(db.Boolean, default=False)
    is_private = db.Column(db.Boolean, default=False)
    
    # Relationships
    posts = db.relationship('Post', backref='society', lazy='dynamic')
    creator = db.relationship('User', foreign_keys=[creator_id])
    #subscribers = db.relationship('User', secondary=society_subscribers, lazy='dynamic')
    subscribers = db.relationship('User', secondary=society_subscribers, lazy='dynamic',overlaps="subscribed_societies"  # Add this parameter
)

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    society_id = db.Column(db.Integer, db.ForeignKey('societies.id'))
    is_deleted = db.Column(db.Boolean, default=False)
    is_sticky = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    votes = db.relationship('Vote', foreign_keys='Vote.post_id', backref='post', lazy='dynamic')
    reports = db.relationship('Report', foreign_keys='Report.reported_post_id', backref='reported_post', lazy='dynamic')
    
    @property
    def score(self):
        upvotes = Vote.query.filter_by(post_id=self.id, is_upvote=True).count()
        downvotes = Vote.query.filter_by(post_id=self.id, is_upvote=False).count()
        return upvotes - downvotes
        
    def user_vote(self, user_id):
        """Check if a user has voted on this post and return the vote type"""
        vote = Vote.query.filter_by(post_id=self.id, user_id=user_id).first()
        if not vote:
            return 0
        return 1 if vote.is_upvote else -1
        
    @property
    def is_edited(self):
        """Check if the post has been edited"""
        return self.created_at != self.updated_at

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Relationships
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    votes = db.relationship('Vote', foreign_keys='Vote.comment_id', backref='comment', lazy='dynamic')
    reports = db.relationship('Report', foreign_keys='Report.reported_comment_id', backref='reported_comment', lazy='dynamic')
    
    @property
    def score(self):
        upvotes = Vote.query.filter_by(comment_id=self.id, is_upvote=True).count()
        downvotes = Vote.query.filter_by(comment_id=self.id, is_upvote=False).count()
        return upvotes - downvotes
        
    def user_vote(self, user_id):
        """Check if a user has voted on this comment and return the vote type"""
        vote = Vote.query.filter_by(comment_id=self.id, user_id=user_id).first()
        if not vote:
            return 0
        return 1 if vote.is_upvote else -1
        
    @property
    def is_edited(self):
        """Check if the comment has been edited"""
        return self.created_at != self.updated_at

class Vote(db.Model):
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    is_upvote = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User')

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject = db.Column(db.String(255))
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    deleted_by_sender = db.Column(db.Boolean, default=False)
    deleted_by_recipient = db.Column(db.Boolean, default=False)

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reported_post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    reported_comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reported_society_id = db.Column(db.Integer, db.ForeignKey('societies.id'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolution_note = db.Column(db.Text, nullable=True)
    report_type = db.Column(db.String(20), nullable=False)  # 'post', 'comment', 'user', 'society'
    society_id = db.Column(db.Integer, db.ForeignKey('societies.id'), nullable=True)  # Society where the report was made
    
    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id])
    reported_user = db.relationship('User', foreign_keys=[reported_user_id])
    reported_society = db.relationship('Society', foreign_keys=[reported_society_id])
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_id])