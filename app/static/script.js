let currentId = null;

async function loadNext() {
    const res = await fetch("/next");
    const data = await res.json();

    if (data.done) {
        alert("All done!");
        return;
    }

    currentId = data.id;

    const audioBlob = new Blob(
        [new Float32Array(data.audio)],
        { type: "audio/wav" }
    );

    const url = URL.createObjectURL(audioBlob);
    document.getElementById("audio").src = url;
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

loadNext();
