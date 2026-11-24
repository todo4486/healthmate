// Loads the Firebase SDK from Google's CDN, only when it is needed.
// There is no npm or build step: the browser imports the files directly.

import { firebaseConfig } from "./firebase-config.js";

const SDK_URL = "https://www.gstatic.com/firebasejs/12.17.1";

// True once all four settings in firebase-config.js have been filled in.
export const isConfigured = ["apiKey", "authDomain", "projectId", "appId"]
    .every((key) => Boolean(firebaseConfig[key]));

let authServices = null;
let firestoreServices = null;

// Returns { auth, sdk } where sdk holds the Firebase Auth functions.
export function loadAuth() {
    if (!isConfigured) {
        return Promise.reject(new Error("Firebase is not configured."));
    }
    authServices ??= Promise.all([
        import(`${SDK_URL}/firebase-app.js`),
        import(`${SDK_URL}/firebase-auth.js`),
    ]).then(([appSdk, authSdk]) => {
        const app = appSdk.initializeApp(firebaseConfig);
        return { app, auth: authSdk.getAuth(app), sdk: authSdk };
    });
    return authServices;
}

// Returns { db, sdk } where sdk holds the Firestore functions.
export function loadFirestore() {
    firestoreServices ??= Promise.all([
        loadAuth(),
        import(`${SDK_URL}/firebase-firestore.js`),
    ]).then(([{ app }, firestoreSdk]) => ({
        db: firestoreSdk.getFirestore(app),
        sdk: firestoreSdk,
    }));
    return firestoreServices;
}

// Friendly message for a failed Firestore request.
export function firestoreErrorMessage(error) {
    switch (error?.code) {
        case "permission-denied":
            return "You don't have permission to do that. If this keeps happening, "
                + "the database security rules may not be published yet.";
        case "unavailable":
        case "deadline-exceeded":
            return "We can't reach the database. Check your internet connection and try again.";
        case "unauthenticated":
            return "Your sign-in has expired. Please log in again.";
        default:
            console.error("Firestore error", error);
            return "Something went wrong while saving or loading your data. Please try again.";
    }
}
