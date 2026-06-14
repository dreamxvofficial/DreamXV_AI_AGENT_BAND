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
   KEEP FINAL FRAME
========================================== */

video.addEventListener("ended", () => {

    video.pause();

    video.currentTime =
        Math.max(
            0,
            video.duration - 0.05
        );

});

/* ==========================================
   FORCE AUTOPLAY
========================================== */

video.play().catch(() => {});