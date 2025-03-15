from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, User, Society, Post, Comment, Vote, Report
from sqlalchemy import func
from datetime import datetime, timedelta

mod_bp = Blueprint('mod', __name__)

# Moderator access decorator
def mod_required(f):
    def decorated_function(*args, **kwargs):
        society_id = kwargs.get('society_id')
        if society_id:
            society = Society.query.get_or_404(society_id)
            if current_user not in society.moderators and not current_user.is_admin:
                abort(403)
        else:
            # Check if user is a moderator of any society
            if not current_user.moderated_societies.count() and not current_user.is_admin:
                abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@mod_bp.route('/mod')
@login_required
def mod_panel():
    # Get societies where the current user is a moderator
    moderated_societies = current_user.moderated_societies.all()
    
    if not moderated_societies and not current_user.is_admin:
        flash('You are not a moderator of any society.', 'warning')
        return redirect(url_for('main.index'))
        
    return render_template('mod_panel.html', societies=moderated_societies)

@mod_bp.route('/mod/society/<int:society_id>')
@login_required
@mod_required
def mod_society(society_id):
    society = Society.query.get_or_404(society_id)
    return render_template('mod_society.html', society=society)

@mod_bp.route('/mod/dashboard/<int:society_id>')
@login_required
@mod_required
def mod_dashboard(society_id):
    society = Society.query.get_or_404(society_id)
    
    # Get statistics for moderator dashboard
    post_count = Post.query.filter_by(society_id=society_id).count()
    comment_count = Comment.query.join(Post).filter(Post.society_id == society_id).count()
    
    # Recent reports in this society
    reports = Report.query.filter_by(society_id=society_id).order_by(Report.created_at.desc()).limit(10).all()
    
    # Posts in the last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_posts = Post.query.filter(Post.society_id == society_id, Post.created_at >= week_ago).count()
    
    # Active users (users who posted or commented in the last 7 days)
    active_posters = db.session.query(Post.user_id).distinct().filter(
        Post.society_id == society_id,
        Post.created_at >= week_ago
    ).count()
    
    return render_template('mod_dash.html', 
                          society=society,
                          post_count=post_count,
                          comment_count=comment_count,
                          reports=reports,
                          new_posts=new_posts,
                          active_users=active_posters)

@mod_bp.route('/mod/reports/<int:society_id>')
@login_required
@mod_required
def mod_reports(society_id):
    society = Society.query.get_or_404(society_id)
    reports = Report.query.filter_by(society_id=society_id).order_by(Report.created_at.desc()).all()
    return render_template('mod_reports.html', society=society, reports=reports)

@mod_bp.route('/mod/ban/<int:society_id>/<int:user_id>', methods=['POST'])
@login_required
@mod_required
def ban_from_society(society_id, user_id):
    society = Society.query.get_or_404(society_id)
    user = User.query.get_or_404(user_id)
    reason = request.form.get('reason', 'No reason provided')
    
    if user in society.moderators and not current_user.is_admin:
        flash('Cannot ban another moderator.', 'danger')
        return redirect(url_for('mod.mod_society', society_id=society_id))
    
    if user not in society.banned_users:
        society.banned_users.append(user)
        db.session.commit()
        
        # Add ban reason to a separate table in a real application
        flash(f'User {user.username} has been banned from {society.name}.', 'success')
    else:
        flash(f'User {user.username} is already banned from {society.name}.', 'warning')
        
    return redirect(url_for('mod.mod_society', society_id=society_id))

@mod_bp.route('/mod/unban/<int:society_id>/<int:user_id>')
@login_required
@mod_required
def unban_from_society(society_id, user_id):
    society = Society.query.get_or_404(society_id)
    user = User.query.get_or_404(user_id)
    
    if user in society.banned_users:
        society.banned_users.remove(user)
        db.session.commit()
        flash(f'User {user.username} has been unbanned from {society.name}.', 'success')
    else:
        flash(f'User {user.username} is not banned from {society.name}.', 'warning')
        
    return redirect(url_for('mod.mod_society', society_id=society_id))

@mod_bp.route('/mod/add_moderator/<int:society_id>', methods=['POST'])
@login_required
@mod_required
def add_moderator(society_id):
    society = Society.query.get_or_404(society_id)
    username = request.form.get('username')
    
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f'User {username} not found.', 'danger')
        return redirect(url_for('mod.mod_society', society_id=society_id))
        
    if user in society.moderators:
        flash(f'{username} is already a moderator of {society.name}.', 'warning')
    else:
        society.moderators.append(user)
        db.session.commit()
        flash(f'{username} is now a moderator of {society.name}.', 'success')
        
    return redirect(url_for('mod.mod_society', society_id=society_id))

@mod_bp.route('/mod/remove_moderator/<int:society_id>/<int:user_id>')
@login_required
@mod_required
def remove_moderator(society_id, user_id):
    society = Society.query.get_or_404(society_id)
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot remove yourself as moderator.', 'danger')
        return redirect(url_for('mod.mod_society', society_id=society_id))
        
    if user in society.moderators:
        society.moderators.remove(user)
        db.session.commit()
        flash(f'{user.username} is no longer a moderator of {society.name}.', 'success')
    else:
        flash(f'{user.username} is not a moderator of {society.name}.', 'warning')
        
    return redirect(url_for('mod.mod_society', society_id=society_id))

@mod_bp.route('/mod/sticky/<int:post_id>')
@login_required
def sticky_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if user is a moderator of the post's society
    if current_user not in post.society.moderators and not current_user.is_admin:
        abort(403)
    
    post.is_sticky = not post.is_sticky
    db.session.commit()
    
    if post.is_sticky:
        flash('Post has been stickied.', 'success')
    else:
        flash('Post has been unstickied.', 'success')
        
    return redirect(url_for('posts.view_post', post_id=post_id))

@mod_bp.route('/mod/lock/<int:post_id>')
@login_required
def lock_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Check if user is a moderator of the post's society
    if current_user not in post.society.moderators and not current_user.is_admin:
        abort(403)
    
    post.is_locked = not post.is_locked
    db.session.commit()
    
    if post.is_locked:
        flash('Post has been locked.', 'success')
    else:
        flash('Post has been unlocked.', 'success')
        
    return redirect(url_for('posts.view_post', post_id=post_id))

@mod_bp.route('/mod/log/<int:society_id>')
@login_required
@mod_required
def mod_log(society_id):
    society = Society.query.get_or_404(society_id)
    # In a real application, you would have a proper mod action log table
    # This is a placeholder
    return render_template('mod_log.html', society=society)

@mod_bp.route('/mod/trends/<int:society_id>')
@login_required
@mod_required
def mod_trends(society_id):
    society = Society.query.get_or_404(society_id)
    
    # Get data for trends over time
    # This would typically involve more complex queries with grouping by date
    
    # Example: Posts per day for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # This is a simplified version - in a real app you'd use proper date grouping
    posts_by_day = db.session.query(
        func.date(Post.created_at).label('date'),
        func.count(Post.id).label('count')
    ).filter(
        Post.society_id == society_id,
        Post.created_at >= thirty_days_ago
    ).group_by(func.date(Post.created_at)).all()
    
    # Convert to format suitable for charts
    dates = [str(row[0]) for row in posts_by_day]
    post_counts = [row[1] for row in posts_by_day]
    
    return render_template('mod_dash_trends.html', 
                          society=society,
                          dates=dates,
                          post_counts=post_counts)