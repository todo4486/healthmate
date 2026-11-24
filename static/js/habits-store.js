// Reading and saving habits in Firestore. Used by the Habit Tracker and the
// Dashboard, so both always show the same data.
//
// Data structure (all under the signed-in user's own document):
//
//   users/{uid}/habits/{habitId}
//       name       "Drink 8 glasses of water" (1-60 characters)
//       category   "hydration" | "sleep" | "exercise" | "nutrition" | "mental" | "other"
//       createdAt  set by the server
//
//   users/{uid}/habitLogs/{YYYY-MM-DD}
//       completed  [habitId, habitId, ...]   habits ticked off on that day
//       updatedAt  set by the server
//
// One small log document per day keeps "done today" simple: ticking a habit
// adds its id to today's list, unticking removes it.

import { loadFirestore } from "./firebase.js";

export const MAX_HABITS = 20;
export const MAX_NAME_LENGTH = 60;
export const CATEGORIES = ["hydration", "sleep", "exercise", "nutrition", "mental", "other"];

// Today's date in the user's own time zone, e.g. "2026-11-24".
export function todayKey(date = new Date()) {
    const pad = (number) => String(number).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/**
 * Calls onChange({ habits, completedIds }) now and whenever the habits or
 * today's ticks change (also when changed in another tab).
 * Returns a function that stops listening.
 */
export async function watchHabits(uid, onChange, onError) {
    const { db, sdk } = await loadFirestore();
    let habits = null;
    let completedIds = null;

    const emit = () => {
        if (habits !== null && completedIds !== null) {
            // Ignore ticks for habits that have since been deleted.
            const ids = new Set(habits.map((habit) => habit.id));
            onChange({ habits, completedIds: new Set([...completedIds].filter((id) => ids.has(id))) });
        }
    };

    const stopHabits = sdk.onSnapshot(
        sdk.collection(db, "users", uid, "habits"),
        (snapshot) => {
            habits = snapshot.docs
                .map((doc) => {
                    const data = doc.data({ serverTimestamps: "estimate" });
                    return {
                        id: doc.id,
                        name: data.name,
                        category: data.category,
                        createdAt: data.createdAt?.toMillis?.() ?? 0,
                    };
                })
                .sort((a, b) => a.createdAt - b.createdAt);
            emit();
        },
        onError,
    );

    const stopLog = sdk.onSnapshot(
        sdk.doc(db, "users", uid, "habitLogs", todayKey()),
        (snapshot) => {
            completedIds = new Set(snapshot.exists() ? snapshot.data().completed || [] : []);
            emit();
        },
        onError,
    );

    return () => {
        stopHabits();
        stopLog();
    };
}

export async function addHabit(uid, name, category) {
    const { db, sdk } = await loadFirestore();
    await sdk.addDoc(sdk.collection(db, "users", uid, "habits"), {
        name,
        category,
        createdAt: sdk.serverTimestamp(),
    });
}

// Marks a habit done (true) or not done (false) for today.
export async function setHabitDone(uid, habitId, done) {
    const { db, sdk } = await loadFirestore();
    await sdk.setDoc(
        sdk.doc(db, "users", uid, "habitLogs", todayKey()),
        {
            completed: done ? sdk.arrayUnion(habitId) : sdk.arrayRemove(habitId),
            updatedAt: sdk.serverTimestamp(),
        },
        { merge: true },
    );
}

// Deletes a habit and removes it from today's ticks.
export async function deleteHabit(uid, habitId) {
    const { db, sdk } = await loadFirestore();
    await sdk.deleteDoc(sdk.doc(db, "users", uid, "habits", habitId));
    try {
        await setHabitDone(uid, habitId, false);
    } catch (error) {
        // Not important: ticks for deleted habits are ignored anyway.
        console.warn("Could not tidy today's log", error);
    }
}

// Reloads the page just after midnight, so a page left open overnight
// starts showing (and saving) the new day instead of yesterday.
export function reloadAtMidnight() {
    const now = new Date();
    const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 5);
    setTimeout(() => window.location.reload(), midnight - now);
}
