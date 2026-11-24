// Wellness Assistant chat. Sends each question to /api/assistant and shows
// the pre-written answer. Nothing is stored: refreshing the page clears it.

const MAX_LENGTH = 500;

const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const sendButton = form.querySelector('[type="submit"]');
const messages = document.querySelector("[data-chat-messages]");
const welcome = document.querySelector("[data-chat-welcome]");
const suggestions = document.querySelectorAll("[data-chat-suggestion]");

// Small helper: create an element with optional class and text.
// Text is always set with textContent, so it is never treated as HTML.
function el(tag, className, text) {
    const element = document.createElement(tag);
    if (className) {
        element.className = className;
    }
    if (text) {
        element.textContent = text;
    }
    return element;
}

function addBubble(bubble) {
    messages.append(bubble);
    messages.scrollTop = messages.scrollHeight;
    return bubble;
}

function userBubble(text) {
    return addBubble(el("div", "bubble bubble--user", text));
}

function typingBubble() {
    const bubble = el("div", "bubble bubble--assistant");
    bubble.setAttribute("role", "status");
    bubble.setAttribute("aria-label", "The assistant is answering");
    const dots = el("span", "typing");
    dots.append(el("span"), el("span"), el("span"));
    bubble.append(dots);
    return addBubble(bubble);
}

function replyBubble(reply) {
    const urgent = reply.kind === "urgent" || reply.kind === "crisis";
    const bubble = el("div", `bubble bubble--assistant${urgent ? " bubble--urgent" : ""}`);
    bubble.append(el("h3", "", reply.title));
    reply.paragraphs.forEach((text) => bubble.append(el("p", "", text)));

    if (reply.tips.length) {
        const list = el("ul", "check-list");
        reply.tips.forEach((tip) => list.append(el("li", "", `✓ ${tip}`)));
        bubble.append(list);
    }
    // Links only ever point to pages on this site (they come from our own data).
    if (reply.link && reply.link.url.startsWith("/")) {
        const link = el("a", "card__link", reply.link.label);
        link.href = reply.link.url;
        const line = el("p");
        line.append(link);
        bubble.append(line);
    }
    bubble.append(el("p", "bubble__note", reply.disclaimer));
    return bubble;
}

function errorBubble(text) {
    return el("div", "bubble bubble--assistant bubble--error", text);
}

function setWaiting(waiting) {
    input.disabled = waiting;
    sendButton.disabled = waiting;
    sendButton.setAttribute("aria-busy", String(waiting));
    suggestions.forEach((button) => { button.disabled = waiting; });
}

async function ask(text) {
    const question = text.trim();
    if (!question) {
        input.focus();
        return;
    }
    if (question.length > MAX_LENGTH) {
        addBubble(errorBubble(`Please keep your question under ${MAX_LENGTH} characters.`));
        return;
    }

    welcome.hidden = true;
    userBubble(question);
    input.value = "";
    setWaiting(true);
    const typing = typingBubble();

    try {
        const response = await fetch("/api/assistant", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: question }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || "Sorry, something went wrong. Please try again.");
        }
        typing.replaceWith(replyBubble(data));
    } catch (error) {
        const message = error instanceof TypeError
            ? "I couldn't connect. Check your internet connection and try again."
            : error.message;
        typing.replaceWith(errorBubble(message));
    } finally {
        setWaiting(false);
        messages.scrollTop = messages.scrollHeight;
        input.focus();
    }
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    ask(input.value);
});

suggestions.forEach((button) => {
    button.addEventListener("click", () => ask(button.textContent));
});
