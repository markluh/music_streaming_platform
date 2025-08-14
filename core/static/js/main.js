document.addEventListener('DOMContentLoaded', (event) => {
    const commonPlayer = document.getElementById('common-player');
    const playerTitle = document.getElementById('player-title');
    const playButtons = document.querySelectorAll('.play-btn');

    console.log(`Found ${playButtons.length} play buttons on the page.`);

    let currentPlayingIndex = -1;

    playButtons.forEach((button, index) => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const songSrc = this.getAttribute('data-src');
            const songTitle = this.getAttribute('data-title');
            const songArtist = this.getAttribute('data-artist');

            if (commonPlayer.src !== songSrc) {
                commonPlayer.src = songSrc;
                playerTitle.textContent = `${songTitle} by ${songArtist}`;
                
                commonPlayer.play().catch(error => {
                    console.error("Autoplay failed:", error);
                });
                
                currentPlayingIndex = index;
                console.log(`Now playing song at index: ${currentPlayingIndex}`);
            } else {
                if (commonPlayer.paused) {
                    commonPlayer.play();
                } else {
                    commonPlayer.pause();
                }
            }
        });
    });

    commonPlayer.addEventListener('ended', () => {
        console.log("Audio player finished current song.");

        currentPlayingIndex++;

        // Check if the next song exists before trying to play it
        if (currentPlayingIndex < playButtons.length) {
            console.log(`Attempting to play next song at index: ${currentPlayingIndex}`);
            playButtons[currentPlayingIndex].click();
        } else {
            console.log("Reached end of playlist. Looping back to the first song.");
            currentPlayingIndex = 0;
            playButtons[currentPlayingIndex].click();
        }
    });
});