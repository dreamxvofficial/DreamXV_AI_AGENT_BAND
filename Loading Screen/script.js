const video = document.getElementById("introVideo");

/* ==========================================
   SAFE STORAGE & PARSING UTILITIES
========================================== */

const safeStorage = {
    fallbackStore: {},
    getItem(key) {
        try {
            return localStorage.getItem(key);
        } catch (e) {
            console.warn("Storage read blocked, using fallback memory store:", e);
            return this.fallbackStore[key] || null;
        }
    },
    setItem(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch (e) {
            console.warn("Storage write blocked, saving to fallback memory store:", e);
            this.fallbackStore[key] = value;
        }
    },
    removeItem(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.warn("Storage remove blocked, clearing fallback memory store:", e);
            delete this.fallbackStore[key];
        }
    }
};

function safeJsonParse(str) {
    if (!str) return null;
    try {
        return JSON.parse(str);
    } catch (e) {
        console.error("JSON parse exception:", e);
        return null;
    }
}

/* ==========================================
   LOAD CORRECT VIDEO
========================================== */

function loadCorrectVideo() {
    const isMobile = window.innerWidth <= 768;
    const newSource = isMobile
        ? "/videos/DreamXV Intro Video_Mobile.mp4"
        : "/videos/DreamXV Intro Video_Desktop.mp4";

    if (video && video.src && decodeURIComponent(video.src).includes(newSource)) {
        return;
    }

    if (video) {
        const handleError = () => {
            console.error("Video failed to load:", newSource);
            const fallbackImg = document.getElementById("videoFallbackImage");
            if (fallbackImg) {
                fallbackImg.style.display = "block";
            }
            setTimeout(transitionToMainSite, 2000);
        };

        video.onerror = handleError;

        const sources = video.getElementsByTagName("source");
        for (let i = 0; i < sources.length; i++) {
            sources[i].onerror = handleError;
        }

        video.src = newSource;
        video.load();
        video.play().catch((err) => {
            console.log("Autoplay blocked or load issue, transitioning to fallback image: ", err);
            const fallbackImg = document.getElementById("videoFallbackImage");
            if (fallbackImg) {
                fallbackImg.style.display = "block";
            }
            setTimeout(transitionToMainSite, 2000);
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

    const container = document.querySelector(".loading-screen") || document.querySelector(".loading-container");
    const mainContent = document.getElementById("main-content");

    if (container) {
        container.classList.add("fade-out");
        setTimeout(() => {
            container.style.display = "none";
        }, 800);
    }

    if (mainContent) {
        mainContent.classList.remove("hidden");
        // Force reflow
        mainContent.offsetHeight;
        mainContent.classList.add("fade-in");
        
        // Check session and route to the correct screen
        const user = safeStorage.getItem("dreamxv_user");
        const onboarded = safeStorage.getItem("dreamxv_onboarded");
        
        if (user && onboarded) {
            showView("dashboard-view");
        } else {
            showView("landing-view");
        }
    }

    // Restore scroll and prevent layout shift
    document.body.style.overflow = "auto";
    document.documentElement.style.overflow = "auto";
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
        const user = safeStorage.getItem("dreamxv_user");
        const onboarded = safeStorage.getItem("dreamxv_onboarded");

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

    // 2. Google OAuth & Mock Fallback Flow
    const showTestBtn = document.getElementById("show-test-accounts-btn");
    const accountChooser = document.getElementById("account-chooser");
    const toggleCustomBtn = document.getElementById("toggle-custom-auth-btn");
    const customForm = document.getElementById("custom-account-form");
    const customSubmitBtn = document.getElementById("custom-signin-submit");

    if (showTestBtn) {
        showTestBtn.addEventListener("click", () => {
            accountChooser.classList.toggle("hidden");
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
            window.saveUserSession(name, email, avatar);
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
                window.saveUserSession(nameInput.value.trim(), emailInput.value.trim(), avatar);
            } else {
                alert("Please fill in both Name and Email.");
            }
        });
    }

    // Initialize real Google Auth
    initGoogleAuth();

    // 3. Onboarding Quiz Interaction
    const onboardWelcomeBtn = document.getElementById("start-onboard-btn");
    const onboardWelcome = document.getElementById("onboard-welcome");
    const onboardQuiz = document.getElementById("onboard-quiz");
    const nextBtn = document.getElementById("next-question-btn");
    const prevBtn = document.getElementById("prev-question-btn");

    let currentStep = 1;
    const totalSteps = 4;
    const quizAnswers = {};

    if (onboardWelcomeBtn) {
        onboardWelcomeBtn.addEventListener("click", () => {
            onboardWelcome.classList.add("hidden");
            onboardQuiz.classList.remove("hidden");
            updateQuizUI();
        });
    }

    function startOnboarding() {
        const user = safeJsonParse(safeStorage.getItem("dreamxv_user"));
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
                if (nextBtn) nextBtn.disabled = false;
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
                safeStorage.setItem("dreamxv_onboarding_data", JSON.stringify(quizAnswers));
                safeStorage.setItem("dreamxv_onboarded", "true");
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
        if (prevBtn) {
            if (currentStep === 1) {
                prevBtn.classList.add("hidden");
            } else {
                prevBtn.classList.remove("hidden");
            }
        }

        // Change Next button text at final step
        if (nextBtn) {
            if (currentStep === totalSteps) {
                nextBtn.textContent = "FINISH";
            } else {
                nextBtn.textContent = "NEXT";
            }
        }

        // Update progress indicators
        const stepIndicator = document.getElementById("progress-step-indicator");
        const progressBar = document.getElementById("onboard-progress-bar");
        if (stepIndicator) stepIndicator.textContent = `Question ${currentStep} of ${totalSteps}`;
        if (progressBar) progressBar.style.width = `${(currentStep / totalSteps) * 100}%`;

        // Check if current step has an answer saved to enable/disable Next button
        if (nextBtn) {
            const currentAnswer = quizAnswers[`q${currentStep}`];
            if (currentAnswer && (Array.isArray(currentAnswer) ? currentAnswer.length > 0 : true)) {
                nextBtn.disabled = false;
            } else {
                nextBtn.disabled = true;
            }
        }
    }

    // Save User Session helper (Exposed globally for Google Sign-In Callback)
    window.saveUserSession = function(name, email, avatar) {
        const user = {
            name: name,
            email: email,
            avatar: avatar,
            created: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
        };
        safeStorage.setItem("dreamxv_user", JSON.stringify(user));
        startOnboarding();
    };

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
            safeStorage.removeItem("dreamxv_user");
            safeStorage.removeItem("dreamxv_onboarded");
            safeStorage.removeItem("dreamxv_onboarding_data");
            showView("landing-view");
        });
    }

    // Initial Dashboard call if user is already logged in
    const user = safeStorage.getItem("dreamxv_user");
    const onboarded = safeStorage.getItem("dreamxv_onboarded");
    if (user && onboarded) {
        initDashboard();
    }
}

// 5. Initialize Dashboard Data
function initDashboard() {
    const user = safeJsonParse(safeStorage.getItem("dreamxv_user"));
    const onboardData = safeJsonParse(safeStorage.getItem("dreamxv_onboarding_data"));

    if (!user) {
        console.warn("Dashboard initialized without user session. Redirecting to login.");
        showView("auth-view");
        return;
    }

    // Update Avatar & Names
    const navAvatar = document.getElementById("nav-user-avatar-placeholder");
    const navName = document.getElementById("nav-user-name");
    const dropEmail = document.getElementById("dropdown-user-email");
    const dropCreated = document.getElementById("dropdown-created-date");
    const dbGreeting = document.getElementById("dashboard-greeting");
    const dbAvatar = document.getElementById("dashboard-user-avatar-placeholder");

    // Assign initials/pics
    const initials = (user.name || "U").charAt(0).toUpperCase();
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

    if (navName) navName.textContent = user.name || "Dreamer";
    if (dropEmail) dropEmail.textContent = user.email || "";
    if (dropCreated) dropCreated.textContent = `Created ${user.created || "Recently"}`;

    // Get time-based greeting
    const hour = new Date().getHours();
    let greetTime = "Evening";
    if (hour < 12) {
        greetTime = "Morning";
    } else if (hour < 18) {
        greetTime = "Afternoon";
    }
    if (dbGreeting) dbGreeting.textContent = `Good ${greetTime}, ${user.name || "Dreamer"}`;

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

/* ==========================================
   GOOGLE OAUTH SIGN-IN
========================================== */

let googleAuthRetries = 0;
function initGoogleAuth() {
    if (typeof google === "undefined" || typeof google.accounts === "undefined") {
        if (googleAuthRetries < 10) {
            googleAuthRetries++;
            setTimeout(initGoogleAuth, 500);
        } else {
            console.warn("Google Sign-In SDK failed to load. Falling back to test accounts only.");
            const googleContainer = document.getElementById("google-signin-btn");
            if (googleContainer) {
                googleContainer.innerHTML = "<p style='color: var(--lunar-gold); font-size: 13px; text-align: center; margin: 10px 0;'>Google Sign-In unavailable (SDK Blocked)</p>";
            }
        }
        return;
    }
    
    google.accounts.id.initialize({
        client_id: "122741106854-2pjjbguicplm05iurfcsog0uipr0nn74.apps.googleusercontent.com",
        callback: handleCredentialResponse
    });
    
    google.accounts.id.renderButton(
        document.getElementById("google-signin-btn"),
        { 
            theme: "filled_blue", 
            size: "large", 
            width: 320,
            text: "signin_with",
            shape: "rectangular"
        }
    );
}

function handleCredentialResponse(response) {
    try {
        const base64Url = response.credential.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        const googleUser = JSON.parse(jsonPayload);
        
        // Save user session and direct to onboarding
        window.saveUserSession(googleUser.name, googleUser.email, googleUser.picture);
    } catch (e) {
        console.error("Failed to parse Google credentials:", e);
    }
}

/* ==========================================
   INTERNAL AI PROVIDER ROUTER
========================================== */

window.AIRouter = {
    providers: [
        { name: "Featherless AI", isFallback: false },
        { name: "AIMLAPI", isFallback: true }
    ],
    async generateContent(prompt, options = {}) {
        console.log(`[AIRouter] Attempting generation with default provider: Featherless AI`);
        try {
            // Simulate Featherless AI call
            const response = await this.callFeatherless(prompt, options);
            console.log(`[AIRouter] Success with Featherless AI`);
            return response;
        } catch (error) {
            console.warn(`[AIRouter] Featherless AI failed: ${error.message || error}. Automatically falling back to AIMLAPI...`);
            try {
                const response = await this.callAIMLAPI(prompt, options);
                console.log(`[AIRouter] Success with fallback AIMLAPI`);
                return response;
            } catch (fallbackError) {
                console.error(`[AIRouter] All AI providers failed.`, fallbackError);
                throw new Error("All AI providers failed to respond.");
            }
        }
    },
    async callFeatherless(prompt, options) {
        if (options.simulateFailure === "featherless" || options.simulateFailure === "both") {
            throw new Error("Featherless AI connection timed out.");
        }
        return {
            provider: "Featherless AI",
            text: `[Featherless AI] Processed: "${prompt}"`
        };
    },
    async callAIMLAPI(prompt, options) {
        if (options.simulateFailure === "aimlapi" || options.simulateFailure === "both") {
            throw new Error("AIMLAPI service unavailable.");
        }
        return {
            provider: "AIMLAPI",
            text: `[AIMLAPI (Fallback)] Processed: "${prompt}"`
        };
    }
};