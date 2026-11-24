// Turns Firebase Authentication error codes into plain-English messages.

export const MIN_PASSWORD_LENGTH = 8;

// Returns "" for errors that need no message (e.g. the user closed the popup).
export function friendlyError(error) {
    const code = error?.code || "";
    const messages = {
        "auth/invalid-credential": "Email or password is incorrect.",
        "auth/wrong-password": "Email or password is incorrect.",
        "auth/user-not-found": "Email or password is incorrect.",
        "auth/invalid-email": "Enter a valid email address.",
        "auth/missing-password": "Enter your password.",
        "auth/email-already-in-use":
            "An account with this email already exists. Try logging in instead.",
        "auth/weak-password": `Choose a stronger password of at least ${MIN_PASSWORD_LENGTH} characters.`,
        "auth/too-many-requests": "Too many attempts. Please wait a few minutes and try again.",
        "auth/network-request-failed":
            "We can't reach the server. Check your internet connection and try again.",
        "auth/popup-blocked":
            "Your browser blocked the Google sign-in window. Allow pop-ups for this site and try again.",
        "auth/operation-not-allowed": "This sign-in method isn't turned on for HealthMate yet.",
        "auth/unauthorized-domain":
            "Sign-in isn't allowed from this web address yet. It must be added in Firebase.",
        "auth/user-disabled": "This account has been disabled.",
        "auth/account-exists-with-different-credential":
            "An account already uses this email. Log in the way you did before.",
        "auth/popup-closed-by-user": "",
        "auth/cancelled-popup-request": "",
    };
    if (code in messages) {
        return messages[code];
    }
    if (code.startsWith("auth/api-key") || code === "auth/invalid-api-key"
        || code === "auth/configuration-not-found") {
        return "Sign-in isn't set up correctly. Please check the Firebase settings.";
    }
    console.error("Unexpected sign-in error", error);
    return "Something went wrong. Please try again.";
}
