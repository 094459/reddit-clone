from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from models import Post, Comment, Society, Vote, Report, db
from forms import PostForm, CommentForm, ReportForm
from datetime import datetime
from sqlalchemy import desc

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/post/<int:post_id>')
def view_post(post_id):
    """Display a post and its comments"""
    post = Post.query.get_or_404(post_id)
    
    # Check if post is deleted and user is not a mod or admin
    if post.is_deleted and not (current_user.is_admin or current_user.is_mod_of(post.society)):
        abort(404)
    
    # Get comments for the post
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None, is_deleted=False).order_by(desc(Comment.created_at)).all()
    
    # Check if user has voted on this post
    user_vote = None
    if current_user.is_authenticated:
        user_vote = Vote.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    comment_form = CommentForm()
    report_form = ReportForm()
    
    return render_template('post.html', 
                          title=post.title,
                          post=post,
                          comments=comments,
                          user_vote=user_vote,
                          comment_form=comment_form,
                          report_form=report_form)

@posts_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    """Create a new post"""
    form = PostForm()
    
    # Populate society choices
    societies = Society.query.filter_by(is_locked=False).all()
    form.society.choices = [(s.id, s.name) for s in societies]
    
    if form.validate_on_submit():
        society = Society.query.get(form.society.data)
        
        # Check if society exists and is not locked
        if not society:
            flash('Society not found', 'danger')
            return redirect(url_for('main.home'))
        
        if society.is_locked:
            flash('This society is locked and does not accept new posts', 'danger')
            return redirect(url_for('societies.view_society', society_id=society.id))
        
        # Check if user is banned from the society
        if current_user.is_banned_from(society):
            flash('You are banned from posting in this society', 'danger')
            return redirect(url_for('societies.view_society', society_id=society.id))
        
        # Create new post
        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id,
            society_id=society.id
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Your post has been created!', 'success')
        return redirect(url_for('posts.view_post', post_id=post.id))
    
    return render_template('new_post.html', title='New Post', form=form)

@posts_bp.route('/post/<int:post_id>/vote', methods=['POST'])
@login_required
def vote_post(post_id):
    """Handle post voting"""
    post = Post.query.get_or_404(post_id)
    
    # Check if post is deleted
    if post.is_deleted:
        flash('Cannot vote on a deleted post', 'danger')
        return redirect(url_for('posts.view_post', post_id=post_id))
    
    # Get vote direction from form
    is_upvote = request.form.get('vote') == 'up'
    
    # Check if user has already voted on this post
    existing_vote = Vote.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing_vote:
        # If same vote direction, remove vote (toggle off)
        if existing_vote.is_upvote == is_upvote:
            db.session.delete(existing_vote)
        else:
            # If different direction, update vote
            existing_vote.is_upvote = is_upvote
            existing_vote.created_at = datetime.utcnow()
    else:
        # Create new vote
        vote = Vote(
            user_id=current_user.id,
            post_id=post_id,
            is_upvote=is_upvote
        )
        db.session.add(vote)
    
    db.session.commit()
    
    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {'success': True, 'score': post.score}
    
    return redirect(url_for('posts.view_post', post_id=post_id))

@posts_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete a post"""
    post = Post.query.get_or_404(post_id)
    
    # Check if user is authorized to delete (author, mod, or admin)
    if post.user_id != current_user.id and not current_user.is_mod_of(post.society) and not current_user.is_admin:
        flash('You are not authorized to delete this post', 'danger')
        return redirect(url_for('posts.view_post', post_id=post_id))
    
    # Mark post as deleted instead of actually deleting
    post.is_deleted = True
    db.session.commit()
    
    flash('Post has been deleted', 'success')
    return redirect(url_for('societies.view_society', society_id=post.society_id))

@posts_bp.route('/post/<int:post_id>/report', methods=['POST'])
@login_required
def report_post(post_id):
    """Report a post"""
    post = Post.query.get_or_404(post_id)
    form = ReportForm()
    
    if form.validate_on_submit():
        # Check if user has already reported this post
        existing_report = Report.query.filter_by(
            reporter_id=current_user.id,
            reported_post_id=post_id
        ).first()
        
        if existing_report:
            flash('You have already reported this post', 'info')
        else:
            report = Report(
                reporter_id=current_user.id,
                reported_post_id=post_id,
                reason=form.reason.data,
                report_type='post',
                society_id=post.society_id
            )
            db.session.add(report)
            db.session.commit()
            flash('Post has been reported to moderators', 'success')
    
    return redirect(url_for('posts.view_post', post_id=post_id))

@posts_bp.route('/post/<int:post_id>/sticky', methods=['POST'])
@login_required
def sticky_post(post_id):
    """Sticky or unsticky a post"""
    post = Post.query.get_or_404(post_id)
    
    # Check if user is a mod or admin
    if not current_user.is_mod_of(post.society) and not current_user.is_admin:
        flash('You are not authorized to sticky posts', 'danger')
        return redirect(url_for('posts.view_post', post_id=post_id))
    
    # Toggle sticky status
    post.is_sticky = not post.is_sticky
    db.session.commit()
    
    flash(f'Post has been {"stickied" if post.is_sticky else "unstickied"}', 'success')
    return redirect(url_for('posts.view_post', post_id=post_id))

@posts_bp.route('/post/<int:post_id>/lock', methods=['POST'])
@login_required
def lock_post(post_id):
    """Lock or unlock a post"""
    post = Post.query.get_or_404(post_id)
    
    # Check if user is a mod or admin
    if not current_user.is_mod_of(post.society) and not current_user.is_admin:
        flash('You are not authorized to lock posts', 'danger')
        return redirect(url_for('posts.view_post', post_id=post_id))
    
    # Toggle lock status
    post.is_locked = not post.is_locked
    db.session.commit()
    
    flash(f'Post has been {"locked" if post.is_locked else "unlocked"}', 'success')
    return redirect(url_for('posts.view_post', post_id=post_id))