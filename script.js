const video = document.getElementById("introVideo");
const source = document.getElementById("videoSource");

/* ==========================================
   LOAD CORRECT VIDEO
========================================== */

function loadCorrectVideo() {

    const isMobile = window.innerWidth <= 768;

    const newSource = isMobile
        ? "DreamXV Intro Video_Mobile.mp4"
        : "DreamXV Intro Video_Desktop.mp4";

    if (decodeURIComponent(source.src).includes(newSource)) {
        return;
    }

    source.src = newSource;

    video.load();

    video.play().catch(() => {});
}

/* ==========================================
   INITIAL LOAD
========================================== */

window.addEventListener("load", () => {

    loadCorrectVideo();

});

/* ==========================================
   SCREEN ROTATION
========================================== */

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

/* ==========================================
   FORCE AUTOPLAY
========================================== */

video.play().catch(() => {});