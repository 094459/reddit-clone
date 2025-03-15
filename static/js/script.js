// Document ready function
$(document).ready(function() {
    // Toggle reply form visibility
    $('.reply-button').click(function() {
        var commentId = $(this).data('comment-id');
        $('#reply-form-' + commentId).toggle();
    });
    
    // Cancel reply
    $('.cancel-reply').click(function() {
        var commentId = $(this).data('comment-id');
        $('#reply-form-' + commentId).hide();
    });
    
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-toggle="popover"]').popover();
    
    // Auto-resize textareas
    $('textarea').each(function() {
        this.setAttribute('style', 'height:' + (this.scrollHeight) + 'px;overflow-y:hidden;');
    }).on('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Confirm delete actions
    $('.confirm-delete').click(function(e) {
        if (!confirm('Are you sure you want to delete this?')) {
            e.preventDefault();
        }
    });
    
    // Handle vote buttons with AJAX
    $('.vote-button').click(function(e) {
        if ($(this).hasClass('ajax-vote')) {
            e.preventDefault();
            
            var form = $(this).closest('form');
            var url = form.attr('action');
            var voteType = $(this).siblings('input[name="vote"]').val();
            var csrfToken = form.find('input[name="csrf_token"]').val();
            
            $.ajax({
                url: url,
                type: 'POST',
                data: {
                    'vote': voteType,
                    'csrf_token': csrfToken
                },
                success: function(response) {
                    if (response.success) {
                        // Update score display
                        form.siblings('.score').text(response.score);
                        
                        // Toggle vote button styles
                        if (voteType === 'up') {
                            form.find('.upvote').toggleClass('upvoted');
                            form.siblings('form').find('.downvote').removeClass('downvoted');
                        } else {
                            form.find('.downvote').toggleClass('downvoted');
                            form.siblings('form').find('.upvote').removeClass('upvoted');
                        }
                    }
                }
            });
        }
    });
});