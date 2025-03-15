from flask import Flask, render_template, redirect, url_for, flash, request, session, g
from flask_login import LoginManager, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import os
from datetime import datetime
from dotenv import load_dotenv
import jinja2

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///oeddit.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize database
from models import db, User, Society, Post, Comment, Vote, Message, Report
db.init_app(app)

# Initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    #return User.query.get(int(user_id))
    return db.session.get(User, int(user_id))

# Custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br_filter(s):
    if s is None:
        return ""
    return jinja2.utils.markupsafe.Markup(s.replace('\n', '<br>'))

# Import routes after initializing app to avoid circular imports
from routes.auth import auth_bp
from routes.main import main_bp
from routes.posts import posts_bp
from routes.comments import comments_bp
from routes.societies import societies_bp
from routes.users import users_bp
from routes.admin import admin_bp
from routes.mod import mod_bp
from routes.messages import messages_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(comments_bp)
app.register_blueprint(societies_bp)
app.register_blueprint(users_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(mod_bp)
app.register_blueprint(messages_bp)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', title='Page Not Found', message='The page you requested was not found.'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', title='Server Error', message='An internal server error occurred.'), 500

if __name__ == '__main__':
    app.run(debug=True)