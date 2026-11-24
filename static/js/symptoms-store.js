// Saved Symptom Guide results in Firestore.
//
//   users/{uid}/symptomChecks/{checkId}
//       symptoms   ["fever", "cough"]   ids of the symptoms the user ticked
//       duration   "1_3_days"
//       severity   "mild"
//       ageGroup   "18_64"
//       level      "self_care" | "doctor" | "urgent"
//       createdAt  set by the server
//
// Checks are saved ONLY when the user presses "Save to my history".
// The free-text description and warning-sign answers are never saved.

import { loadFirestore } from "./firebase.js";

export const HISTORY_LIMIT = 50;

export async function saveSymptomCheck(uid, check) {
    const { db, sdk } = await loadFirestore();
    await sdk.addDoc(sdk.collection(db, "users", uid, "symptomChecks"), {
        symptoms: check.symptoms,
        duration: check.duration,
        severity: check.severity,
        ageGroup: check.ageGroup,
        level: check.level,
        createdAt: sdk.serverTimestamp(),
    });
}

// Calls onChange(checks) with the newest checks first, now and after changes.
export async function watchSymptomChecks(uid, onChange, onError) {
    const { db, sdk } = await loadFirestore();
    const newestFirst = sdk.query(
        sdk.collection(db, "users", uid, "symptomChecks"),
        sdk.orderBy("createdAt", "desc"),
        sdk.limit(HISTORY_LIMIT),
    );
    return sdk.onSnapshot(
        newestFirst,
        (snapshot) => {
            onChange(snapshot.docs.map((doc) => {
                const data = doc.data({ serverTimestamps: "estimate" });
                return { id: doc.id, ...data, createdAt: data.createdAt?.toDate?.() ?? new Date() };
            }));
        },
        onError,
    );
}

export async function deleteSymptomCheck(uid, checkId) {
    const { db, sdk } = await loadFirestore();
    await sdk.deleteDoc(sdk.doc(db, "users", uid, "symptomChecks", checkId));
}
