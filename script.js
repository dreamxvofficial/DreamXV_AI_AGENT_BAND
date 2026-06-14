const video = document.getElementById("introVideo");

/* ==========================================
   LOAD CORRECT VIDEO
========================================== */

function loadCorrectVideo() {
    const isMobile = window.innerWidth <= 768;
    const newSource = isMobile
        ? "DreamXV Intro Video_Mobile.mp4"
        : "DreamXV Intro Video_Desktop.mp4";

    if (video && video.src && decodeURIComponent(video.src).includes(newSource)) {
        return;
    }

    if (video) {
        video.src = newSource;
        video.load();
        video.play().catch((err) => {
            console.log("Autoplay blocked or load issue: ", err);
        });
    }
}

/* ==========================================
   INITIAL LOAD & EVENTS
========================================== */

loadCorrectVideo();

document.addEventListener("DOMContentLoaded", () => {
    loadCorrectVideo();
    initApp();
});

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
    if (video && video.paused) {
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
        mainContent.classList.remove("hidden");
        // Check session and route to the correct screen
        const user = localStorage.getItem("dreamxv_user");
        const onboarded = localStorage.getItem("dreamxv_onboarded");
        
        if (user && onboarded) {
            showView("dashboard-view");
        } else {
            showView("landing-view");
        }
    }
}

// Transition when video ends
if (video) {
    video.addEventListener("ended", () => {
        transitionToMainSite();
    });
}

// Fallback: Transition after 10s
setTimeout(() => {
    transitionToMainSite();
}, 10000);

/* ==========================================
   VIEW SWITCHER / NAVIGATION
========================================== */

function showView(viewId) {
    const panels = document.querySelectorAll(".view-panel");
    panels.forEach(panel => {
        panel.classList.add("hidden");
        panel.style.opacity = "0";
    });

    const activePanel = document.getElementById(viewId);
    if (activePanel) {
        activePanel.classList.remove("hidden");
        // Force reflow
        activePanel.offsetHeight;
        activePanel.style.opacity = "1";
    }

    // Scroll to top on switch
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ==========================================
   APPLICATION LOGIC (AUTH, ONBOARDING, DASHBOARD)
========================================== */

function initApp() {
    // 1. Landing Navigation to Auth
    const launchBtn = document.getElementById("launch-studio-btn");
    const launchTriggers = document.querySelectorAll(".launch-studio-trigger");
    
    const handleLaunch = (e) => {
        if (e) e.preventDefault();
        const user = localStorage.getItem("dreamxv_user");
        const onboarded = localStorage.getItem("dreamxv_onboarded");

        if (user && onboarded) {
            showView("dashboard-view");
            initDashboard();
        } else if (user) {
            startOnboarding();
        } else {
            showView("auth-view");
        }
    };

    if (launchBtn) launchBtn.addEventListener("click", handleLaunch);
    launchTriggers.forEach(btn => btn.addEventListener("click", handleLaunch));

    // 2. Google OAuth Mock Flow
    const googleBtn = document.getElementById("google-signin-btn");
    const accountChooser = document.getElementById("account-chooser");
    const toggleCustomBtn = document.getElementById("toggle-custom-auth-btn");
    const customForm = document.getElementById("custom-account-form");
    const customSubmitBtn = document.getElementById("custom-signin-submit");

    if (googleBtn) {
        googleBtn.addEventListener("click", () => {
            accountChooser.classList.remove("hidden");
        });
    }

    if (toggleCustomBtn) {
        toggleCustomBtn.addEventListener("click", () => {
            customForm.classList.toggle("hidden");
        });
    }

    // Handle Mock Account Selection
    const accountItems = document.querySelectorAll(".account-item");
    accountItems.forEach(item => {
        item.addEventListener("click", () => {
            const name = item.getAttribute("data-name");
            const email = item.getAttribute("data-email");
            const avatar = item.getAttribute("data-pic");
            saveUser(name, email, avatar);
        });
    });

    // Handle Custom Account Form Submission
    if (customSubmitBtn) {
        customSubmitBtn.addEventListener("click", (e) => {
            e.preventDefault();
            const nameInput = document.getElementById("custom-name");
            const emailInput = document.getElementById("custom-email");

            if (nameInput.value && emailInput.value) {
                const seedName = encodeURIComponent(nameInput.value.trim());
                const avatar = `https://api.dicebear.com/7.x/initials/svg?seed=${seedName}&backgroundColor=c47d1a&textColor=0c1a2e`;
                saveUser(nameInput.value.trim(), emailInput.value.trim(), avatar);
            } else {
                alert("Please fill in both Name and Email.");
            }
        });
    }

    // 3. Onboarding Quiz Interaction
    const onboardWelcomeBtn = document.getElementById("start-onboard-btn");
    const onboardWelcome = document.getElementById("onboard-welcome");
    const onboardQuiz = document.getElementById("onboard-quiz");
    const nextBtn = document.getElementById("next-question-btn");
    const prevBtn = document.getElementById("prev-question-btn");

    let currentStep = 1;
    const totalSteps = 5;
    const quizAnswers = {};

    if (onboardWelcomeBtn) {
        onboardWelcomeBtn.addEventListener("click", () => {
            onboardWelcome.classList.add("hidden");
            onboardQuiz.classList.remove("hidden");
            updateQuizUI();
        });
    }

    function startOnboarding() {
        const user = JSON.parse(localStorage.getItem("dreamxv_user"));
        const greetText = document.getElementById("onboard-greet");
        if (greetText && user) {
            greetText.textContent = `Welcome, ${user.name}.`;
        }
        showView("onboarding-view");
        onboardWelcome.classList.remove("hidden");
        onboardQuiz.classList.add("hidden");
        currentStep = 1;
        updateQuizUI();
    }

    // Enable Next button when choices are made
    const quizContainers = document.querySelectorAll(".quiz-question");
    quizContainers.forEach(q => {
        // Handle radio buttons
        const radios = q.querySelectorAll('input[type="radio"]');
        radios.forEach(radio => {
            radio.addEventListener("change", () => {
                quizAnswers[`q${currentStep}`] = radio.value;
                nextBtn.disabled = false;
            });
        });

        // Handle checkboxes (multi-select for Q3)
        const checkboxes = q.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            cb.addEventListener("change", () => {
                const selectedCbs = Array.from(q.querySelectorAll('input[type="checkbox"]:checked')).map(c => c.value);
                if (selectedCbs.length > 0) {
                    quizAnswers[`q${currentStep}`] = selectedCbs;
                    nextBtn.disabled = false;
                } else {
                    delete quizAnswers[`q${currentStep}`];
                    nextBtn.disabled = true;
                }
            });
        });
    });

    if (nextBtn) {
        nextBtn.addEventListener("click", () => {
            if (currentStep < totalSteps) {
                currentStep++;
                updateQuizUI();
            } else {
                // Save onboarding choices and complete
                localStorage.setItem("dreamxv_onboarding_data", JSON.stringify(quizAnswers));
                localStorage.setItem("dreamxv_onboarded", "true");
                showView("dashboard-view");
                initDashboard();
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener("click", () => {
            if (currentStep > 1) {
                currentStep--;
                updateQuizUI();
            }
        });
    }

    function updateQuizUI() {
        // Toggle questions
        quizContainers.forEach(q => {
            const stepNum = parseInt(q.getAttribute("data-step"));
            if (stepNum === currentStep) {
                q.classList.remove("hidden");
                q.classList.add("active");
            } else {
                q.classList.add("hidden");
                q.classList.remove("active");
            }
        });

        // Toggle back button
        if (currentStep === 1) {
            prevBtn.classList.add("hidden");
        } else {
            prevBtn.classList.remove("hidden");
        }

        // Change Next button text at final step
        if (currentStep === totalSteps) {
            nextBtn.textContent = "FINISH";
        } else {
            nextBtn.textContent = "NEXT";
        }

        // Update progress indicators
        const stepIndicator = document.getElementById("progress-step-indicator");
        const progressBar = document.getElementById("onboard-progress-bar");
        if (stepIndicator) stepIndicator.textContent = `Question ${currentStep} of ${totalSteps}`;
        if (progressBar) progressBar.style.width = `${(currentStep / totalSteps) * 100}%`;

        // Check if current step has an answer saved to enable/disable Next button
        const currentAnswer = quizAnswers[`q${currentStep}`];
        if (currentAnswer && (Array.isArray(currentAnswer) ? currentAnswer.length > 0 : true)) {
            nextBtn.disabled = false;
        } else {
            nextBtn.disabled = true;
        }
    }

    // Save User Session helper
    function saveUser(name, email, avatar) {
        const user = {
            name: name,
            email: email,
            avatar: avatar,
            created: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
        };
        localStorage.setItem("dreamxv_user", JSON.stringify(user));
        startOnboarding();
    }

    // 4. Dashboard Controls
    const profileTrigger = document.getElementById("profile-trigger");
    const profileDropdown = document.getElementById("profile-dropdown");
    const logoutBtn = document.getElementById("logout-btn");

    if (profileTrigger && profileDropdown) {
        profileTrigger.addEventListener("click", (e) => {
            e.stopPropagation();
            profileDropdown.classList.toggle("hidden");
        });

        document.addEventListener("click", () => {
            profileDropdown.classList.add("hidden");
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            localStorage.removeItem("dreamxv_user");
            localStorage.removeItem("dreamxv_onboarded");
            localStorage.removeItem("dreamxv_onboarding_data");
            showView("landing-view");
        });
    }

    // Initial Dashboard call if user is already logged in
    const user = localStorage.getItem("dreamxv_user");
    const onboarded = localStorage.getItem("dreamxv_onboarded");
    if (user && onboarded) {
        initDashboard();
    }
}

// 5. Initialize Dashboard Data
function initDashboard() {
    const user = JSON.parse(localStorage.getItem("dreamxv_user"));
    const onboardData = JSON.parse(localStorage.getItem("dreamxv_onboarding_data"));

    if (!user) return;

    // Update Avatar & Names
    const navAvatar = document.getElementById("nav-user-avatar-placeholder");
    const navName = document.getElementById("nav-user-name");
    const dropEmail = document.getElementById("dropdown-user-email");
    const dropCreated = document.getElementById("dropdown-created-date");
    const dbGreeting = document.getElementById("dashboard-greeting");
    const dbAvatar = document.getElementById("dashboard-user-avatar-placeholder");

    // Assign initials/pics
    const initials = user.name.charAt(0).toUpperCase();
    if (navAvatar) {
        navAvatar.textContent = initials;
        navAvatar.style.background = "var(--lunar-gold)";
        navAvatar.style.color = "var(--void-navy)";
    }
    if (dbAvatar) {
        dbAvatar.textContent = initials;
        dbAvatar.style.background = "var(--lunar-gold)";
        dbAvatar.style.color = "var(--void-navy)";
    }

    if (navName) navName.textContent = user.name;
    if (dropEmail) dropEmail.textContent = user.email;
    if (dropCreated) dropCreated.textContent = `Created ${user.created}`;

    // Get time-based greeting
    const hour = new Date().getHours();
    let greetTime = "Evening";
    if (hour < 12) {
        greetTime = "Morning";
    } else if (hour < 18) {
        greetTime = "Afternoon";
    }
    if (dbGreeting) dbGreeting.textContent = `Good ${greetTime}, ${user.name}`;

    // Setup Connected AI Providers based on Onboarding selection (Q3)
    if (onboardData && onboardData.q3) {
        const chosenModels = Array.isArray(onboardData.q3) ? onboardData.q3 : [onboardData.q3];
        
        // Reset all
        const providers = [
            { id: "provider-featherless", name: "Featherless AI" },
            { id: "provider-aimlapi", name: "AIMLAPI" },
            { id: "provider-gemini", name: "Gemini" },
            { id: "provider-openrouter", name: "OpenRouter" }
        ];

        providers.forEach(p => {
            const element = document.getElementById(p.id);
            if (element) {
                const statusBadge = element.querySelector(".connection-status");
                // Check if user selected this model
                const isConnected = chosenModels.some(model => model.toLowerCase().includes(p.name.toLowerCase()) || p.name.toLowerCase().includes(model.toLowerCase()));
                if (isConnected) {
                    statusBadge.textContent = "Connected";
                    statusBadge.className = "connection-status status-connected";
                } else {
                    statusBadge.textContent = "Inactive";
                    statusBadge.className = "connection-status status-inactive";
                }
            }
        });
    }
}

/* ==========================================
   TERMS & CONDITIONS MODAL
========================================== */

const termsModal = document.getElementById("terms-modal");
const openTermsBtn = document.getElementById("open-terms-btn");
const closeTermsBtn = document.getElementById("close-terms-btn");

if (openTermsBtn && termsModal) {
    openTermsBtn.addEventListener("click", (e) => {
        e.preventDefault();
        termsModal.classList.remove("hidden");
    });
}

if (closeTermsBtn && termsModal) {
    closeTermsBtn.addEventListener("click", () => {
        termsModal.classList.add("hidden");
    });

    // Close when clicking outside of modal content
    termsModal.addEventListener("click", (e) => {
        if (e.target === termsModal) {
            termsModal.classList.add("hidden");
        }
    });
}