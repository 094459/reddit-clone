from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, User, Society, Post, Comment, Vote, Report
from sqlalchemy import func
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

# Admin access decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_panel():
    return render_template('admin_panel.html')

@admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Get statistics for admin dashboard
    user_count = User.query.count()
    post_count = Post.query.count()
    comment_count = Comment.query.count()
    society_count = Society.query.count()
    
    # Recent reports
    reports = Report.query.order_by(Report.created_at.desc()).limit(10).all()
    
    # New users in the last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users = User.query.filter(User.created_at >= week_ago).count()
    
    # Active users (users who posted or commented in the last 7 days)
    active_posters = db.session.query(Post.user_id).distinct().filter(Post.created_at >= week_ago).count()
    active_commenters = db.session.query(Comment.user_id).distinct().filter(Comment.created_at >= week_ago).count()
    
    return render_template('admin_dash.html', 
                          user_count=user_count,
                          post_count=post_count,
                          comment_count=comment_count,
                          society_count=society_count,
                          reports=reports,
                          new_users=new_users,
                          active_users=max(active_posters, active_commenters))

@admin_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template('admin_reports.html', reports=reports)

@admin_bp.route('/admin/ban/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    reason = request.form.get('reason', 'No reason provided')
    duration = int(request.form.get('duration', 0))
    
    if user.is_admin:
        flash('Cannot ban another admin.', 'danger')
        return redirect(url_for('admin.admin_users'))
    
    if duration > 0:
        user.banned_until = datetime.utcnow() + timedelta(days=duration)
    else:
        user.banned_until = datetime(9999, 12, 31)  # Permanent ban
    
    user.ban_reason = reason
    db.session.commit()
    
    flash(f'User {user.username} has been banned.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/unban/<int:user_id>')
@login_required
@admin_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.banned_until = None
    user.ban_reason = None
    db.session.commit()
    
    flash(f'User {user.username} has been unbanned.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/make_admin/<int:user_id>')
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    
    flash(f'{user.username} is now an admin.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/remove_admin/<int:user_id>')
@login_required
@admin_required
def remove_admin(user_id):
    if current_user.id == user_id:
        flash('You cannot remove yourself as admin.', 'danger')
        return redirect(url_for('admin.admin_users'))
        
    user = User.query.get_or_404(user_id)
    user.is_admin = False
    db.session.commit()
    
    flash(f'{user.username} is no longer an admin.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/trends')
@login_required
@admin_required
def admin_trends():
    # Get data for trends over time
    # This would typically involve more complex queries with grouping by date
    
    # Example: Posts per day for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # This is a simplified version - in a real app you'd use proper date grouping
    posts_by_day = db.session.query(
        func.date(Post.created_at).label('date'),
        func.count(Post.id).label('count')
    ).filter(Post.created_at >= thirty_days_ago).group_by(func.date(Post.created_at)).all()
    
    # Convert to format suitable for charts
    dates = [str(row[0]) for row in posts_by_day]
    post_counts = [row[1] for row in posts_by_day]
    
    return render_template('admin_dash_trends.html', 
                          dates=dates,
                          post_counts=post_counts)

@admin_bp.route('/admin/log')
@login_required
@admin_required
def admin_log():
    # In a real application, you would have a proper admin action log table
    # This is a placeholder
    return render_template('admin_log.html')