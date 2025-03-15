from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask_login import current_user, login_required
from models import Post, Society, db
from sqlalchemy import desc

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Redirect to home page or login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    else:
        return redirect(url_for('auth.login'))

@main_bp.route('/home')
def home():
    """Display home page with posts from all societies"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get sticky posts first, then regular posts sorted by time
    sticky_posts = Post.query.filter_by(
        is_deleted=False,
        is_sticky=True
    ).order_by(desc(Post.created_at)).all()
    
    regular_posts = Post.query.filter_by(
        is_deleted=False,
        is_sticky=False
    ).order_by(desc(Post.created_at)).paginate(page=page, per_page=per_page)
    
    # Combine sticky and regular posts
    posts = sticky_posts + regular_posts.items
    
    # Get trending societies (most active in the last week)
    trending_societies = Society.query.limit(5).all()  # This would need more complex logic in a real app
    
    return render_template('home.html', 
                          title='Home',
                          posts=posts, 
                          pagination=regular_posts,
                          trending_societies=trending_societies)