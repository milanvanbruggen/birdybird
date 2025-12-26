document.addEventListener('DOMContentLoaded', () => {
    const listElement = document.getElementById('detections-list');
    let knownIds = new Set();

    function fetchDetections() {
        fetch('/api/detections')
            .then(response => response.json())
            .then(data => {
                if (data.length === 0 && knownIds.size === 0) {
                    listElement.innerHTML = '<div class="loading-spinner">Waiting for birds...</div>';
                    return;
                }

                // Reverse to show newest on top if API sends newest first we good
                // Usually API sends DESC sort, so first item is newest.

                // We want to update the list without full re-render if possible, or just re-render all for simplicity
                // For a smooth experience, let's just re-render sorted 

                const newIds = new Set(data.map(d => d.id));

                // If ids changed, render
                // Simple check: join IDs string
                const currentIdSig = Array.from(knownIds).sort().join(',');
                const newIdSig = data.map(d => d.id).sort().join(',');

                if (currentIdSig !== newIdSig || knownIds.size === 0) {
                    renderList(data);
                    knownIds = newIds;
                }
            })
            .catch(err => console.error('Error fetching detections:', err));
    }

    function renderList(detections) {
        listElement.innerHTML = '';

        detections.forEach(detection => {
            const card = document.createElement('div');
            card.className = 'detection-card';

            // Format timestamp
            const date = new Date(detection.timestamp);
            const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            card.innerHTML = `
                <img src="${detection.image_path}" alt="${detection.species}" class="bird-thumb">
                <div class="bird-info">
                    <div class="bird-species">${detection.species}</div>
                    <div class="bird-meta">
                        <span><i class="far fa-clock"></i> ${timeStr}</span> &bull; 
                        <span>${Math.round(detection.confidence * 100)}% Match</span>
                    </div>
                    ${detection.interesting_fact ? `<div class="bird-fact">${detection.interesting_fact}</div>` : ''}
                </div>
            `;

            listElement.appendChild(card);
        });
    }

    // Camera Selection Logic
    const cameraSelect = document.getElementById('camera-select');
    const videoFeed = document.querySelector('.live-feed');

    function loadCameras() {
        fetch('/api/cameras')
            .then(res => res.json())
            .then(cameras => {
                cameraSelect.innerHTML = '';
                cameras.forEach(cam => {
                    const option = document.createElement('option');
                    option.value = cam.id;
                    option.textContent = cam.name;
                    cameraSelect.appendChild(option);
                });

                // Select first one by default if not set
                if (cameras.length > 0) {
                    // Optionally check local storage for preference
                } else {
                    const option = document.createElement('option');
                    option.textContent = "No cameras found";
                    cameraSelect.appendChild(option);
                }
            });
    }

    cameraSelect.addEventListener('change', (e) => {
        const camId = e.target.value;
        fetch(`/api/cameras/${camId}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                console.log(data.message);

                // Force reload of image source to restart stream connection
                // We strip existing params and add a timestamp to bypass browser cache
                const currentSrc = videoFeed.src.split('?')[0];
                videoFeed.src = '';

                // Slight delay to allow backend to switch and browser to clear old connection
                setTimeout(() => {
                    videoFeed.src = `${currentSrc}?t=${new Date().getTime()}`;
                }, 200);
            });
    });

    const debugToggle = document.getElementById('debug-mode');
    debugToggle.addEventListener('change', (e) => {
        const enabled = e.target.checked;
        fetch(`/api/debug/${enabled}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => console.log("Debug mode:", data.debug_mode));
    });

    const clearBtn = document.getElementById('clear-log-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (confirm("Are you sure you want to clear all detection logs and images?")) {
                fetch('/api/detections', { method: 'DELETE' })
                    .then(res => res.json())
                    .then(data => {
                        console.log(data.message);
                        fetchDetections(); // Refresh empty list
                    });
            }
        });
    }

    loadCameras();

    // Poll every 3 seconds
    fetchDetections();
    setInterval(fetchDetections, 3000);
    // Poll for processing status
    const statusText = document.getElementById('status-text');

    setInterval(() => {
        fetch('/api/status')
            .then(res => res.json())
            .then(data => {
                if (data.processing) {
                    statusText.textContent = "AI Analysis in progress...";
                    statusText.style.color = "var(--accent)";
                    statusText.style.fontWeight = "bold";
                } else if (data.cooldown > 0) {
                    statusText.textContent = `Cooldown: ${Math.ceil(data.cooldown)}s`;
                    statusText.style.color = "var(--text-secondary)";
                    statusText.style.fontWeight = "normal";
                } else {
                    statusText.textContent = "Monitoring for movement...";
                    statusText.style.color = "var(--text-primary)";
                    statusText.style.fontWeight = "normal";
                }
            })
            .catch(err => console.log("Status poll error", err));
    }, 1000);
});
