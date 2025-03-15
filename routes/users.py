from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, User, Society, Post, Comment, Vote, Report
from forms import ProfileForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

users_bp = Blueprint('users', __name__)

@users_bp.route('/user/<int:user_id>')
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user.id, is_deleted=False).order_by(Post.created_at.desc()).limit(5).all()
    comments = Comment.query.filter_by(user_id=user.id, is_deleted=False).order_by(Comment.created_at.desc()).limit(5).all()
    
    # Count posts and comments
    post_count = Post.query.filter_by(user_id=user.id).count()
    comment_count = Comment.query.filter_by(user_id=user.id).count()
    
    return render_template('user.html', 
                          user=user, 
                          posts=posts, 
                          comments=comments, 
                          post_count=post_count,
                          comment_count=comment_count)

@users_bp.route('/user/profile')
@login_required
def profile():
    posts = Post.query.filter_by(user_id=current_user.id, is_deleted=False).order_by(Post.created_at.desc()).limit(5).all()
    comments = Comment.query.filter_by(user_id=current_user.id, is_deleted=False).order_by(Comment.created_at.desc()).limit(5).all()
    
    # Count posts, comments and subscriptions
    post_count = Post.query.filter_by(user_id=current_user.id).count()
    comment_count = Comment.query.filter_by(user_id=current_user.id).count()
    subscribed_count = current_user.subscribed_societies.count()
    
    return render_template('profile.html', 
                          user=current_user, 
                          posts=posts, 
                          comments=comments,
                          post_count=post_count,
                          comment_count=comment_count,
                          subscribed_count=subscribed_count)

@users_bp.route('/user/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        if form.password.data:
            # Check if current password is correct
            if check_password_hash(current_user.password_hash, form.current_password.data):
                current_user.password_hash = generate_password_hash(form.password.data)
                db.session.commit()
                flash('Your password has been updated!', 'success')
            else:
                flash('Current password is incorrect.', 'danger')
        
        # Update email if changed
        if form.email.data != current_user.email:
            # Check if email is already in use
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Email already in use.', 'danger')
            else:
                current_user.email = form.email.data
                db.session.commit()
                flash('Your email has been updated!', 'success')
            
        return redirect(url_for('users.profile'))
        
    # Pre-fill form with current data
    form.email.data = current_user.email
    return render_template('edit_profile.html', form=form)

@users_bp.route('/user/<int:user_id>/posts')
def user_posts(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user.id, is_deleted=False).order_by(Post.created_at.desc()).all()
    return render_template('user_posts.html', user=user, posts=posts)

@users_bp.route('/user/<int:user_id>/comments')
def user_comments(user_id):
    user = User.query.get_or_404(user_id)
    comments = Comment.query.filter_by(user_id=user.id, is_deleted=False).order_by(Comment.created_at.desc()).all()
    return render_template('user_comments.html', user=user, comments=comments)

@users_bp.route('/user/<int:user_id>/societies')
def user_societies(user_id):
    user = User.query.get_or_404(user_id)
    moderated_societies = user.moderated_societies
    return render_template('user_societies.html', user=user, societies=moderated_societies)

@users_bp.route('/report/user/<int:user_id>', methods=['POST'])
@login_required
def report_user(user_id):
    user = User.query.get_or_404(user_id)
    reason = request.form.get('reason')
    
    if not reason:
        flash('Please provide a reason for the report.', 'danger')
        return redirect(url_for('users.view_user', user_id=user.id))
    
    # Check if user has already reported this user
    existing_report = Report.query.filter_by(
        reporter_id=current_user.id,
        reported_user_id=user.id
    ).first()
    
    if existing_report:
        flash('You have already reported this user.', 'info')
    else:
        report = Report(
            reporter_id=current_user.id,
            reported_user_id=user.id,
            reason=reason,
            report_type='user',
            created_at=datetime.utcnow()
        )
        
        db.session.add(report)
        db.session.commit()
        flash('User has been reported to administrators.', 'success')
    
    return redirect(url_for('users.view_user', user_id=user.id))