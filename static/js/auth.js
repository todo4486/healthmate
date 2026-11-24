// Sign-in state for every page.
//
//  - Shows "Log in / Sign up" or the user's name and "Log out" in the header.
//  - Private pages (Dashboard, Habits) stay hidden until a user is confirmed,
//    and send signed-out visitors to /login.
//  - Guest-only pages (Login, Register) send signed-in users onwards.
//
// IMPORTANT: this only controls what the browser SHOWS. Anyone can change
// JavaScript in their own browser, so this is not security. User data is
// protected by the Firestore security rules (firestore.rules), which Google
// checks on its servers for every read and write.

import { isConfigured, loadAuth } from "./firebase.js";

const root = document.documentElement;
const pageAccess = document.body.dataset.access || "public";
const HINT_KEY = "hm-auth"; // remembers "signed in" to avoid header flicker

// Pages that must never be used as the place to go after logging in.
const AUTH_PAGES = ["/login", "/register", "/reset-password"];

// While a login or sign-up form is still saving data, it asks us not to
// redirect yet (see auth-forms.js).
let redirectHeld = false;
export function holdRedirect(held) {
    redirectHeld = held;
}

/**
 * Returns a safe place to go after login: a path on THIS site only.
 * Anything else (another website, "//evil.com", "javascript:...") falls back.
 */
export function safeNextPath(value, fallback = "/dashboard") {
    if (typeof value !== "string" || !value.startsWith("/") || value.startsWith("//")) {
        return fallback;
    }
    let url;
    try {
        url = new URL(value, window.location.origin);
    } catch {
        return fallback;
    }
    // The browser tidies odd input (e.g. "/\t/evil.com" or "/..//evil.com" both
    // become "//evil.com"), so check the tidied result is still on our own site
    // and cannot be read as a link to another site.
    if (url.origin !== window.location.origin
        || url.pathname.startsWith("//")
        || AUTH_PAGES.includes(url.pathname)) {
        return fallback;
    }
    return url.pathname + url.search + url.hash;
}

function rememberSignedIn(signedIn) {
    try {
        if (signedIn) {
            localStorage.setItem(HINT_KEY, "user");
        } else {
            localStorage.removeItem(HINT_KEY);
        }
    } catch {
        // Storage can be blocked (e.g. private browsing). The hint is optional.
    }
}

function showUser(user) {
    root.dataset.auth = user ? "user" : "guest";
    rememberSignedIn(Boolean(user));

    const name = user ? (user.displayName || user.email || "") : "";
    const firstName = name.split(/[\s@]/)[0] || "there";

    document.querySelectorAll("[data-user-name]").forEach((el) => {
        el.textContent = name;
        el.title = name;
    });
    document.querySelectorAll("[data-user-initial]").forEach((el) => {
        el.textContent = firstName.charAt(0).toUpperCase();
    });
    document.querySelectorAll("[data-user-first-name]").forEach((el) => {
        el.textContent = firstName;
    });
}

// Replaces the "Checking your sign-in…" message on private pages.
function showPrivateMessage(title, text) {
    const loading = document.querySelector("[data-auth-loading]");
    if (!loading) {
        return;
    }
    const heading = document.createElement("h1");
    heading.textContent = title;
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    const home = document.createElement("a");
    home.className = "btn btn--primary";
    home.href = "/";
    home.textContent = "Go to the home page";
    const actions = document.createElement("div");
    actions.className = "cluster";
    actions.append(home);

    loading.className = "container message-page";
    loading.removeAttribute("role");
    loading.replaceChildren(heading, paragraph, actions);
}

function revealPrivateContent() {
    document.querySelector("[data-auth-loading]")?.remove();
    const content = document.querySelector("[data-private-content]");
    if (content) {
        content.hidden = false;
    }
}

function applyPageAccess(user) {
    if (pageAccess === "private") {
        if (user) {
            revealPrivateContent();
        } else {
            const next = encodeURIComponent(window.location.pathname);
            window.location.replace(`/login?next=${next}`);
        }
    } else if (pageAccess === "guest-only" && user && !redirectHeld) {
        const params = new URLSearchParams(window.location.search);
        window.location.replace(safeNextPath(params.get("next")));
    }
}

function setUpLogout(auth, sdk) {
    document.querySelectorAll("[data-logout]").forEach((button) => {
        button.addEventListener("click", async () => {
            button.disabled = true;
            try {
                await sdk.signOut(auth);
                rememberSignedIn(false);
                window.location.assign("/");
            } catch (error) {
                console.error("Logout failed", error);
                button.disabled = false;
            }
        });
    });
}

// Resolves with the signed-in user (or null) once Firebase has checked.
export const currentUser = new Promise((resolve) => {
    if (!isConfigured) {
        showUser(null);
        if (pageAccess === "private") {
            showPrivateMessage(
                "Sign-in isn't available yet",
                "This page needs an account, but Firebase hasn't been set up for this site yet.",
            );
        }
        resolve(null);
        return;
    }

    loadAuth()
        .then(({ auth, sdk }) => {
            setUpLogout(auth, sdk);
            let firstCheck = true;
            sdk.onAuthStateChanged(auth, (user) => {
                showUser(user);
                applyPageAccess(user);
                if (firstCheck) {
                    firstCheck = false;
                    resolve(user);
                }
            });
        })
        .catch((error) => {
            console.error("Could not load Firebase", error);
            showUser(null);
            if (pageAccess === "private") {
                showPrivateMessage(
                    "We couldn't check your sign-in",
                    "Check your internet connection, then reload the page.",
                );
            }
            resolve(null);
        });
});
