document.addEventListener("DOMContentLoaded", () => {
    const feedbackCards = document.querySelectorAll('.feedback-card');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const initialBatch = 8;
    const batchSize = 4;
    let shown = 0;

    function showNextBatch(size) {
        let delay = 0;
        for (let i = shown; i < shown + size && i < feedbackCards.length; i++) {
            const card = feedbackCards[i];
            setTimeout(() => {
                card.style.display = 'block';
                requestAnimationFrame(() => {
                    card.classList.add('visible');
                });
            }, delay);
            delay += 100; // Задержка между карточками
        }
        shown += size;

        if (shown >= feedbackCards.length && loadMoreBtn) {
            loadMoreBtn.classList.add('fade-out');
            setTimeout(() => loadMoreBtn.style.display = 'none', 500);
        }
    }

    showNextBatch(initialBatch);

    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => showNextBatch(batchSize));
    }
});
