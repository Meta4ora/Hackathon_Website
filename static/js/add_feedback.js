document.addEventListener('DOMContentLoaded', function() {
    // Check if showFeedbackModal is defined (passed from Django template)
    if (typeof showFeedbackModal !== 'undefined' && showFeedbackModal) {
        var feedbackModal = new bootstrap.Modal(document.getElementById('feedbackSuccessModal'));
        feedbackModal.show();
    }
});