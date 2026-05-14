

// ================= DEPARTMENT BUTTONS =================

// Handle department links (e.g., ACSML / NCSML / DCSML)
function handleDeptLink(event, targetPage) {
  event.preventDefault();

  if (!isLoggedIn()) {
    window.location.href = "login.html";
    return;
  }

  const role = getUserRole();

  // For now, just let both roles go to targetPage
  // If you later add dashboards:
  // if (role === "student") window.location.href = "student-dashboard.html";
  // if (role === "faculty") window.location.href = "faculty-dashboard.html";

  window.location.href = targetPage; // e.g., "ACSML_subpage.html"
}

// ================= HERO BACKGROUND SLIDER =================

document.addEventListener("DOMContentLoaded", function () {
  const hero = document.getElementById("hero");

  if (!hero) return;

  const images = [
    "ml1.jpg",
    "ml2.jpg",
    "ml3.jpg"
  ];

  let index = 0;

  function changeBackground() {
    hero.style.background =
      `url(${images[index]}) center/cover no-repeat`;
    index = (index + 1) % images.length;
  }

  changeBackground();
  setInterval(changeBackground, 4000);
});

// ================= POPUPS (ABOUT, OUTREACH, FACULTY) =================

// Open popup (next sibling with .hide-display)
function openPopup(el) {
  event.stopPropagation();

  const popup = el.nextElementSibling;
  if (popup && popup.classList.contains("hide-display")) {
    popup.classList.add("active");
  }
}

// Click outside → close all popups
document.addEventListener("click", function () {
  document.querySelectorAll(".hide-display.active")
    .forEach(popup => popup.classList.remove("active"));
});

// Prevent closing when clicking inside popup
document.querySelectorAll(".about-pop, .out-reach-pop")
  .forEach(pop =>
    pop.addEventListener("click", e => e.stopPropagation())
  );

/* ---------- SUB BUTTON POPUPS ---------- */
function openSubPopup(event, id) {
  event.stopPropagation();

  // Close all sub popups
  document.querySelectorAll(".hide-display-sub")
    .forEach(p => p.classList.remove("active"));

  // Open selected popup
  const popup = document.getElementById(id);
  if (popup) popup.classList.add("active");
}

// Click outside → close all sub popups
document.addEventListener("click", function () {
  document.querySelectorAll(".hide-display-sub")
    .forEach(p => p.classList.remove("active"));
});

// Prevent closing when clicking inside popup
document.querySelectorAll(".hide-display-sub")
  .forEach(popup => {
    popup.addEventListener("click", e => e.stopPropagation());
  });

/* ---------- VIEW ALL FACULTY BUTTON ---------- */
document.addEventListener("DOMContentLoaded", function () {
  const grid = document.getElementById("facultyGrid");
  const btn = document.getElementById("viewBtn");

  if (!grid || !btn) return;

  // Click → show all faculty
  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    grid.classList.add("show-all");
    btn.style.display = "none";
  });

  // Click anywhere → hide extra faculty
  document.addEventListener("click", function () {
    grid.classList.remove("show-all");
    btn.style.display = "inline-block";
  });

  // Prevent closing when clicking inside faculty grid
  grid.addEventListener("click", function (e) {
    e.stopPropagation();
  });
});

// ================= CHAT FUNCTIONALITY =================

function openChat() {
  const panel = document.getElementById("chat-panel");
  panel.classList.add("visible");
}

function closeChat() {
  const panel = document.getElementById("chat-panel");
  panel.classList.remove("visible");
}

function handleChatEnter(event) {
  if (event.key === "Enter") {
    sendChat();
  }
}

function sendChat() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();

  if (!message) return;

  // Add user message
  addMessage(message, "user");

  // Clear input
  input.value = "";

  // Send to server
  fetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message: message }),
  })
  .then(response => response.json())
  .then(data => {
    // Add bot response
    addMessage(data.reply, "bot");
  })
  .catch(error => {
    console.error("Chat error:", error);
    addMessage("Sorry, I'm having trouble connecting. Please try again.", "bot");
  });
}

function addMessage(text, type) {
  const messages = document.getElementById("chat-messages");
  const messageElement = document.createElement("p");
  messageElement.className = type;
  messageElement.textContent = text;
  messages.appendChild(messageElement);

  // Scroll to bottom
  messages.scrollTop = messages.scrollHeight;
}

// ================= DEPARTMENT BUTTONS =================

async function handleDeptLink(event, targetPage) {
    event.preventDefault();

    // Instead of localStorage, we check if the session is active via an API call
    try {
        // You need to create this simple route in app.py to check status
        const response = await fetch("/check-auth"); 
        const data = await response.json();

        if (!data.logged_in) {
            window.location.href = "/login";
            return;
        }

        // If logged in, proceed to target page
        window.location.href = targetPage;
    } catch (err) {
        console.error("Auth check failed:", err);
        window.location.href = "/login";
    }
}

// ================= NEW BACKEND-COMPATIBLE LOGIN =================

document.getElementById("login-form")?.addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = e.target.username.value;
    const password = e.target.password.value;
    const mode = e.target.mode.value; // "student" or "faculty"

    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password,
                mode: mode
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message);
            // Redirect to the correct backend route
            window.location.href = (data.role === "student") ? "/student-dashboard" : "/faculty-dashboard";
        } else {
            alert("Login Failed: " + data.message);
        }
    } catch (err) {
        console.error("Login error:", err);
        alert("Server connection failed.");
    }
});

document.addEventListener("DOMContentLoaded", async function () {
    const response = await fetch("/check-auth");
    const data = await response.json();
    
    const userNav = document.getElementById("user-nav");
    const loginLink = document.getElementById("login-link");

    if (data.logged_in) {
        if (loginLink) loginLink.style.display = "none";
        if (userNav) userNav.style.display = "flex";
    } else {
        if (loginLink) loginLink.style.display = "inline";
        if (userNav) userNav.style.display = "none";
    }
});