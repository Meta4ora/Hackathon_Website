// Dynamically show/hide participant cards based on the number of participants
document.addEventListener('DOMContentLoaded', function() {
    var showFeedbackModal = {{ show_feedback_modal|yesno:"true,false" }};
    var showTeamModal = {{ show_team_modal|yesno:"true,false" }};

    document.getElementById('num_participants').addEventListener('change', function() {
        const numParticipants = parseInt(this.value);
        const totalCards = 4; // We have 4 possible cards (for participants 2 to 5)

        // Hide all cards first
        for (let i = 1; i <= totalCards; i++) {
            const card = document.getElementById(`participant-card-${i}`);
            card.style.display = 'none';
            // Clear input fields when hiding
            card.querySelectorAll('input').forEach(input => input.value = '');
        }

        // Show the appropriate number of cards (numParticipants - 1, since captain is included)
        if (numParticipants > 1) {
            const cardsToShow = numParticipants - 1;
            for (let i = 1; i <= cardsToShow; i++) {
                document.getElementById(`participant-card-${i}`).style.display = 'block';
            }
        }
    });

    // Automatically trigger modal if showFeedbackModal or showTeamModal is true
    if (showFeedbackModal) {
        new bootstrap.Modal(document.getElementById('feedbackSuccessModal')).show();
    }
    if (showTeamModal) {
        new bootstrap.Modal(document.getElementById('teamSuccessModal')).show();
    }
});