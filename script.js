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
    const newSource = "/videos/DreamXV Intro Video_Desktop.mp4";

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
        video.play().catch(() => { });
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
        }, 1000);
    }

    if (mainContent) {
        mainContent.classList.remove("hidden");
        // Check session and route to the correct screen
        const user = safeStorage.getItem("dreamxv_user");
        const onboarded = safeStorage.getItem("dreamxv_onboarded");

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
        const user = safeJsonParse(safeStorage.getItem("dreamxv_user"));
        const onboarded = safeStorage.getItem("dreamxv_onboarded");

        if (user && onboarded === "true") {
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

    // 2. Tab switching & Local Auth handling
    const tabLoginBtn = document.getElementById("tab-login-btn");
    const tabSignupBtn = document.getElementById("tab-signup-btn");
    const loginForm = document.getElementById("login-form");
    const signupForm = document.getElementById("signup-form");
    const authErrorBox = document.getElementById("auth-error-box");

    if (tabLoginBtn && tabSignupBtn && loginForm && signupForm) {
        tabLoginBtn.addEventListener("click", () => {
            tabLoginBtn.classList.add("active");
            tabLoginBtn.style.color = "var(--lunar-gold)";
            tabLoginBtn.style.borderBottomColor = "var(--lunar-gold)";
            tabSignupBtn.classList.remove("active");
            tabSignupBtn.style.color = "rgba(240, 232, 208, 0.4)";
            tabSignupBtn.style.borderBottomColor = "transparent";
            loginForm.classList.remove("hidden");
            signupForm.classList.add("hidden");
            if (authErrorBox) authErrorBox.style.display = "none";
        });

        tabSignupBtn.addEventListener("click", () => {
            tabSignupBtn.classList.add("active");
            tabSignupBtn.style.color = "var(--lunar-gold)";
            tabSignupBtn.style.borderBottomColor = "var(--lunar-gold)";
            tabLoginBtn.classList.remove("active");
            tabLoginBtn.style.color = "rgba(240, 232, 208, 0.4)";
            tabLoginBtn.style.borderBottomColor = "transparent";
            signupForm.classList.remove("hidden");
            loginForm.classList.add("hidden");
            if (authErrorBox) authErrorBox.style.display = "none";
        });
    }

    const showAuthError = (msg) => {
        if (authErrorBox) {
            authErrorBox.textContent = msg;
            authErrorBox.style.display = "block";
        }
    };

    if (signupForm) {
        signupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (authErrorBox) authErrorBox.style.display = "none";

            const name = document.getElementById("signup-name").value.trim();
            const username = document.getElementById("signup-username").value.trim();
            const email = document.getElementById("signup-email").value.trim();
            const password = document.getElementById("signup-password").value;
            const confirm = document.getElementById("signup-confirm").value;

            if (password !== confirm) {
                showAuthError("Passwords do not match.");
                return;
            }

            try {
                const res = await fetch("/api/auth/signup", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, username, email, password })
                });
                const data = await res.json();
                if (!data.success) {
                    showAuthError(data.error || "Signup failed.");
                    return;
                }
                showToast("Account created successfully!", "success");
                
                const userObj = {
                    name: data.user.name,
                    username: data.user.username,
                    email: data.user.email,
                    created: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
                };
                safeStorage.setItem("dreamxv_user", JSON.stringify(userObj));
                safeStorage.setItem("dreamxv_onboarded", "false");
                startOnboarding();
            } catch (err) {
                console.error("Signup error:", err);
                showAuthError("Failed to reach server. Please try again.");
            }
        });
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (authErrorBox) authErrorBox.style.display = "none";

            const usernameOrEmail = document.getElementById("login-username").value.trim();
            const password = document.getElementById("login-password").value;

            try {
                const res = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username_or_email: usernameOrEmail, password })
                });
                const data = await res.json();
                if (!data.success) {
                    showAuthError(data.error || "Invalid credentials.");
                    return;
                }
                
                const userObj = {
                    name: data.user.name,
                    username: data.user.username,
                    email: data.user.email,
                    created: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
                };
                safeStorage.setItem("dreamxv_user", JSON.stringify(userObj));
                
                if (data.user.onboarded) {
                    safeStorage.setItem("dreamxv_onboarded", "true");
                    safeStorage.setItem("dreamxv_onboarding_data", JSON.stringify(data.user.onboarding_answers));
                    showView("dashboard-view");
                    initDashboard();
                } else {
                    safeStorage.setItem("dreamxv_onboarded", "false");
                    startOnboarding();
                }
                showToast(`Welcome back, ${data.user.name}!`, "success");
            } catch (err) {
                console.error("Login error:", err);
                showAuthError("Failed to reach server. Please try again.");
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
    const totalSteps = 4;
    const quizAnswers = {
        q1: "",
        q2: "",
        q3: [],
        q4: ""
    };

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

    const nicknameInput = document.getElementById("onboard-nickname");
    if (nicknameInput) {
        nicknameInput.addEventListener("input", () => {
            quizAnswers.q1 = nicknameInput.value.trim();
            validateCurrentStep();
        });
    }

    document.addEventListener("change", (e) => {
        if (e.target && e.target.name === "creator_type") {
            quizAnswers.q2 = e.target.value;
            validateCurrentStep();
        }
    });

    document.addEventListener("change", (e) => {
        if (e.target && e.target.name === "genres") {
            const checkboxes = document.querySelectorAll('input[name="genres"]:checked');
            quizAnswers.q3 = Array.from(checkboxes).map(cb => cb.value);
            validateCurrentStep();
        }
    });

    const dreamProjectInput = document.getElementById("onboard-dream-project");
    if (dreamProjectInput) {
        dreamProjectInput.addEventListener("input", () => {
            quizAnswers.q4 = dreamProjectInput.value.trim();
            validateCurrentStep();
        });
    }

    function validateCurrentStep() {
        if (!nextBtn) return;
        let valid = false;
        if (currentStep === 1) {
            valid = quizAnswers.q1.length > 0;
        } else if (currentStep === 2) {
            valid = quizAnswers.q2.length > 0;
        } else if (currentStep === 3) {
            valid = quizAnswers.q3.length > 0;
        } else if (currentStep === 4) {
            valid = quizAnswers.q4.length > 0;
        }
        nextBtn.disabled = !valid;
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", async () => {
            if (currentStep < totalSteps) {
                currentStep++;
                updateQuizUI();
            } else {
                const user = safeJsonParse(safeStorage.getItem("dreamxv_user"));
                if (!user) return;

                try {
                    const res = await fetch("/api/auth/onboarding", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            username: user.username,
                            name: quizAnswers.q1,
                            creator_type: quizAnswers.q2,
                            favorite_genres: quizAnswers.q3,
                            dream_project: quizAnswers.q4
                        })
                    });
                    const data = await res.json();
                    if (data.success) {
                        user.name = quizAnswers.q1;
                        safeStorage.setItem("dreamxv_user", JSON.stringify(user));
                        safeStorage.setItem("dreamxv_onboarding_data", JSON.stringify(data.user.onboarding_answers));
                        safeStorage.setItem("dreamxv_onboarded", "true");
                        showView("dashboard-view");
                        initDashboard();
                        showToast("Onboarding complete!", "success");
                    } else {
                        showToast("Onboarding failed to sync with server, saving locally.", "warning");
                        user.name = quizAnswers.q1;
                        safeStorage.setItem("dreamxv_user", JSON.stringify(user));
                        safeStorage.setItem("dreamxv_onboarding_data", JSON.stringify(quizAnswers));
                        safeStorage.setItem("dreamxv_onboarded", "true");
                        showView("dashboard-view");
                        initDashboard();
                    }
                } catch (err) {
                    console.error("Onboarding sync failed:", err);
                    user.name = quizAnswers.q1;
                    safeStorage.setItem("dreamxv_user", JSON.stringify(user));
                    safeStorage.setItem("dreamxv_onboarding_data", JSON.stringify(quizAnswers));
                    safeStorage.setItem("dreamxv_onboarded", "true");
                    showView("dashboard-view");
                    initDashboard();
                }
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
        const quizContainers = document.querySelectorAll(".quiz-question");
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

        if (prevBtn) {
            if (currentStep === 1) {
                prevBtn.classList.add("hidden");
            } else {
                prevBtn.classList.remove("hidden");
            }
        }

        if (nextBtn) {
            if (currentStep === totalSteps) {
                nextBtn.textContent = "FINISH";
            } else {
                nextBtn.textContent = "NEXT";
            }
        }

        const stepIndicator = document.getElementById("progress-step-indicator");
        const progressBar = document.getElementById("onboard-progress-bar");
        if (stepIndicator) stepIndicator.textContent = `Question ${currentStep} of ${totalSteps}`;
        if (progressBar) progressBar.style.width = `${(currentStep / totalSteps) * 100}%`;

        validateCurrentStep();
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
        logoutBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            try {
                await fetch("/api/auth/logout", { method: "POST" });
            } catch (err) {}
            safeStorage.removeItem("dreamxv_user");
            safeStorage.removeItem("dreamxv_onboarded");
            safeStorage.removeItem("dreamxv_onboarding_data");
            showView("landing-view");
            showToast("Logged out successfully.", "info");
        });
    }

    const userObj = safeStorage.getItem("dreamxv_user");
    const onboardedObj = safeStorage.getItem("dreamxv_onboarded");
    if (userObj && onboardedObj === "true") {
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

    // Welcome greeting with first name
    const firstName = (user.name || "Dreamer").split(" ")[0];
    if (dbGreeting) dbGreeting.textContent = `Welcome, ${firstName}`;

    // Fetch projects from backend
    fetchAndRenderProjects();
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
async function initGoogleAuth() {
    return; // Temporarily disabled Google login
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

    let clientId = "122741106854-2pjjbguicplm05iurfcsog0uipr0nn74.apps.googleusercontent.com"; // Fallback Client ID
    try {
        const response = await fetch("/api/health");
        if (response.ok) {
            const data = await response.json();
            if (data.google_client_id) {
                clientId = data.google_client_id;
            }
        }
    } catch (e) {
        console.warn("Failed to dynamically load Google Client ID, using default.", e);
    }

    google.accounts.id.initialize({
        client_id: clientId,
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
        const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
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
   BACKEND API CONFIGURATION (Relative Paths only)
========================================== */

/* ==========================================
   CREATE PROJECT MODAL
========================================== */

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("create-project-modal");
    const promptInput = document.getElementById("project-prompt-input");
    const charCount = document.getElementById("prompt-char-count");
    const errorBox = document.getElementById("create-project-error");
    const submitBtn = document.getElementById("submit-create-project-btn");
    const submitText = document.getElementById("submit-btn-text");
    const submitSpinner = document.getElementById("submit-btn-spinner");
    const closeBtn = document.getElementById("close-create-project-btn");
    const cancelBtn = document.getElementById("cancel-create-project-btn");
    const progressSection = document.getElementById("generation-progress");

    if (!modal) return;

    // --- Open modal triggers ---
    function openCreateModal() {
        modal.classList.remove("hidden");
        if (promptInput) {
            promptInput.value = "";
            promptInput.focus();
        }
        if (charCount) charCount.textContent = "0 / 5000";
        if (errorBox) errorBox.style.display = "none";
        if (progressSection) progressSection.style.display = "none";
        resetSubmitButton();
    }

    // Wire all "create" triggers
    const createStudioCard = document.getElementById("action-create-studio");
    const createProjectEmpty = document.getElementById("btn-create-project-empty");

    if (createStudioCard) createStudioCard.addEventListener("click", openCreateModal);
    if (createProjectEmpty) createProjectEmpty.addEventListener("click", openCreateModal);

    // --- Close modal ---
    function closeCreateModal() {
        modal.classList.add("hidden");
    }

    if (closeBtn) closeBtn.addEventListener("click", closeCreateModal);
    if (cancelBtn) cancelBtn.addEventListener("click", closeCreateModal);
    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeCreateModal();
    });

    // --- Character count ---
    if (promptInput && charCount) {
        promptInput.addEventListener("input", () => {
            const len = promptInput.value.length;
            charCount.textContent = `${len} / 5000`;
            if (len > 5000) {
                charCount.style.color = "#f87171";
            } else {
                charCount.style.color = "rgba(240, 232, 208, 0.4)";
            }
        });
    }

    // --- Reset submit button ---
    function resetSubmitButton() {
        if (submitBtn) submitBtn.disabled = false;
        if (submitText) submitText.textContent = "GENERATE PROJECT";
        if (submitSpinner) submitSpinner.style.display = "none";
    }

    // --- Show loading state ---
    function setSubmitLoading() {
        if (submitBtn) submitBtn.disabled = true;
        if (submitText) submitText.textContent = "GENERATING...";
        if (submitSpinner) submitSpinner.style.display = "inline-block";
    }

    // --- Show error ---
    function showError(msg) {
        if (errorBox) {
            errorBox.textContent = msg;
            errorBox.style.display = "block";
        }
    }

    // --- Submit handler ---
    if (submitBtn) {
        submitBtn.addEventListener("click", async () => {
            const prompt = promptInput ? promptInput.value.trim() : "";

            // Client-side validation
            if (prompt.length < 10) {
                showError("Prompt must be at least 10 characters. Describe your game idea!");
                return;
            }
            if (prompt.length > 5000) {
                showError("Prompt exceeds 5,000 character limit.");
                return;
            }

            if (errorBox) errorBox.style.display = "none";
            setSubmitLoading();

            // Show progress section immediately
            if (progressSection) {
                progressSection.style.display = "block";
            }

            const initialStatuses = [
                { agent_name: "Chief Agent", status: "ready" },
                { agent_name: "Story Agent", status: "ready" },
                { agent_name: "Character Agent", status: "ready" },
                { agent_name: "World Agent", status: "ready" },
                { agent_name: "Gameplay Agent", status: "ready" },
                { agent_name: "Art Agent", status: "ready" },
                { agent_name: "QA Agent", status: "ready" },
                { agent_name: "Reviewer Agent", status: "ready" },
                { agent_name: "Documentation Agent", status: "ready" },
            ];

            updateModalAgentStatus(initialStatuses);
            updateAgentStatusPanel(initialStatuses);

            // Progress bar and percentage text elements
            const progressIndicator = document.getElementById("generation-progress-indicator");
            const progressPercent = document.getElementById("generation-progress-percent");

            if (progressPercent) progressPercent.textContent = "0%";
            if (progressIndicator) progressIndicator.style.width = "0%";

            let progressVal = 0;
            let progressInterval = setInterval(() => {
                if (progressVal < 95) {
                    progressVal += Math.random() * 2 + 1; // Increment by 1-3%
                    if (progressVal > 95) progressVal = 95;
                    updateProgressBar(progressVal);
                }
            }, 150);

            function updateProgressBar(val) {
                if (progressIndicator) progressIndicator.style.width = `${val}%`;
                if (progressPercent) progressPercent.textContent = `${Math.floor(val)}%`;
            }

            // Simulation setup
            let simTimeout = null;
            let simIndex = 0;
            const simSteps = [
                {
                    updates: [
                        { agent_name: "Chief Agent", status: "running" }
                    ],
                    delay: 1500
                },
                {
                    updates: [
                        { agent_name: "Chief Agent", status: "completed" },
                        { agent_name: "Story Agent", status: "running" },
                        { agent_name: "Character Agent", status: "running" },
                        { agent_name: "World Agent", status: "running" },
                        { agent_name: "Gameplay Agent", status: "running" }
                    ],
                    delay: 3000
                },
                {
                    updates: [
                        { agent_name: "Story Agent", status: "completed" },
                        { agent_name: "Character Agent", status: "completed" },
                        { agent_name: "World Agent", status: "completed" },
                        { agent_name: "Gameplay Agent", status: "completed" },
                        { agent_name: "Art Agent", status: "running" }
                    ],
                    delay: 2000
                },
                {
                    updates: [
                        { agent_name: "Art Agent", status: "completed" },
                        { agent_name: "QA Agent", status: "running" }
                    ],
                    delay: 1500
                },
                {
                    updates: [
                        { agent_name: "QA Agent", status: "completed" },
                        { agent_name: "Reviewer Agent", status: "running" }
                    ],
                    delay: 1500
                },
                {
                    updates: [
                        { agent_name: "Reviewer Agent", status: "completed" },
                        { agent_name: "Documentation Agent", status: "running" }
                    ],
                    delay: 1500
                }
            ];

            let activeStatuses = JSON.parse(JSON.stringify(initialStatuses));
            const genStartTime = Date.now();
            initExecutionDashboard(initialStatuses, genStartTime);

            function runSimulationStep() {
                if (simIndex < simSteps.length) {
                    const step = simSteps[simIndex];
                    step.updates.forEach(up => {
                        const existing = activeStatuses.find(s => s.agent_name === up.agent_name);
                        if (existing) existing.status = up.status;
                    });
                    updateModalAgentStatus(activeStatuses);
                    updateAgentStatusPanel(activeStatuses);
                    updatePipelineVisualization(activeStatuses);
                    updateExecutionDashboard(activeStatuses, genStartTime);

                    simIndex++;
                    simTimeout = setTimeout(runSimulationStep, step.delay);
                }
            }
            runSimulationStep();

            // Get user from session
            const user = safeJsonParse(safeStorage.getItem("dreamxv_user"));
            const userId = user ? user.email : "anonymous";

            try {
                const response = await fetch("/api/generate-project", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ prompt: prompt, user_id: userId }),
                });

                if (simTimeout) clearTimeout(simTimeout);
                if (progressInterval) clearInterval(progressInterval);
                updateProgressBar(100);

                const responseText = await response.text();
                console.log(responseText);

                if (!response.ok) {
                    let errMsg = "";
                    try {
                        const errData = JSON.parse(responseText);
                        errMsg = errData.error || errData.detail;
                    } catch (_) {
                        errMsg = `Server error: ${response.status}`;
                    }
                    throw new Error(errMsg || `Server error: ${response.status}`);
                }
                
                const data = JSON.parse(responseText);
                if (!data.success) {
                    console.error(data);
                    showToast(data.error || "Generation failed", "error");
                    
                    // Reset UI/button state as done in catch block
                    resetSubmitButton();
                    const readyStatuses = initialStatuses.map(s => ({ ...s, status: "ready" }));
                    updateModalAgentStatus(readyStatuses);
                    updateAgentStatusPanel(readyStatuses);
                    updatePipelineVisualization(readyStatuses);
                    return;
                }
                const projectObj = data.project || data.data || {};
                console.log("[DreamXV] Project generation completed:", projectObj);

                activeStatuses.forEach(s => s.status = "completed");
                updateModalAgentStatus(activeStatuses);
                updateAgentStatusPanel(activeStatuses);
                updatePipelineVisualization(activeStatuses);
                updateExecutionDashboard(activeStatuses, genStartTime);
                finalizeExecutionDashboard(genStartTime);

                // Add to local projects
                const localProjectsStr = safeStorage.getItem("dreamxv_projects") || "[]";
                const localProjects = safeJsonParse(localProjectsStr) || [];

                projectObj.status = "completed";
                if (!projectObj.project_id) {
                    projectObj.project_id = "dxv_" + Math.random().toString(36).substring(2, 11);
                }
                if (!projectObj.created_at) {
                    projectObj.created_at = new Date().toISOString();
                }

                localProjects.push(projectObj);
                safeStorage.setItem("dreamxv_projects", JSON.stringify(localProjects));

                showToast("Project generation complete!", "success");

                // Close modal after a short delay
                setTimeout(() => {
                    if (modal) modal.classList.add("hidden");
                    resetSubmitButton();

                    // Reset statuses back to ready
                    const readyStatuses = initialStatuses.map(s => ({ ...s, status: "ready" }));
                    updateModalAgentStatus(readyStatuses);
                    updateAgentStatusPanel(readyStatuses);
                    updatePipelineVisualization(readyStatuses);
                }, 2000);

                // Refresh project list
                fetchAndRenderProjects();

            } catch (err) {
                console.error("[DreamXV] API fetch or project generation failed:", err);
                showToast("Generation failed: " + err.message, "error");

                if (simTimeout) clearTimeout(simTimeout);
                if (progressInterval) clearInterval(progressInterval);
                updateProgressBar(0);

                // Set running agents to error status
                activeStatuses.forEach(s => {
                    if (s.status === "running") s.status = "error";
                });
                updateModalAgentStatus(activeStatuses);
                updateAgentStatusPanel(activeStatuses);
                updatePipelineVisualization(activeStatuses);

                setTimeout(() => {
                    if (modal) modal.classList.add("hidden");
                    resetSubmitButton();

                    const readyStatuses = initialStatuses.map(s => ({ ...s, status: "ready" }));
                    updateModalAgentStatus(readyStatuses);
                    updateAgentStatusPanel(readyStatuses);
                    updatePipelineVisualization(readyStatuses);
                }, 3000);
            }
        });
    }
});

/* ==========================================
   AGENT STATUS PANEL UPDATES
========================================== */

const STATUS_COLORS = {
    ready: "status-ready",
    running: "status-running",
    completed: "status-completed",
    error: "status-error",
};

function updateAgentStatusPanel(agents) {
    const panel = document.getElementById("agent-status-list");
    if (!panel || !agents || agents.length === 0) return;

    panel.innerHTML = agents.map(a => `
        <div class="agent-status-item">
            <span class="agent-role font-code">${a.agent_name}</span>
            <span class="status-badge ${STATUS_COLORS[a.status] || 'status-ready'}">${capitalize(a.status)}</span>
        </div>
    `).join("");
}

function updateModalAgentStatus(agents) {
    const container = document.getElementById("modal-agent-status");
    if (!container || !agents) return;

    container.innerHTML = agents.map(a => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid rgba(26, 48, 72, 0.3);">
            <span style="font-family: var(--font-code); font-size: 13px; color: var(--starlight);">${a.agent_name}</span>
            <span class="status-badge ${STATUS_COLORS[a.status] || 'status-ready'}" style="font-size: 11px;">${capitalize(a.status)}</span>
        </div>
    `).join("");
}

function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/* ==========================================
   STATUS POLLING
========================================== */

let _statusPollInterval = null;

function startStatusPolling() {
    stopStatusPolling();

    _statusPollInterval = setInterval(async () => {
        try {
            const response = await fetch("/api/agents");
            if (!response.ok) return;

            const data = await response.json();
            if (data.agents && data.agents.length > 0) {
                updateAgentStatusPanel(data.agents);
                updateModalAgentStatus(data.agents);

                // Check if all completed
                const allDone = data.agents.every(
                    a => a.status === "completed" || a.status === "error"
                );

                if (allDone) {
                    stopStatusPolling();
                    showToast("Project generation complete!", "success");

                    // Close modal after a short delay
                    setTimeout(() => {
                        const modal = document.getElementById("create-project-modal");
                        if (modal) modal.classList.add("hidden");
                    }, 2000);

                    // Refresh project list
                    fetchAndRenderProjects();
                }
            }
        } catch (err) {
            console.warn("[DreamXV] Status poll failed:", err.message);
        }
    }, 3000); // Poll every 3 seconds
}

function stopStatusPolling() {
    if (_statusPollInterval) {
        clearInterval(_statusPollInterval);
        _statusPollInterval = null;
    }
}

/* ==========================================
   PROJECTS LIST
========================================== */

async function fetchAndRenderProjects() {
    const container = document.getElementById("projects-list-container");
    const emptyState = document.getElementById("projects-empty-state");
    if (!container) return;

    // Load local projects from localStorage
    const localProjectsStr = safeStorage.getItem("dreamxv_projects") || "[]";
    const localProjects = safeJsonParse(localProjectsStr) || [];

    let mergedProjects = [...localProjects];

    // Sort by created_at descending
    mergedProjects.sort((a, b) => {
        const dateA = new Date(a.created_at || 0);
        const dateB = new Date(b.created_at || 0);
        return dateB - dateA;
    });

    if (mergedProjects.length > 0) {
        if (emptyState) emptyState.style.display = "none";

        // Remove existing project list cards
        container.querySelectorAll(".project-list-card").forEach(c => c.remove());

        mergedProjects.forEach(p => {
            const card = document.createElement("div");
            card.className = "project-list-card";
            card.style.cursor = "pointer";
            card.innerHTML = `
                <div>
                    <div class="project-title">${escapeHtml(p.title || "Untitled")}</div>
                    <div class="project-date">${formatDate(p.created_at)}</div>
                </div>
                <span class="project-status">${p.status || "completed"}</span>
            `;
            card.addEventListener("click", () => {
                showProjectDetails(p.project_id);
            });
            container.appendChild(card);
        });
    } else {
        if (emptyState) emptyState.style.display = "flex";
    }
}

function showProjectDetails(projectId) {
    const localProjectsStr = safeStorage.getItem("dreamxv_projects") || "[]";
    const localProjects = safeJsonParse(localProjectsStr) || [];
    const project = localProjects.find(p => p.project_id === projectId);

    if (!project) {
        showToast("Project details not found in local storage.", "error");
        return;
    }

    const modal = document.getElementById("project-details-modal");
    if (!modal) return;

    const titleEl = document.getElementById("details-project-title");
    if (titleEl) titleEl.textContent = project.title || "Untitled Project";

    // 1. Narrative Tab
    let story = project.story || {};
    if (typeof story === "string") {
        story = { summary: story, lore: story, acts: [], themes: [] };
    }
    const loreEl = document.getElementById("details-lore");
    if (loreEl) loreEl.textContent = story.lore || story.summary || "No lore generated.";

    const summaryEl = document.getElementById("details-summary");
    if (summaryEl) summaryEl.textContent = story.summary || "No story synopsis generated.";

    const actsEl = document.getElementById("details-acts");
    if (actsEl) {
        actsEl.innerHTML = "";
        const acts = story.acts || [];
        if (acts.length > 0) {
            acts.forEach(act => {
                const li = document.createElement("li");
                li.textContent = act;
                actsEl.appendChild(li);
            });
        } else {
            actsEl.innerHTML = "<li>No story acts generated.</li>";
        }
    }

    const themesEl = document.getElementById("details-themes");
    if (themesEl) {
        themesEl.innerHTML = "";
        const themes = story.themes || [];
        if (themes.length > 0) {
            themes.forEach(theme => {
                const tag = document.createElement("div");
                tag.className = "feature-tag";
                tag.style.margin = "4px";
                tag.textContent = theme;
                themesEl.appendChild(tag);
            });
        } else {
            themesEl.innerHTML = "<span style='color: rgba(240, 232, 208, 0.4); font-size: 13px;'>No thematic focus points generated.</span>";
        }
    }

    // 2. Characters Tab
    const charListEl = document.getElementById("details-character-list");
    if (charListEl) {
        charListEl.innerHTML = "";
        const characters = project.characters || [];
        if (characters.length > 0) {
            characters.forEach(char => {
                const charCard = document.createElement("div");
                charCard.className = "character-card";

                charCard.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-2);">
                        <strong style="color: var(--lunar-gold); font-size: 16px;">${escapeHtml(char.name)}</strong>
                        <span style="font-family: var(--font-code); font-size: 11px; padding: 2px 8px; border: 1px solid var(--earth-teal); color: var(--earth-teal); border-radius: 12px; height: fit-content;">${escapeHtml(char.role)}</span>
                    </div>
                    <p style="font-size: 13px; color: rgba(240, 232, 208, 0.8); line-height: 1.5; margin-bottom: var(--space-3);">${escapeHtml(char.backstory)}</p>
                    
                    <div style="margin-bottom: var(--space-2);">
                        <span style="font-size: 11px; color: var(--lunar-gold); font-family: var(--font-code); display: block; margin-bottom: 2px;">ABILITIES & POWERS</span>
                        <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                            ${(char.abilities || []).map(ab => `<span class="feature-tag" style="font-size: 10px; padding: 2px 6px;">${escapeHtml(ab)}</span>`).join("") || `<span style="color: rgba(240, 232, 208, 0.4); font-size: 11px;">None</span>`}
                        </div>
                    </div>
                    
                    <div>
                        <span style="font-size: 11px; color: var(--lunar-gold); font-family: var(--font-code); display: block; margin-bottom: 2px;">PERSONALITY TRAITS</span>
                        <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                            ${(char.personality_traits || []).map(t => `<span class="feature-tag" style="font-size: 10px; padding: 2px 6px; background: rgba(27, 138, 122, 0.1); border-color: rgba(27, 138, 122, 0.2);">${escapeHtml(t)}</span>`).join("") || `<span style="color: rgba(240, 232, 208, 0.4); font-size: 11px;">None</span>`}
                        </div>
                    </div>
                `;
                charListEl.appendChild(charCard);
            });
        } else {
            charListEl.innerHTML = "<p style='color: rgba(240, 232, 208, 0.4); font-size: 14px;'>No characters generated.</p>";
        }
    }

    // 3. Gameplay & World Tab
    let world = project.world || {};
    if (typeof world === "string") {
        world = { description: world, atmosphere: "" };
    }
    const worldDescEl = document.getElementById("details-world-desc");
    if (worldDescEl) worldDescEl.textContent = world.description || "No world setting generated.";

    const worldAtmosphereEl = document.getElementById("details-world-atmosphere");
    if (worldAtmosphereEl) worldAtmosphereEl.textContent = world.atmosphere || "No atmosphere details generated.";

    let gameplay = project.gameplay || {};
    if (typeof gameplay === "string") {
        gameplay = { core_loop: gameplay, progression_system: "", difficulty_curve: "" };
    }
    const coreLoopEl = document.getElementById("details-core-loop");
    if (coreLoopEl) coreLoopEl.textContent = gameplay.core_loop || "No core loop design generated.";

    const progressionEl = document.getElementById("details-progression");
    if (progressionEl) progressionEl.textContent = gameplay.progression_system || "No progression system details generated.";

    const difficultyEl = document.getElementById("details-difficulty");
    if (difficultyEl) difficultyEl.textContent = gameplay.difficulty_curve || "No difficulty curve details generated.";

    // 4. Visuals & QA Tab
    let art = project.art || {};
    if (typeof art === "string") {
        art = { style_guide: art, image_paths: project.images || [] };
    } else if (project.images && (!art.image_paths || art.image_paths.length === 0)) {
        art.image_paths = project.images;
    }
    const styleGuideEl = document.getElementById("details-style-guide");
    if (styleGuideEl) styleGuideEl.textContent = art.style_guide || "No visual style guide generated.";

    const galleryEl = document.getElementById("details-gallery");
    if (galleryEl) {
        galleryEl.innerHTML = "";
        const imagePaths = art.image_paths || [];
        if (imagePaths.length > 0) {
            imagePaths.forEach((path, idx) => {
                const img = document.createElement("img");
                img.src = path;
                img.alt = `Concept Art ${idx + 1}`;
                img.style.width = "100%";
                img.style.height = "160px";
                img.style.objectFit = "cover";
                img.style.borderRadius = "6px";
                img.style.border = "1px solid rgba(26, 48, 72, 0.5)";
                galleryEl.appendChild(img);
            });
        } else {
            galleryEl.innerHTML = "<div style='grid-column: span 3; text-align: center; color: rgba(240, 232, 208, 0.4); font-size: 13px; padding: 20px 0;'>No concept art generated.</div>";
        }
    }

    const qa = project.qa || {};
    const qaScoreEl = document.getElementById("details-qa-score");
    if (qaScoreEl) qaScoreEl.textContent = `SCORE: ${qa.consistency_score != null ? qa.consistency_score.toFixed(1) : "--"}/10`;

    const qaAssessmentEl = document.getElementById("details-qa-assessment");
    if (qaAssessmentEl) qaAssessmentEl.textContent = qa.overall_assessment || "No QA overall assessment generated.";

    const qaIssuesEl = document.getElementById("details-qa-issues");
    if (qaIssuesEl) {
        qaIssuesEl.innerHTML = "";
        const issues = qa.issues || [];
        if (issues.length > 0) {
            issues.forEach(issue => {
                const li = document.createElement("li");
                li.textContent = issue;
                qaIssuesEl.appendChild(li);
            });
        } else {
            qaIssuesEl.innerHTML = "<li style='color: var(--earth-teal); list-style-type: none;'>No consistency issues found.</li>";
        }
    }

    const qaSuggestionsEl = document.getElementById("details-qa-suggestions");
    if (qaSuggestionsEl) {
        qaSuggestionsEl.innerHTML = "";
        const suggestions = qa.suggestions || [];
        if (suggestions.length > 0) {
            suggestions.forEach(sug => {
                const li = document.createElement("li");
                li.textContent = sug;
                qaSuggestionsEl.appendChild(li);
            });
        } else {
            qaSuggestionsEl.innerHTML = "<li style='list-style-type: none; color: rgba(240, 232, 208, 0.4);'>No improvement suggestions.</li>";
        }
    }

    // 5. Documentation Tab
    const doc = project.documentation || {};
    const elevatorPitchEl = document.querySelector("#details-elevator-pitch .doc-pitch-text");
    if (elevatorPitchEl) elevatorPitchEl.textContent = doc.elevator_pitch || "No elevator pitch generated.";

    const readmeEl = document.getElementById("details-readme");
    if (readmeEl) readmeEl.textContent = doc.readme || "No README.md generated.";

    const gddEl = document.getElementById("details-gdd");
    if (gddEl) gddEl.textContent = doc.gdd || "No Game Design Document generated.";

    const docFeaturesEl = document.getElementById("details-feature-list");
    if (docFeaturesEl) {
        docFeaturesEl.innerHTML = "";
        const features = doc.feature_list || [];
        if (features.length > 0) {
            features.forEach(f => {
                const li = document.createElement("li");
                li.textContent = f;
                docFeaturesEl.appendChild(li);
            });
        } else {
            docFeaturesEl.innerHTML = "<li>No features listed.</li>";
        }
    }

    const docMechanicsEl = document.getElementById("details-core-mechanics");
    if (docMechanicsEl) {
        docMechanicsEl.innerHTML = "";
        const mechanics = doc.core_mechanics || [];
        if (mechanics.length > 0) {
            mechanics.forEach(m => {
                const li = document.createElement("li");
                li.textContent = m;
                docMechanicsEl.appendChild(li);
            });
        } else {
            docMechanicsEl.innerHTML = "<li>No core mechanics listed.</li>";
        }
    }

    const docMonetizationEl = document.getElementById("details-monetization");
    if (docMonetizationEl) {
        docMonetizationEl.innerHTML = "";
        const monetization = doc.monetization || [];
        if (monetization.length > 0) {
            monetization.forEach(m => {
                const li = document.createElement("li");
                li.textContent = m;
                docMonetizationEl.appendChild(li);
            });
        } else {
            docMonetizationEl.innerHTML = "<li>No monetization ideas listed.</li>";
        }
    }

    const docExpansionEl = document.getElementById("details-future-expansion");
    if (docExpansionEl) {
        docExpansionEl.innerHTML = "";
        const expansion = doc.future_expansion || [];
        if (expansion.length > 0) {
            expansion.forEach(e => {
                const li = document.createElement("li");
                li.textContent = e;
                docExpansionEl.appendChild(li);
            });
        } else {
            docExpansionEl.innerHTML = "<li>No future expansion ideas listed.</li>";
        }
    }

    const docTechSummaryEl = document.getElementById("details-tech-summary");
    if (docTechSummaryEl) docTechSummaryEl.textContent = doc.technical_summary || "No technical summary generated.";

    // 6. Review Report Section
    const review = project.review || {};
    const reviewScoreEl = document.getElementById("details-review-score");
    if (reviewScoreEl) reviewScoreEl.textContent = `SCORE: ${review.consistency_score != null ? review.consistency_score.toFixed(1) : "--"}/10`;

    const reviewSummaryEl = document.getElementById("details-review-summary");
    if (reviewSummaryEl) reviewSummaryEl.textContent = review.summary || "No review summary generated.";

    const reviewIssuesEl = document.getElementById("details-review-issues");
    if (reviewIssuesEl) {
        reviewIssuesEl.innerHTML = "";
        const issues = review.issues || [];
        if (issues.length > 0) {
            issues.forEach(issue => {
                const card = document.createElement("div");
                card.className = `review-issue-card severity-${issue.severity || 'warning'}`;
                card.innerHTML = `
                    <div class="review-issue-meta">
                        <span class="review-issue-category">${escapeHtml((issue.category || 'general').toUpperCase())}</span>
                        <span class="review-issue-severity">${escapeHtml((issue.severity || 'warning').toUpperCase())}</span>
                    </div>
                    <div class="review-issue-desc">${escapeHtml(issue.description)}</div>
                    ${issue.suggested_fix ? `<div class="review-issue-fix"><strong>Suggested Fix:</strong> ${escapeHtml(issue.suggested_fix)}</div>` : ''}
                    ${issue.references && issue.references.length > 0 ? `
                        <div class="review-issue-refs">
                            <strong>References:</strong>
                            ${issue.references.map(ref => `<span class="ref-tag">${escapeHtml(ref)}</span>`).join("")}
                        </div>
                    ` : ''}
                `;
                reviewIssuesEl.appendChild(card);
            });
        } else {
            reviewIssuesEl.innerHTML = "<div style='color: var(--earth-teal); font-size: 13px;'>No major discrepancies identified. Cohesion is optimal.</div>";
        }
    }

    // Bind Export project button
    const exportBtn = document.getElementById("export-project-btn");
    if (exportBtn) {
        const newBtn = exportBtn.cloneNode(true);
        exportBtn.parentNode.replaceChild(newBtn, exportBtn);
        newBtn.addEventListener("click", () => {
            exportProjectToZip(project);
        });
    }

    const firstTabBtn = document.querySelector(".details-tabs button[data-tab='details-narrative']");
    if (firstTabBtn) firstTabBtn.click();

    modal.classList.remove("hidden");
}

(function initDetailsModalEvents() {
    const closeBtn = document.getElementById("close-details-btn");
    const modal = document.getElementById("project-details-modal");

    if (closeBtn && modal) {
        closeBtn.addEventListener("click", () => {
            modal.classList.add("hidden");
        });
        modal.addEventListener("click", (e) => {
            if (e.target === modal) modal.classList.add("hidden");
        });
    }

    const tabBtns = document.querySelectorAll(".details-tabs .tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const contents = document.querySelectorAll(".details-content-wrapper .tab-content");
            contents.forEach(c => c.classList.add("hidden"));

            const targetId = btn.getAttribute("data-tab");
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.remove("hidden");
            }
        });
    });
})();

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return "";
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
    } catch {
        return dateStr;
    }
}

/* ==========================================
   BROWSE PROJECTS ACTION CARD
========================================== */

(function initBrowseProjects() {
    const browseCard = document.getElementById("action-browse-projects");
    if (browseCard) {
        browseCard.addEventListener("click", () => {
            // Scroll to the Recent Projects section
            const projectsSection = document.getElementById("projects-list-container");
            if (projectsSection) {
                projectsSection.scrollIntoView({ behavior: "smooth", block: "center" });
                // Flash highlight
                projectsSection.parentElement.style.boxShadow = "0 0 20px rgba(196, 125, 26, 0.3)";
                setTimeout(() => {
                    projectsSection.parentElement.style.boxShadow = "";
                }, 1500);
            }
            fetchAndRenderProjects();
        });
    }
})();

/* ==========================================
   ATLAS ACTION CARD
========================================== */

(function initAtlasCard() {
    const atlasCard = document.getElementById("action-atlas");
    if (atlasCard) {
        atlasCard.addEventListener("click", () => {
            showToast("DreamXV Atlas: Explore worlds, ideas, lore, and inspiration. Coming Soon.", "info");
        });
    }
})();

/* ==========================================
   TOAST NOTIFICATIONS
========================================== */

function showToast(message, type = "info") {
    // Remove existing toasts
    document.querySelectorAll(".toast-notification").forEach(t => t.remove());

    const toast = document.createElement("div");
    toast.className = "toast-notification";

    const icon = type === "success" ? "✓" : type === "error" ? "✕" : "ℹ";
    const borderColor = type === "success"
        ? "var(--earth-teal)"
        : type === "error"
            ? "#f87171"
            : "var(--lunar-gold)";

    toast.style.borderLeftWidth = "3px";
    toast.style.borderLeftColor = borderColor;
    toast.innerHTML = `<span style="margin-right: 8px;">${icon}</span> ${escapeHtml(message)}`;

    document.body.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(10px)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/* ==========================================
   GLOBAL ERROR BOUNDARY
========================================== */

function showErrorBoundary(error) {
    console.error("[Global Error Boundary] Caught exception:", error);

    const boundary = document.getElementById("global-error-boundary");
    const details = document.getElementById("global-error-details");

    if (boundary) {
        if (details) {
            details.textContent = error && error.stack
                ? error.stack
                : (error && error.message ? error.message : String(error));
        }
        boundary.classList.remove("hidden");
    }
}

// Bind global unhandled runtime exceptions
window.addEventListener("error", (event) => {
    showErrorBoundary(event.error || new Error(event.message));
});

window.addEventListener("unhandledrejection", (event) => {
    showErrorBoundary(event.reason || new Error("Unhandled promise rejection"));
});

// Wire the Reset App button inside the error boundary modal
document.addEventListener("DOMContentLoaded", () => {
    const resetBtn = document.getElementById("reset-boundary-btn");
    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            try {
                localStorage.clear();
                showToast("Application cache reset. Reloading...", "success");
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } catch (e) {
                location.reload();
            }
        });
    }
});

/* ==========================================
   INTERNAL AI PROVIDER ROUTER (FALLBACK)
========================================== */

window.AIRouter = {
    providers: [
        { name: "Featherless AI", isFallback: false },
        { name: "AIMLAPI", isFallback: true }
    ],
    async generateContent(prompt, options = {}) {
        console.log(`[AIRouter] Attempting generation with default provider: Featherless AI`);
        try {
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

/* ==========================================
   CLIENT-SIDE MOCK GENERATOR & ZIP EXPORTER
========================================== */

// generateClientSideMockProject removed to prevent demo fallback data.

async function exportProjectToZip(project) {
    if (!window.JSZip) {
        showToast("ZIP library not loaded. Please try again.", "error");
        return;
    }
    
    showToast("Preparing export...", "info");
    
    const zip = new JSZip();
    
    const designFolder = zip.folder("GameDesign");
    const docsFolder = zip.folder("Documentation");
    
    let gddMd = `# Game Design Document: ${project.title || 'Untitled Project'}\n\n`;
    gddMd += `## Elevator Pitch\n${project.documentation?.elevator_pitch || 'N/A'}\n\n`;
    gddMd += `## Story & Narrative\n${project.story?.lore || project.story?.summary || 'N/A'}\n\n`;
    gddMd += `### Acts/Chapters\n`;
    if (project.story?.acts && project.story.acts.length > 0) {
        project.story.acts.forEach((act, idx) => {
            gddMd += `${idx + 1}. ${act}\n`;
        });
    } else {
        gddMd += `N/A\n`;
    }
    gddMd += `\n## World-Building\n${project.world?.description || 'N/A'}\n`;
    gddMd += `*Atmosphere*: ${project.world?.atmosphere || 'N/A'}\n\n`;
    gddMd += `## Gameplay & Mechanics\n`;
    gddMd += `### Core Loop\n${project.gameplay?.core_loop || 'N/A'}\n\n`;
    gddMd += `### Mechanics\n`;
    if (project.gameplay?.mechanics && project.gameplay.mechanics.length > 0) {
        project.gameplay.mechanics.forEach(m => gddMd += `- ${m}\n`);
    } else {
        gddMd += `N/A\n`;
    }
    gddMd += `\n### Progression System\n${project.gameplay?.progression_system || 'N/A'}\n\n`;
    
    designFolder.file("GameDesignDocument.md", gddMd);
    
    docsFolder.file("README.md", project.documentation?.readme || `# ${project.title || 'Untitled Project'}\n\nGenerated by DreamXV AI Studio.`);
    
    zip.file("project_manifest.json", JSON.stringify(project, null, 4));
    
    docsFolder.file("TechnicalSummary.md", `# Technical Architecture\n\n${project.documentation?.technical_summary || 'N/A'}`);
    
    try {
        const content = await zip.generateAsync({ type: "blob" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(content);
        link.download = `${(project.title || "project").toLowerCase().replace(/[^a-z0-9]/g, "_")}_design_kit.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast("Project exported successfully!", "success");
    } catch (err) {
        console.error("ZIP Generation failed:", err);
        showToast("Failed to generate export ZIP.", "error");
    }
}

/* ==========================================
   EXECUTION DASHBOARD & PIPELINE VISUALIZATION
========================================== */

function initExecutionDashboard(agents, startTime) {
    const container = document.getElementById("exec-dashboard-content");
    const totalTimeDiv = document.getElementById("exec-total-time");
    if (!container) return;

    if (totalTimeDiv) totalTimeDiv.style.display = "none";
    
    container.innerHTML = `
        <div class="exec-status-header" style="display: flex; justify-content: space-between; font-family: var(--font-code); font-size: 11px; color: var(--earth-teal); margin-bottom: var(--space-2); border-bottom: 1px solid rgba(26,48,72,0.3); padding-bottom: var(--space-2);">
            <span>AGENT</span>
            <span>STATUS</span>
        </div>
        <div id="exec-dashboard-rows" style="display: flex; flex-direction: column; gap: var(--space-2);">
            ${agents.map(a => `
                <div class="exec-dashboard-row" data-agent-row="${a.agent_name}" style="display: flex; justify-content: space-between; align-items: center; font-size: 13px;">
                    <span style="color: var(--starlight); font-family: var(--font-code);">${a.agent_name}</span>
                    <span class="exec-agent-time font-code" style="color: rgba(240, 232, 208, 0.3);">Queued</span>
                </div>
            `).join("")}
        </div>
    `;
}

function updateExecutionDashboard(agents, startTime) {
    const container = document.getElementById("exec-dashboard-rows");
    if (!container) return;

    const now = Date.now();
    const elapsedTotal = ((now - startTime) / 1000).toFixed(1);
    
    agents.forEach(a => {
        const row = container.querySelector(`[data-agent-row="${a.agent_name}"]`);
        if (row) {
            const timeVal = row.querySelector(".exec-agent-time");
            if (timeVal) {
                if (a.status === "running") {
                    timeVal.textContent = "Running...";
                    timeVal.style.color = "var(--earth-teal)";
                } else if (a.status === "completed") {
                    timeVal.textContent = "Completed";
                    timeVal.style.color = "var(--starlight)";
                } else if (a.status === "error") {
                    timeVal.textContent = "Error";
                    timeVal.style.color = "#f87171";
                } else {
                    timeVal.textContent = "Queued";
                    timeVal.style.color = "rgba(240, 232, 208, 0.3)";
                }
            }
        }
    });

    const totalTimeVal = document.getElementById("exec-total-time-value");
    if (totalTimeVal) totalTimeVal.textContent = `${elapsedTotal}s`;
}

function finalizeExecutionDashboard(startTime) {
    const totalTimeDiv = document.getElementById("exec-total-time");
    if (totalTimeDiv) totalTimeDiv.style.display = "flex";
    
    const now = Date.now();
    const elapsedTotal = ((now - startTime) / 1000).toFixed(1);
    const totalTimeVal = document.getElementById("exec-total-time-value");
    if (totalTimeVal) totalTimeVal.textContent = `${elapsedTotal}s`;
}

function updatePipelineVisualization(agents) {
    agents.forEach(a => {
        const node = document.querySelector(`.pipeline-node[data-agent="${a.agent_name}"]`);
        if (node) {
            node.classList.remove("active", "completed", "error");
            if (a.status === "running") {
                node.classList.add("active");
            } else if (a.status === "completed") {
                node.classList.add("completed");
            } else if (a.status === "error") {
                node.classList.add("error");
            }
        }
    });
}