from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Message
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/messages')
@login_required
def inbox():
    received_messages = Message.query.filter_by(
        recipient_id=current_user.id,
        deleted_by_recipient=False
    ).order_by(Message.created_at.desc()).all()
    
    sent_messages = Message.query.filter_by(
        sender_id=current_user.id,
        deleted_by_sender=False
    ).order_by(Message.created_at.desc()).all()
    
    return render_template('messages/inbox.html', 
                         received_messages=received_messages,
                         sent_messages=sent_messages)

@messages_bp.route('/messages/new', methods=['GET', 'POST'])
@login_required
def new_message():
    if request.method == 'POST':
        recipient_name = request.form.get('recipient')
        subject = request.form.get('subject')
        body = request.form.get('body')
        
        recipient = User.query.filter_by(username=recipient_name).first()
        
        if not recipient:
            flash('User not found.', 'danger')
            return redirect(url_for('messages.inbox'))
            
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient.id,
            subject=subject,
            body=body,
            created_at=datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        
        flash('Message sent successfully.', 'success')
        return redirect(url_for('messages.inbox'))
        
    return render_template('messages/new_message.html')

@messages_bp.route('/messages/<int:message_id>')
@login_required
def view_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    # Check if user has permission to view this message
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        flash('You do not have permission to view this message.', 'danger')
        return redirect(url_for('messages.inbox'))
    
    # Mark as read if recipient is viewing
    if message.recipient_id == current_user.id and not message.is_read:
        message.is_read = True
        message.read_at = datetime.utcnow()
        db.session.commit()
    
    return render_template('messages/view_message.html', message=message)

@messages_bp.route('/messages/<int:message_id>/delete')
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    # Check if user has permission to delete this message
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        flash('You do not have permission to delete this message.', 'danger')
        return redirect(url_for('messages.inbox'))
    
    # Mark as deleted for the appropriate user
    if message.sender_id == current_user.id:
        message.deleted_by_sender = True
    if message.recipient_id == current_user.id:
        message.deleted_by_recipient = True
    
    # If both users have deleted the message, we can remove it from the database
    if message.deleted_by_sender and message.deleted_by_recipient:
        db.session.delete(message)
    
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('messages.inbox'))

@messages_bp.route('/messages/<int:message_id>/reply', methods=['GET', 'POST'])
@login_required
def reply_message(message_id):
    original = Message.query.get_or_404(message_id)
    
    # Check if user has permission to reply to this message
    if original.recipient_id != current_user.id:
        flash('You do not have permission to reply to this message.', 'danger')
        return redirect(url_for('messages.inbox'))
    
    if request.method == 'POST':
        body = request.form.get('body')
        
        message = Message(
            sender_id=current_user.id,
            recipient_id=original.sender_id,
            subject=f"Re: {original.subject}",
            body=body,
            parent_id=original.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        
        flash('Reply sent successfully.', 'success')
        return redirect(url_for('messages.inbox'))
        
    return render_template('messages/reply_message.html', original=original)