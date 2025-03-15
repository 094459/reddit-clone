from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from models import Comment, Post, Vote, Report, db
from forms import CommentForm
from datetime import datetime

comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Add a new comment to a post"""
    post = Post.query.get_or_404(post_id)
    
    # Check if post is locked
    if post.is_locked:
        flash('This post is locked. New comments cannot be added.', 'warning')
        return redirect(url_for('posts.view_post', post_id=post_id))
    
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            post_id=post_id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(comment)
        db.session.commit()
        
        flash('Your comment has been added.', 'success')
    
    return redirect(url_for('posts.view_post', post_id=post_id))

@comments_bp.route('/comment/<int:comment_id>/reply', methods=['POST'])
@login_required
def add_reply(comment_id):
    """Add a reply to a comment"""
    parent_comment = Comment.query.get_or_404(comment_id)
    post = Post.query.get_or_404(parent_comment.post_id)
    
    # Check if post is locked
    if post.is_locked:
        flash('This post is locked. New replies cannot be added.', 'warning')
        return redirect(url_for('posts.view_post', post_id=post.id))
    
    content = request.form.get('content')
    if not content:
        flash('Reply cannot be empty.', 'danger')
        return redirect(url_for('posts.view_post', post_id=post.id))
    
    reply = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post.id,
        parent_id=comment_id,
        created_at=datetime.utcnow()
    )
    
    db.session.add(reply)
    db.session.commit()
    
    flash('Your reply has been added.', 'success')
    return redirect(url_for('posts.view_post', post_id=post.id))

@comments_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if user is authorized to delete (author, mod, or admin)
    if comment.user_id != current_user.id and not current_user.is_mod_of(comment.post.society) and not current_user.is_admin:
        flash('You are not authorized to delete this comment.', 'danger')
        return redirect(url_for('posts.view_post', post_id=comment.post_id))
    
    # Mark comment as deleted instead of actually deleting
    comment.is_deleted = True
    comment.content = "[deleted]"
    db.session.commit()
    
    flash('Comment has been deleted.', 'success')
    return redirect(url_for('posts.view_post', post_id=comment.post_id))

@comments_bp.route('/comment/<int:comment_id>/vote', methods=['POST'])
@login_required
def vote_comment(comment_id):
    """Handle comment voting"""
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if comment is deleted
    if comment.is_deleted:
        flash('Cannot vote on a deleted comment.', 'danger')
        return redirect(url_for('posts.view_post', post_id=comment.post_id))
    
    # Get vote direction from form
    is_upvote = request.form.get('vote') == 'up'
    
    # Check if user has already voted on this comment
    existing_vote = Vote.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()
    
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
            comment_id=comment_id,
            is_upvote=is_upvote
        )
        db.session.add(vote)
    
    db.session.commit()
    
    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {'success': True, 'score': comment.score}
    
    return redirect(url_for('posts.view_post', post_id=comment.post_id))

@comments_bp.route('/comment/<int:comment_id>/report', methods=['POST'])
@login_required
def report_comment(comment_id):
    """Report a comment"""
    comment = Comment.query.get_or_404(comment_id)
    reason = request.form.get('reason')
    
    if not reason:
        flash('Please provide a reason for the report.', 'danger')
        return redirect(url_for('posts.view_post', post_id=comment.post_id))
    
    # Check if user has already reported this comment
    existing_report = Report.query.filter_by(
        reporter_id=current_user.id,
        reported_comment_id=comment_id
    ).first()
    
    if existing_report:
        flash('You have already reported this comment.', 'info')
    else:
        report = Report(
            reporter_id=current_user.id,
            reported_comment_id=comment_id,
            reason=reason,
            report_type='comment',
            society_id=comment.post.society_id
        )
        db.session.add(report)
        db.session.commit()
        flash('Comment has been reported to moderators.', 'success')
    
    return redirect(url_for('posts.view_post', post_id=comment.post_id))