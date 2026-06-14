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
   BACKEND API CONFIGURATION
========================================== */

const API_CONFIG = {
    // Loaded dynamically from localStorage if present
    baseUrl: safeStorage.getItem("dreamxv_backend_url") || "",
    
    getUrl(path) {
        const base = this.baseUrl ? this.baseUrl.replace(/\/$/, "") : "";
        const cleanPath = path.startsWith("/") ? path : `/${path}`;
        return base ? `${base}${cleanPath}` : cleanPath;
    }
};

/* ==========================================
   CREATE PROJECT MODAL
========================================== */

(function initCreateProjectModal() {
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

            // Get user from session
            const user = safeJsonParse(safeStorage.getItem("dreamxv_user"));
            const userId = user ? user.email : "anonymous";

            try {
                const response = await fetch(API_CONFIG.getUrl("/generate-project"), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ prompt: prompt, user_id: userId }),
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => ({}));
                    throw new Error(errData.detail || `Server error: ${response.status}`);
                }

                const data = await response.json();
                console.log("[DreamXV] Project generation started:", data);

                // Show progress section
                if (progressSection) {
                    progressSection.style.display = "block";
                    updateModalAgentStatus([
                        { agent_name: "Chief Agent", status: "running" },
                        { agent_name: "Story Agent", status: "ready" },
                        { agent_name: "Character Agent", status: "ready" },
                        { agent_name: "World Agent", status: "ready" },
                        { agent_name: "Gameplay Agent", status: "ready" },
                        { agent_name: "Art Agent", status: "ready" },
                        { agent_name: "QA Agent", status: "ready" },
                    ]);
                }

                showToast("Project generation started! Agents are working...", "success");

                // Start polling agent status
                startStatusPolling();

                // Update dashboard agent status panel
                updateAgentStatusPanel([
                    { agent_name: "Chief Agent", status: "running" },
                    { agent_name: "Story Agent", status: "ready" },
                    { agent_name: "Character Agent", status: "ready" },
                    { agent_name: "World Agent", status: "ready" },
                    { agent_name: "Gameplay Agent", status: "ready" },
                    { agent_name: "Art Agent", status: "ready" },
                    { agent_name: "QA Agent", status: "ready" },
                ]);

            } catch (err) {
                console.error("[DreamXV] Generation failed:", err);
                resetSubmitButton();

                if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
                    showError("Cannot reach the backend server. Make sure the API is running and the URL is configured in API_CONFIG.");
                } else {
                    showError(err.message || "Generation failed. Please try again.");
                }
            }
        });
    }
})();

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
            const response = await fetch(API_CONFIG.getUrl("/agent-status"));
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

    try {
        const response = await fetch(API_CONFIG.getUrl("/projects"));
        if (!response.ok) return;

        const data = await response.json();

        if (data.projects && data.projects.length > 0) {
            // Hide empty state, show project cards
            if (emptyState) emptyState.style.display = "none";

            // Remove any existing project cards (but keep empty state in DOM)
            container.querySelectorAll(".project-list-card").forEach(c => c.remove());

            data.projects.forEach(p => {
                const card = document.createElement("div");
                card.className = "project-list-card";
                card.innerHTML = `
                    <div>
                        <div class="project-title">${escapeHtml(p.title || "Untitled")}</div>
                        <div class="project-date">${formatDate(p.created_at)}</div>
                    </div>
                    <span class="project-status">${p.status || "completed"}</span>
                `;
                container.appendChild(card);
            });
        } else {
            // Show empty state
            if (emptyState) emptyState.style.display = "flex";
        }
    } catch (err) {
        // Backend not available — show empty state silently
        console.log("[DreamXV] Projects fetch skipped (backend unavailable)");
        if (emptyState) emptyState.style.display = "flex";
    }
}

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
   SETTINGS ACTION CARD
========================================== */

(function initSettings() {
    const settingsCard = document.getElementById("action-settings");
    if (settingsCard) {
        settingsCard.addEventListener("click", () => {
            showToast("Settings panel coming soon. Configure API keys in the backend .env file.", "info");
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
   WEBSOCKET CONNECTION (REAL-TIME STATUS)
========================================== */

let _activeWebSocket = null;
let _wsReconnectTimeout = null;

function connectWebSocket() {
    // Clear any pending reconnects
    if (_wsReconnectTimeout) {
        clearTimeout(_wsReconnectTimeout);
        _wsReconnectTimeout = null;
    }

    // Close existing connection
    if (_activeWebSocket) {
        try {
            _activeWebSocket.onclose = null; // Prevent reconnect loop from old socket closing
            _activeWebSocket.close();
        } catch (e) {
            console.error("[DreamXV] Error closing old WebSocket:", e);
        }
        _activeWebSocket = null;
    }

    let wsUrl = "";
    if (!API_CONFIG.baseUrl) {
        const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        wsUrl = `${wsProtocol}//${window.location.host}/ws/status`;
    } else {
        const wsBase = API_CONFIG.baseUrl.replace(/^http/, "ws");
        wsUrl = `${wsBase}/ws/status`;
    }

    try {
        console.log(`[DreamXV] Attempting WebSocket connection to: ${wsUrl}`);
        const ws = new WebSocket(wsUrl);
        _activeWebSocket = ws;

        ws.onopen = () => {
            console.log("[DreamXV] WebSocket connected for real-time status");
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "agent_status") {
                    const panel = document.getElementById("agent-status-list");
                    if (panel) {
                        const items = panel.querySelectorAll(".agent-status-item");
                        items.forEach(item => {
                            const nameEl = item.querySelector(".agent-role");
                            if (nameEl && nameEl.textContent.trim() === data.agent_name) {
                                const badge = item.querySelector(".status-badge");
                                if (badge) {
                                    badge.className = `status-badge ${STATUS_COLORS[data.status] || "status-ready"}`;
                                    badge.textContent = capitalize(data.status);
                                }
                            }
                        });
                    }
                }
            } catch (err) {
                // Non-JSON message, ignore
            }
        };

        ws.onerror = () => {
            console.log("[DreamXV] WebSocket error (backend may not be running or domain mismatch)");
        };

        ws.onclose = () => {
            console.log("[DreamXV] WebSocket closed. Reconnecting in 10 seconds...");
            _wsReconnectTimeout = setTimeout(() => connectWebSocket(), 10000);
        };
    } catch (err) {
        console.log("[DreamXV] WebSocket connection failed:", err);
    }
}

// Initial connection
connectWebSocket();

/* ==========================================
   SETTINGS MODAL CONTROLLER
========================================== */

(function initSettingsModal() {
    const modal = document.getElementById("settings-modal");
    const settingsCard = document.getElementById("action-settings");
    const closeBtn = document.getElementById("close-settings-btn");
    const cancelBtn = document.getElementById("cancel-settings-btn");
    const saveBtn = document.getElementById("save-settings-btn");
    const backendUrlInput = document.getElementById("settings-backend-url");

    if (!modal) return;

    function openSettingsModal() {
        if (backendUrlInput) {
            backendUrlInput.value = safeStorage.getItem("dreamxv_backend_url") || "";
        }
        modal.classList.remove("hidden");
    }

    function closeSettingsModal() {
        modal.classList.add("hidden");
    }

    if (settingsCard) {
        settingsCard.addEventListener("click", openSettingsModal);
    }

    if (closeBtn) closeBtn.addEventListener("click", closeSettingsModal);
    if (cancelBtn) cancelBtn.addEventListener("click", closeSettingsModal);
    
    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeSettingsModal();
    });

    if (saveBtn) {
        saveBtn.addEventListener("click", () => {
            const url = backendUrlInput ? backendUrlInput.value.trim() : "";
            
            // Validate URL format (if not empty)
            if (url) {
                try {
                    new URL(url);
                } catch (_) {
                    showToast("Please enter a valid URL (e.g. http://localhost:8000)", "error");
                    return;
                }
            }

            safeStorage.setItem("dreamxv_backend_url", url);
            API_CONFIG.baseUrl = url;
            
            showToast("Settings saved successfully!", "success");
            closeSettingsModal();

            // Refresh projects and reconnect websocket
            fetchAndRenderProjects();
            connectWebSocket();
        });
    }
})();

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