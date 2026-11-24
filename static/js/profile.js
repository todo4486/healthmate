// The user's profile document in Firestore: users/{uid}
//
// We store only what the app needs:
//   displayName  first name, used for the dashboard greeting (max 60 characters)
//   createdAt    when the profile was created (set by the server)
// The email address and password stay in Firebase Authentication only.

import { loadFirestore } from "./firebase.js";

// "Priya Sharma" -> "Priya". Keeps only the first name, at most 60 characters.
export function firstNameOf(name) {
    return String(name || "").trim().split(/\s+/)[0].slice(0, 60);
}

// Creates the profile the first time a user signs in. Does nothing if it exists.
export async function ensureUserProfile(user, displayName) {
    const { db, sdk } = await loadFirestore();
    const ref = sdk.doc(db, "users", user.uid);
    const existing = await sdk.getDoc(ref);
    if (existing.exists()) {
        return;
    }
    await sdk.setDoc(ref, {
        displayName: firstNameOf(displayName ?? user.displayName),
        createdAt: sdk.serverTimestamp(),
    });
}
