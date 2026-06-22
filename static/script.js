

// ================= DEPARTMENT BUTTONS =================

// ================= HERO BACKGROUND SLIDER =================

document.addEventListener("DOMContentLoaded", function () {
  const hero = document.getElementById("hero");

  if (!hero) return;

  const images = [
    "/static/images/ml_23_4.jpeg",
    "/static/images/ai_24_3.jpeg",
    "/static/images/dl_23_5.jpeg"
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
function openPopup(event, el) {
  if (event) event.stopPropagation();

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

  // Container for message + actions
  const wrapper = document.createElement('div');
  wrapper.className = 'chat-message-wrapper ' + type;

  const messageElement = document.createElement("div");
  messageElement.className = 'chat-message-text';
  messageElement.textContent = text;

  // Copy button
  const copyBtn = document.createElement('button');
  copyBtn.className = 'chat-copy-btn';
  copyBtn.title = 'Copy message';
  copyBtn.innerText = 'Copy';
  copyBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    navigator.clipboard.writeText(text).then(function () {
      copyBtn.innerText = 'Copied';
      setTimeout(() => copyBtn.innerText = 'Copy', 1500);
    }).catch(() => {
      alert('Copy failed.');
    });
  });

  wrapper.appendChild(messageElement);
  wrapper.appendChild(copyBtn);
  messages.appendChild(wrapper);

  // Scroll to bottom
  messages.scrollTop = messages.scrollHeight;
}

// ================= NEW BACKEND-COMPATIBLE LOGIN =================

document.getElementById("login-form")?.addEventListener("submit", async function (e) {
    e.preventDefault();

    const uid = e.target.uid.value;
    const password = e.target.password.value;
    const role = e.target.role.value; // "student" or "faculty"

    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                uid: uid,
                password: password,
                role: role
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

// ================= PREVIOUS YEAR PAPERS ENHANCEMENTS =================

/**
 * Toggles the visibility of the Add Paper form for Faculty
 */
function toggleAddPaperForm() {
    const formContainer = document.getElementById("add-paper-form-container");
    if (formContainer) {
        formContainer.style.display = (formContainer.style.display === "none" || formContainer.style.display === "") ? "block" : "none";
    }
}

let activePaperId = null;
let cameraStream = null;

/**
 * Opens the device camera to click a paper image
 */
async function openCamera(paperId) {
    activePaperId = paperId;
    const modal = document.getElementById("camera-modal");
    const video = document.getElementById("camera-stream");
    
    if (!modal || !video) return;

    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        video.srcObject = cameraStream;
        modal.style.display = "flex";
    } catch (err) {
        alert("Could not access camera. Please ensure permissions are granted.");
    }
}

function closeCamera() {
    const modal = document.getElementById("camera-modal");
    if (modal) modal.style.display = "none";
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
    }
}

/**
 * Captures the current frame from the video stream and uploads it
 */
function captureAndUpload() {
    const video = document.getElementById("camera-stream");
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    
    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append("paper_id", activePaperId);
        formData.append("image", blob, "paper_capture.jpg");

        fetch("/upload-paper-camera", { method: "POST", body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert("Paper photo uploaded!");
                location.reload();
            } else {
                alert("Error: " + data.message);
            }
            closeCamera();
        });
    }, "image/jpeg");
}

/**
 * Generates AI project descriptions and handles service busy states
 */
async function generateAIDescription(button, titleInputId, featuresInputId, targetTextAreaId) {
    const title = document.getElementById(titleInputId)?.value;
    const features = document.getElementById(featuresInputId)?.value;
    const target = document.getElementById(targetTextAreaId);

    if (!title || !features) {
        alert("Please provide both a project title and key features first.");
        return;
    }

    const originalText = button.innerText;
    button.innerText = "Generating...";
    button.disabled = true;

    try {
        const response = await fetch("/generate_project_description", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, features })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            alert(`Server Error (${response.status}): ${errorData.error || "Unknown server error"}`);
            return;
        }

        const data = await response.json();
        target.value = data.description;

    } catch (err) {
        console.error("AI Generation Fetch Error:", err);
        alert("Network Error: Could not reach the server. Please check if your Flask app is running and your internet connection is stable.");
    } finally {
        button.innerText = originalText;
        button.disabled = false;
    }
}