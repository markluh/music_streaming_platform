document.addEventListener('DOMContentLoaded', (event) => {
    const commonPlayer = document.getElementById('common-player');
    const playerTitle = document.getElementById('player-title');
    const uploaderAvatar = document.getElementById('uploader-avatar');
    const uploaderAvatarWrapper = document.querySelector('.uploader-avatar-wrapper');
    const loopBtn = document.getElementById('loop-btn');
    const rewindBtn = document.getElementById('rewind-btn');
    const forwardBtn = document.getElementById('forward-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const playerContainer = document.querySelector('.common-player-container');
    const playerCardContainer = document.querySelector('.player-card-container');
    const isUserAuthenticated = document.getElementById('user-info').dataset.authenticated === 'True';
    
    const mainContent = document.getElementById('main-content');
    const csrfToken = document.querySelector('#csrf-form input[name="csrfmiddlewaretoken"]').value;

    let currentPlayingIndex = -1;
    let loopMode = 'no-loop';
    let allSongs = [];
    
    const getRandomColor = () => {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    };

    const updatePlayerUI = (index) => {
        if (index === -1) {
            resetPlayer();
            return;
        }
        const song = allSongs[index];
        if (playerTitle) {
            playerTitle.innerHTML = `<strong>${song.title}</strong> by ${song.artist}`;
        }
        if (playerContainer) {
            playerContainer.classList.add('active');
        }
        if (uploaderAvatar && uploaderAvatarWrapper) {
            uploaderAvatar.src = song.uploaderPic; 
            uploaderAvatarWrapper.style.backgroundColor = getRandomColor();
        }
        if (prevBtn && nextBtn) {
            if (loopMode === 'loop-all' || allSongs.length <= 1) {
                prevBtn.disabled = false;
                nextBtn.disabled = false;
            } else {
                prevBtn.disabled = index === 0;
                nextBtn.disabled = index === allSongs.length - 1;
            }
        }
    };

    const playSong = (index) => {
        if (index >= 0 && index < allSongs.length) {
            const song = allSongs[index];
            if (song.src) {
                commonPlayer.src = song.src;
                commonPlayer.play().catch(error => console.error("Autoplay failed:", error));
                currentPlayingIndex = index;
                updatePlayerUI(currentPlayingIndex);
                playerCardContainer.style.backgroundColor = getRandomColor();
                savePlayerState();
            } else {
                 console.error("Attempted to play a song with an undefined source.");
            }
        }
    };

    const resetPlayer = () => {
        commonPlayer.pause();
        commonPlayer.src = '';
        if (playerTitle) playerTitle.textContent = 'No song playing';
        if (playerContainer) playerContainer.classList.remove('active');
        if (uploaderAvatar && uploaderAvatarWrapper) {
            uploaderAvatar.src = "/static/images/default_profile_pic.png";
            uploaderAvatarWrapper.style.backgroundColor = 'transparent'; 
        }
        if (playerCardContainer) {
            playerCardContainer.style.backgroundColor = '';
        }
        localStorage.removeItem('playerState');
        currentPlayingIndex = -1;
    };

    const savePlayerState = () => {
        if (commonPlayer.src && currentPlayingIndex !== -1) {
            const song = allSongs[currentPlayingIndex];
            const state = {
                src: song.src,
                title: song.title,
                artist: song.artist,
                uploaderPic: song.uploaderPic,
                position: commonPlayer.currentTime,
                loopMode: loopMode
            };
            localStorage.setItem('playerState', JSON.stringify(state));
        } else {
            localStorage.removeItem('playerState');
        }
    };

    const loadPlayerState = () => {
        const storedState = localStorage.getItem('playerState');
        if (storedState && isUserAuthenticated) {
            try {
                const state = JSON.parse(storedState);
                if (state.src) {
                    commonPlayer.src = state.src;
                    commonPlayer.currentTime = state.position || 0;
                    loopMode = state.loopMode || 'no-loop';
                    
                    if (playerTitle) playerTitle.innerHTML = `<strong>${state.title}</strong> by ${state.artist}`;
                    if (playerContainer) playerContainer.classList.add('active');
                    if (uploaderAvatar) uploaderAvatar.src = state.uploaderPic;
                    if (uploaderAvatarWrapper) uploaderAvatarWrapper.style.backgroundColor = getRandomColor();
                    
                    if (loopBtn) loopBtn.textContent = (loopMode === 'loop-one') ? 'Loop One' : (loopMode === 'loop-all') ? 'Loop All' : 'No Loop';
                    commonPlayer.loop = (loopMode === 'loop-one');
                    
                    currentPlayingIndex = allSongs.findIndex(song => song.src === state.src);

                    const resumePlayback = () => {
                        commonPlayer.play().catch(error => console.error("Autoplay failed:", error));
                        commonPlayer.removeEventListener('loadedmetadata', resumePlayback);
                    };
                    
                    if (commonPlayer.readyState >= 2) {
                        resumePlayback();
                    } else {
                        commonPlayer.addEventListener('loadedmetadata', resumePlayback);
                    }
                } else {
                    resetPlayer();
                }
            } catch (e) {
                console.error("Failed to parse player state from local storage:", e);
                localStorage.removeItem('playerState');
                resetPlayer();
            }
        } else {
            resetPlayer();
        }
    };

    if (!isUserAuthenticated) {
        resetPlayer();
    }
    
    // --- CONSOLIDATED NAVIGATION AND FORM HANDLING ---

    // Function to load a page via AJAX
    const loadPage = (url) => {
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text();
            })
            .then(html => {
                mainContent.innerHTML = html;
                window.history.pushState({ path: url }, '', url);
                initContentListeners();
                
                // Set the current list of songs after new content is loaded
                const newlyLoadedPlayButtons = mainContent.querySelectorAll('.play-btn');
                allSongs = Array.from(newlyLoadedPlayButtons).map(button => ({
                    src: button.getAttribute('data-src'),
                    title: button.getAttribute('data-title'),
                    artist: button.getAttribute('data-artist'),
                    uploaderPic: button.getAttribute('data-uploader-pic') 
                }));
                // Try to restore player state after the song list is set
                loadPlayerState(); 
            })
            .catch(error => console.error('Error loading page:', error));
    };

    // Function to handle Like/Dislike actions via AJAX
    const handleLikeDislike = (e) => {
        e.preventDefault();
        if (!isUserAuthenticated) {
            alert('You must be logged in to like or dislike music.');
            return;
        }

        const url = e.currentTarget.getAttribute('href');
        const parentContainer = e.currentTarget.closest('.like-dislike-container');

        fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(html => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const newContent = tempDiv.querySelector('.like-dislike-container').innerHTML;
            parentContainer.innerHTML = newContent;
            attachLikeDislikeListeners();
        })
        .catch(error => console.error('Error:', error));
    };

    // Function to handle comment form submissions via AJAX
    const handleCommentForm = (e) => {
        e.preventDefault();
        if (!isUserAuthenticated) {
            alert('You must be logged in to post a comment.');
            return;
        }

        const form = e.currentTarget;
        const formData = new FormData(form);
        const url = form.action;
        const musicItem = form.closest('.music-item');
        const commentList = musicItem.querySelector('.comment-list');
        const commentCountSpan = musicItem.querySelector('.comment-count');
        const noComments = musicItem.querySelector('.no-comments');

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const newCommentHtml = `<div class="comment-item">
                                            <div class="comment-item-header">
                                                <span class="comment-author">${data.username}</span>
                                                <span class="comment-date">${data.date}</span>
                                            </div>
                                            <p>${data.content}</p>
                                        </div>`;
                
                commentList.insertAdjacentHTML('beforeend', newCommentHtml);
                commentCountSpan.textContent = data.comments_count;
                
                if (noComments) {
                    noComments.remove();
                }
                form.querySelector('input[name="comment_text"]').value = '';
            } else {
                console.error('Comment submission failed:', data.error);
            }
        })
        .catch(error => console.error('Error submitting comment:', error));
    };

    const handleSearchForm = (e) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        
        fetch(e.currentTarget.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            const musicResultsContainer = document.getElementById('music-results-container');
            const userResultsContainer = document.getElementById('user-results-container');
            
            if (musicResultsContainer) {
                musicResultsContainer.innerHTML = data.music_html;
            }
            if (userResultsContainer) {
                userResultsContainer.innerHTML = data.user_html;
            }
            
            initContentListeners();
        })
        .catch(error => console.error('Error during search:', error));
    };

    // Attach listeners to all Like/Dislike buttons
    const attachLikeDislikeListeners = () => {
        document.querySelectorAll('.ajax-like-dislike').forEach(button => {
            button.removeEventListener('click', handleLikeDislike);
            button.addEventListener('click', handleLikeDislike);
        });
    };

    // Attach listeners to all comment forms
    const attachCommentFormListeners = () => {
        document.querySelectorAll('.ajax-comment-form').forEach(form => {
            form.removeEventListener('submit', handleCommentForm);
            form.addEventListener('submit', handleCommentForm);
        });
    };

    // Attach listeners to all AJAX links
    const attachAjaxListeners = () => {
        document.querySelectorAll('.ajax-link').forEach(link => {
            link.removeEventListener('click', handleAjaxLink);
            link.addEventListener('click', handleAjaxLink);
        });
    };

    const handleAjaxLink = (event) => {
        event.preventDefault();
        const url = event.currentTarget.getAttribute('href');
        if (url.includes('/login/') || url.includes('/signup/')) {
            playerContainer.classList.add('hidden-on-login');
        } else {
            playerContainer.classList.remove('hidden-on-login');
        }
        loadPage(url);
    };

    const initContentListeners = () => {
        attachAjaxListeners();
        attachLikeDislikeListeners();
        attachCommentFormListeners();
        
        // Handle search form
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
            searchForm.removeEventListener('submit', handleSearchForm);
            searchForm.addEventListener('submit', handleSearchForm);
        }

        // Re-attach play button listeners for new content
        const newlyLoadedPlayButtons = mainContent.querySelectorAll('.play-btn');
        allSongs = Array.from(newlyLoadedPlayButtons).map(button => ({
            src: button.getAttribute('data-src'),
            title: button.getAttribute('data-title'),
            artist: button.getAttribute('data-artist'),
            uploaderPic: button.getAttribute('data-uploader-pic') 
        }));
        
        newlyLoadedPlayButtons.forEach((button) => {
            button.removeEventListener('click', handlePlayButton);
            button.addEventListener('click', handlePlayButton);
        });
    };
    
    const handlePlayButton = function(e) {
        e.preventDefault();
        const songSrc = this.getAttribute('data-src');
        const newIndex = allSongs.findIndex(song => song.src === songSrc);
        if (commonPlayer.src !== songSrc || commonPlayer.paused) {
            playSong(newIndex);
        } else {
            commonPlayer.pause();
        }
    };
    
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            if (currentPlayingIndex !== -1) {
                let nextIndex;
                if (currentPlayingIndex < allSongs.length - 1) {
                    nextIndex = currentPlayingIndex + 1;
                } else if (loopMode === 'loop-all') {
                    nextIndex = 0;
                } else {
                    return;
                }
                playSong(nextIndex);
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            if (currentPlayingIndex !== -1) {
                let prevIndex;
                if (currentPlayingIndex > 0) {
                    prevIndex = currentPlayingIndex - 1;
                } else if (currentPlayingIndex === 0 && loopMode === 'loop-all') {
                    prevIndex = allSongs.length - 1;
                } else {
                    return;
                }
                playSong(prevIndex);
            }
        });
    }

    if (loopBtn) {
        loopBtn.addEventListener('click', () => {
            if (loopMode === 'no-loop') {
                loopMode = 'loop-all';
                loopBtn.textContent = 'Loop All';
                commonPlayer.loop = false;
            } else if (loopMode === 'loop-all') {
                loopMode = 'loop-one';
                loopBtn.textContent = 'Loop One';
                commonPlayer.loop = true;
            } else {
                loopMode = 'no-loop';
                loopBtn.textContent = 'No Loop';
                commonPlayer.loop = false;
            }
            updatePlayerUI(currentPlayingIndex);
            savePlayerState();
        });
    }

    if (rewindBtn) {
        rewindBtn.addEventListener('click', () => {
            if (commonPlayer.src) {
                commonPlayer.currentTime = Math.max(0, commonPlayer.currentTime - 10);
                savePlayerState();
            }
        });
    }

    if (forwardBtn) {
        forwardBtn.addEventListener('click', () => {
            if (commonPlayer.src) {
                commonPlayer.currentTime = commonPlayer.currentTime + 10;
                savePlayerState();
            }
        });
    }
    
    if (commonPlayer) {
        commonPlayer.addEventListener('timeupdate', () => {
            clearTimeout(commonPlayer.saveTimeout);
            commonPlayer.saveTimeout = setTimeout(savePlayerState, 1000);
        });
    }

    if (commonPlayer) {
        commonPlayer.addEventListener('ended', () => {
            if (loopMode === 'loop-one') {
                commonPlayer.play();
                return;
            }
            let nextIndex = currentPlayingIndex + 1;
            if (nextIndex < allSongs.length) {
                playSong(nextIndex);
            } else if (loopMode === 'loop-all') {
                playSong(0);
            } else {
                commonPlayer.pause();
                if (playerTitle) playerTitle.textContent = 'No song playing';
                if (playerContainer) playerContainer.classList.remove('active');
                localStorage.removeItem('playerState');
                currentPlayingIndex = -1;
            }
        });
    }

    window.addEventListener('beforeunload', savePlayerState);
    
    // Popstate event listener for browser back/forward buttons
    window.addEventListener('popstate', (e) => {
        loadPage(document.location.href);
    });

    // Initial setup
    initContentListeners();
});