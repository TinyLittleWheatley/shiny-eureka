let currentId = null;

async function loadNext() {
    const res = await fetch("/next");
    const data = await res.json();

    if (data.done) {
        alert("All done!");
        return;
    }

    currentId = data.id;
    document.getElementById("audio").src = data.audio_url;
    document.getElementById("labelInput").value = data.label;
}

async function submit() {
    const label = document.getElementById("labelInput").value;

    await fetch("/submit", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            id: currentId,
            label: label
        })
    });

    loadNext();
}

async function skipSample() {
    await fetch("/skip", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            id: currentId,
        })
    });

    loadNext();
}

const originalFetch = window.fetch;

window.fetch = async function(...args) {
    const response = await originalFetch(...args);

    // Read progress header
    const progress = response.headers.get("X-Progress");
    if (progress !== null) {
        updateProgress(parseFloat(progress));
    }

    return response;
};

function updateProgress(percent) {
    const bar = document.getElementById("progressBar");
    const text = document.getElementById("progressText");
    if (bar && text) {
        bar.style.width = percent + "%";
        bar.setAttribute("aria-valuenow", percent);
        text.textContent = percent + "%";
    }
}

loadNext();
