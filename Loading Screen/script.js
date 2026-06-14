const video = document.getElementById("introVideo");

/* ==========================================
   LOAD CORRECT VIDEO
========================================== */

function loadCorrectVideo() {
    const isMobile = window.innerWidth <= 768;
    const newSource = isMobile
        ? "DreamXV Intro Video_Mobile.mp4"
        : "DreamXV Intro Video_Desktop.mp4";

    // Compare against video.src directly for accuracy
    if (video.src && decodeURIComponent(video.src).includes(newSource)) {
        return;
    }

    video.src = newSource;
    video.load();
    video.play().catch((err) => {
        console.log("Autoplay blocked or load issue: ", err);
    });
}

/* ==========================================
   INITIAL LOAD & EVENTS
========================================== */

// Run immediately to start buffering/playing
loadCorrectVideo();

// Run on DOMContentLoaded as a backup
document.addEventListener("DOMContentLoaded", () => {
    loadCorrectVideo();
});

// Run on window resize / orientation change
window.addEventListener("resize", () => {
    loadCorrectVideo();
});

/* ==========================================
   DISABLE RIGHT CLICK
========================================== */

document.addEventListener("contextmenu", e => {
    e.preventDefault();
});

/* ==========================================
   AUTOPLAY FALLBACK FOR USER INTERACTION
========================================== */

const playOnInteraction = () => {
    if (video.paused) {
        video.play().catch(() => {});
    }
    document.removeEventListener("click", playOnInteraction);
    document.removeEventListener("touchstart", playOnInteraction);
};
document.addEventListener("click", playOnInteraction);
document.addEventListener("touchstart", playOnInteraction);

/* ==========================================
   TRANSITION TO MAIN SITE
========================================== */

let transitioned = false;

function transitionToMainSite() {
    if (transitioned) return;
    transitioned = true;

    const container = document.querySelector(".loading-container");
    const mainContent = document.getElementById("main-content");

    if (container) {
        container.classList.add("fade-out");
        setTimeout(() => {
            container.style.display = "none";
        }, 1000);
    }

    if (mainContent) {
        mainContent.classList.add("visible");
    }
}

// Transition when video ends
video.addEventListener("ended", () => {
    transitionToMainSite();
});

// Fallback: Transition after 10s (matching the loading progress bar)
setTimeout(() => {
    transitionToMainSite();
}, 10000);