from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from models import Society, Post, User, db
from forms import SocietyForm, SocietyDescriptionForm
from datetime import datetime
from sqlalchemy import desc

societies_bp = Blueprint('societies', __name__)

@societies_bp.route('/society/<int:society_id>')
def view_society(society_id):
    """Display a society and its posts"""
    society = Society.query.get_or_404(society_id)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get sticky posts first, then regular posts sorted by time
    sticky_posts = Post.query.filter_by(
        society_id=society_id,
        is_deleted=False,
        is_sticky=True
    ).order_by(desc(Post.created_at)).all()
    
    regular_posts = Post.query.filter_by(
        society_id=society_id,
        is_deleted=False,
        is_sticky=False
    ).order_by(desc(Post.created_at)).paginate(page=page, per_page=per_page)
    
    # Combine sticky and regular posts
    posts = sticky_posts + regular_posts.items
    
    # Check if user is subscribed
    is_subscribed = False
    if current_user.is_authenticated:
        is_subscribed = society in current_user.subscribed_societies
    
    # Check if user is a moderator
    is_moderator = False
    if current_user.is_authenticated:
        is_moderator = current_user in society.moderators
    
    return render_template('society.html',
                          title=society.name,
                          society=society,
                          posts=posts,
                          pagination=regular_posts,
                          is_subscribed=is_subscribed,
                          is_moderator=is_moderator)

@societies_bp.route('/society/new', methods=['GET', 'POST'])
@login_required
def new_society():
    """Create a new society"""
    form = SocietyForm()
    
    if form.validate_on_submit():
        # Check if society name already exists
        existing_society = Society.query.filter_by(name=form.name.data).first()
        if existing_society:
            flash('Society name already exists', 'danger')
            return render_template('new_society.html', title='New Society', form=form)
        
        # Create new society
        society = Society(
            name=form.name.data,
            description=form.description.data,
            created_at=datetime.utcnow()
        )
        
        # Add current user as moderator
        society.moderators.append(current_user)
        
        # Auto-subscribe creator
        society.subscribers.append(current_user)
        
        db.session.add(society)
        db.session.commit()
        
        flash('Your society has been created!', 'success')
        return redirect(url_for('societies.view_society', society_id=society.id))
    
    return render_template('new_society.html', title='New Society', form=form)

@societies_bp.route('/society/<int:society_id>/subscribe', methods=['POST'])
@login_required
def subscribe(society_id):
    """Subscribe to a society"""
    society = Society.query.get_or_404(society_id)
    
    if society in current_user.subscribed_societies:
        flash(f'You are already subscribed to {society.name}', 'info')
    else:
        current_user.subscribed_societies.append(society)
        flash(f'You have subscribed to {society.name}', 'success')
    
    db.session.commit()
    return redirect(url_for('societies.view_society', society_id=society_id))

@societies_bp.route('/society/<int:society_id>/unsubscribe', methods=['POST'])
@login_required
def unsubscribe(society_id):
    """Unsubscribe from a society"""
    society = Society.query.get_or_404(society_id)
    
    if society in current_user.subscribed_societies:
        current_user.subscribed_societies.remove(society)
        flash(f'You have unsubscribed from {society.name}', 'info')
    else:
        flash(f'You are not subscribed to {society.name}', 'info')
    
    db.session.commit()
    return redirect(url_for('societies.view_society', society_id=society_id))

@societies_bp.route('/society/<int:society_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_society(society_id):
    """Edit society description"""
    society = Society.query.get_or_404(society_id)
    
    # Check if user is a moderator
    if current_user not in society.moderators and not current_user.is_admin:
        flash('You do not have permission to edit this society', 'danger')
        return redirect(url_for('societies.view_society', society_id=society_id))
    
    form = SocietyDescriptionForm()
    
    if form.validate_on_submit():
        society.description = form.description.data
        db.session.commit()
        flash('Society description has been updated', 'success')
        return redirect(url_for('societies.view_society', society_id=society_id))
    
    # Pre-fill form with current description
    form.description.data = society.description
    return render_template('edit_society.html', title=f'Edit {society.name}', form=form, society=society)

@societies_bp.route('/society/<int:society_id>/moderators')
@login_required
def moderators(society_id):
    """View and manage society moderators"""
    society = Society.query.get_or_404(society_id)
    
    # Check if user is a moderator
    if current_user not in society.moderators and not current_user.is_admin:
        flash('You do not have permission to view this page', 'danger')
        return redirect(url_for('societies.view_society', society_id=society_id))
    
    return render_template('society_mods.html', title=f'{society.name} Moderators', society=society)

@societies_bp.route('/society/<int:society_id>/add_moderator', methods=['POST'])
@login_required
def add_moderator(society_id):
    """Add a moderator to a society"""
    society = Society.query.get_or_404(society_id)
    
    # Check if user is a moderator
    if current_user not in society.moderators and not current_user.is_admin:
        flash('You do not have permission to add moderators', 'danger')
        return redirect(url_for('societies.view_society', society_id=society_id))
    
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash(f'User {username} not found', 'danger')
    elif user in society.moderators:
        flash(f'{username} is already a moderator', 'info')
    else:
        society.moderators.append(user)
        db.session.commit()
        flash(f'{username} has been added as a moderator', 'success')
    
    return redirect(url_for('societies.moderators', society_id=society_id))

@societies_bp.route('/society/<int:society_id>/remove_moderator/<int:user_id>', methods=['POST'])
@login_required
def remove_moderator(society_id, user_id):
    """Remove a moderator from a society"""
    society = Society.query.get_or_404(society_id)
    user = User.query.get_or_404(user_id)
    
    # Check if user is a moderator
    if current_user not in society.moderators and not current_user.is_admin:
        flash('You do not have permission to remove moderators', 'danger')
        return redirect(url_for('societies.view_society', society_id=society_id))
    
    # Prevent removing the last moderator
    if len(society.moderators) <= 1 and user in society.moderators:
        flash('Cannot remove the last moderator', 'danger')
        return redirect(url_for('societies.moderators', society_id=society_id))
    
    if user in society.moderators:
        society.moderators.remove(user)
        db.session.commit()
        flash(f'{user.username} has been removed as a moderator', 'success')
    else:
        flash(f'{user.username} is not a moderator', 'info')
    
    return redirect(url_for('societies.moderators', society_id=society_id))

@societies_bp.route('/society/<int:society_id>/lock', methods=['POST'])
@login_required
def lock_society(society_id):
    """Lock or unlock a society"""
    society = Society.query.get_or_404(society_id)
    
    # Check if user is an admin
    if not current_user.is_admin:
        flash('You do not have permission to lock societies', 'danger')
        return redirect(url_for('societies.view_society', society_id=society_id))
    
    # Toggle lock status
    society.is_locked = not society.is_locked
    db.session.commit()
    
    flash(f'Society has been {"locked" if society.is_locked else "unlocked"}', 'success')
    return redirect(url_for('societies.view_society', society_id=society_id))