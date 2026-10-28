(() => {
  const widget = document.querySelector(".chat-widget");
  if (!widget) return;

  const panel = document.getElementById("chat-panel");
  const launcher = widget.querySelector(".chat-launcher");
  const closeButton = widget.querySelector(".chat-close");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("chat-messages");
  const feedback = document.getElementById("chat-feedback");
  const feedbackStatus = document.getElementById("feedback-status");
  const conversationId = window.crypto?.randomUUID
    ? window.crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

  function csrfToken() {
    const cookie = document.cookie.split("; ").find((item) => item.startsWith("csrftoken="));
    return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
  }

  function addMessage(text, kind) {
    const message = document.createElement("p");
    message.className = `chat-message chat-${kind}`;
    message.textContent = text;
    messages.append(message);
    messages.scrollTop = messages.scrollHeight;
  }

  launcher.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    launcher.setAttribute("aria-expanded", String(!panel.hidden));
    if (!panel.hidden) input.focus();
  });

  document.querySelectorAll("[data-open-assistant]").forEach((button) => {
    button.addEventListener("click", () => {
      panel.hidden = false;
      launcher.setAttribute("aria-expanded", "true");
      input.focus();
    });
  });

  closeButton.addEventListener("click", () => {
    panel.hidden = true;
    launcher.setAttribute("aria-expanded", "false");
    launcher.focus();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, "user");
    input.value = "";
    input.disabled = true;
    form.querySelector("button").disabled = true;
    feedback.hidden = true;

    try {
      const response = await fetch(widget.dataset.chatUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
        body: JSON.stringify({ message: question, conversation_id: conversationId }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "The assistant could not process that question.");
      addMessage(data.answer, "answer");
      if (!data.log_saved) addMessage("Chat logging is not configured right now.", "notice");
      feedback.hidden = false;
      feedbackStatus.textContent = "";
    } catch (error) {
      addMessage(error.message || "The assistant is unavailable. Please try again.", "notice");
    } finally {
      input.disabled = false;
      form.querySelector("button").disabled = false;
      input.focus();
    }
  });

  feedback.querySelectorAll("[data-rating]").forEach((button) => {
    button.addEventListener("click", async () => {
      feedbackStatus.textContent = "Saving…";
      try {
        const response = await fetch(widget.dataset.feedbackUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
          body: JSON.stringify({
            rating: Number(button.dataset.rating),
            conversation_id: conversationId,
          }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Feedback could not be saved.");
        feedbackStatus.textContent = "Thanks!";
      } catch (error) {
        feedbackStatus.textContent = error.message || "Feedback could not be saved.";
      }
    });
  });
})();
