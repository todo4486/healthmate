// Login, sign-up and password-reset forms, plus "Continue with Google".
// Loaded only on /login, /register and /reset-password.

import { isConfigured, loadAuth } from "./firebase.js";
import { holdRedirect, safeNextPath } from "./auth.js";
import { ensureUserProfile, firstNameOf } from "./profile.js";
import { MIN_PASSWORD_LENGTH, friendlyError } from "./auth-errors.js";
import {
    EMAIL_PATTERN, clearFieldErrors, focusFirstError, setBusy, setFieldError, showMessage,
} from "./forms.js";

const message = document.querySelector("[data-form-message]");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const resetForm = document.getElementById("reset-form");
const googleButton = document.querySelector("[data-google-signin]");

function nextPage() {
    return safeNextPath(new URLSearchParams(window.location.search).get("next"));
}

// Saves the profile, then leaves the page. A profile failure (e.g. Firestore
// rules not published yet) is logged but does not block signing in.
async function finishSignIn(user, displayName) {
    try {
        await ensureUserProfile(user, displayName);
    } catch (error) {
        console.warn("Signed in, but the profile could not be saved:", error.code || error);
    }
    window.location.assign(nextPage());
}

// Runs one sign-in attempt with a busy button and friendly errors.
async function attempt(button, busyLabel, action) {
    showMessage(message, "");
    setBusy(button, true, busyLabel);
    holdRedirect(true);
    try {
        await action();
    } catch (error) {
        holdRedirect(false);
        setBusy(button, false);
        const text = friendlyError(error);
        if (text) {
            showMessage(message, text, "warn");
        }
    }
}

// ---------- Validation ----------

function validateEmail(form) {
    const email = form.elements.email.value.trim();
    if (!email) {
        setFieldError(form, "email", "Enter your email address.");
    } else if (!EMAIL_PATTERN.test(email)) {
        setFieldError(form, "email", "Enter a valid email address, like name@example.com.");
    }
    return email;
}

function validateLogin(form) {
    clearFieldErrors(form);
    const email = validateEmail(form);
    const password = form.elements.password.value;
    if (!password) {
        setFieldError(form, "password", "Enter your password.");
    }
    return { email, password };
}

function validateRegister(form) {
    clearFieldErrors(form);
    const name = firstNameOf(form.elements.name.value);
    const email = validateEmail(form);
    const password = form.elements.password.value;
    const confirm = form.elements.confirm.value;

    if (!name) {
        setFieldError(form, "name", "Enter your first name.");
    }
    if (password.length < MIN_PASSWORD_LENGTH) {
        setFieldError(form, "password", `Use at least ${MIN_PASSWORD_LENGTH} characters.`);
    }
    if (!confirm) {
        setFieldError(form, "confirm", "Enter your password again.");
    } else if (confirm !== password) {
        setFieldError(form, "confirm", "The passwords don't match.");
    }
    if (!form.elements.acknowledge.checked) {
        setFieldError(form, "acknowledge", "Please confirm you understand this before continuing.");
    }
    return { name, email, password };
}

function hasErrors(form) {
    const invalid = form.querySelector('[aria-invalid="true"]');
    if (invalid) {
        focusFirstError(form);
    }
    return Boolean(invalid);
}

// ---------- Form handlers ----------

loginForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const { email, password } = validateLogin(loginForm);
    if (hasErrors(loginForm)) {
        return;
    }
    const button = loginForm.querySelector('[type="submit"]');
    attempt(button, "Logging in…", async () => {
        const { auth, sdk } = await loadAuth();
        const result = await sdk.signInWithEmailAndPassword(auth, email, password);
        await finishSignIn(result.user);
    });
});

registerForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const { name, email, password } = validateRegister(registerForm);
    if (hasErrors(registerForm)) {
        return;
    }
    const button = registerForm.querySelector('[type="submit"]');
    attempt(button, "Creating account…", async () => {
        const { auth, sdk } = await loadAuth();
        const result = await sdk.createUserWithEmailAndPassword(auth, email, password);
        // The account now exists, so a failure here must not stop the user.
        try {
            await sdk.updateProfile(result.user, { displayName: name });
        } catch (error) {
            console.warn("Account created, but the name could not be saved:", error.code || error);
        }
        await finishSignIn(result.user, name);
    });
});

resetForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearFieldErrors(resetForm);
    const email = validateEmail(resetForm);
    if (hasErrors(resetForm)) {
        return;
    }
    const button = resetForm.querySelector('[type="submit"]');
    showMessage(message, "");
    setBusy(button, true, "Sending…");
    try {
        const { auth, sdk } = await loadAuth();
        await sdk.sendPasswordResetEmail(auth, email);
        resetForm.reset();
        showSentMessage();
    } catch (error) {
        // Never reveal whether an account exists for this email.
        if (error.code === "auth/user-not-found") {
            showSentMessage();
        } else {
            showMessage(message, friendlyError(error), "warn");
        }
    } finally {
        setBusy(button, false);
    }
});

function showSentMessage() {
    showMessage(
        message,
        "If an account exists for that email, we've sent a link to reset your password. "
            + "Check your inbox and spam folder.",
        "ok",
    );
}

googleButton?.addEventListener("click", () => {
    attempt(googleButton, "Opening Google…", async () => {
        const { auth, sdk } = await loadAuth();
        const result = await sdk.signInWithPopup(auth, new sdk.GoogleAuthProvider());
        await finishSignIn(result.user);
    });
});

// ---------- Not configured ----------

if (!isConfigured) {
    showMessage(
        message,
        "Sign-in isn't available yet because Firebase hasn't been set up for this site.",
        "info",
    );
    document.querySelectorAll('form button[type="submit"], [data-google-signin]').forEach((button) => {
        button.disabled = true;
    });
}
