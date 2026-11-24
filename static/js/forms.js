// Small helpers shared by every form: field errors, messages and busy buttons.

export const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Shows (or clears, with "") the error under a field.
export function setFieldError(form, name, message) {
    const error = form.querySelector(`#${name}-error`);
    if (error) {
        error.textContent = message;
    }
    form.querySelectorAll(`[name="${name}"]`).forEach((input) => {
        input.setAttribute("aria-invalid", message ? "true" : "false");
    });
}

export function clearFieldErrors(form) {
    form.querySelectorAll(".field-error").forEach((error) => {
        error.textContent = "";
    });
    form.querySelectorAll("[aria-invalid]").forEach((input) => {
        input.setAttribute("aria-invalid", "false");
    });
}

// Moves keyboard focus to the first field with an error.
export function focusFirstError(form) {
    form.querySelector('[aria-invalid="true"]')?.focus();
}

// Shows a message in a banner. type: "warn", "ok", "danger" or "info".
export function showMessage(element, text, type = "warn") {
    if (!element) {
        return;
    }
    element.className = `banner banner--${type} form-message`;
    element.textContent = text;
}

const originalContents = new WeakMap();

// Disables a button and shows a spinner while work is in progress.
export function setBusy(button, busy, busyLabel) {
    if (!button) {
        return;
    }
    if (busy) {
        // Keep the original contents (which may include an icon) to put back later.
        originalContents.set(button, [...button.childNodes]);
        button.textContent = busyLabel;
        button.setAttribute("aria-busy", "true");
        button.disabled = true;
    } else {
        if (originalContents.has(button)) {
            button.replaceChildren(...originalContents.get(button));
            originalContents.delete(button);
        }
        button.removeAttribute("aria-busy");
        button.disabled = false;
    }
}
