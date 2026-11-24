// Dashboard: today's overview, habits (tickable here too) and saved symptom checks.
// Every number comes from the signed-in user's Firestore data. Nothing is made up.

import { currentUser } from "./auth.js";
import { firestoreErrorMessage } from "./firebase.js";
import { reloadAtMidnight, watchHabits } from "./habits-store.js";
import { renderHabits, renderProgress } from "./habit-view.js";
import { HISTORY_LIMIT, deleteSymptomCheck, watchSymptomChecks } from "./symptoms-store.js";

const labels = JSON.parse(document.getElementById("symptom-labels").textContent);
const LEVEL_TAGS = {
    urgent: ["tag--danger", "Urgent care advised"],
    doctor: ["tag--warn", "See a doctor"],
    self_care: ["tag--ok", "Self-care"],
};

const errorBanner = document.querySelector("[data-dashboard-error]");
const stat = (key) => document.querySelector(`[data-stat="${key}"]`);

function showError(message) {
    errorBanner.querySelector("[data-dashboard-error-text]").textContent = message;
    errorBanner.hidden = !message;
}

document.querySelector("[data-today]").textContent = new Date().toLocaleDateString(undefined, {
    weekday: "long", day: "numeric", month: "long",
});

// ---------- Habits ----------

function showHabits(uid, state) {
    const done = state.habits.filter((habit) => state.completedIds.has(habit.id)).length;
    const total = state.habits.length;
    stat("done").textContent = String(done);
    stat("total").textContent = String(total);
    stat("percent").textContent = total ? `${Math.round((done / total) * 100)}%` : "–";

    document.querySelector("[data-habits-loading]").hidden = true;
    document.querySelector("[data-habits-empty]").hidden = total > 0;
    renderProgress(document.querySelector("[data-habit-summary]"), state);
    renderHabits(document.querySelector("[data-habit-list]"), state, { uid, onError: showError });
}

// ---------- Symptom checks ----------

function describeCheck(check) {
    const symptoms = (check.symptoms || []).map((id) => labels.symptoms[id] || "Other");
    const details = [labels.durations[check.duration], labels.severities[check.severity]]
        .filter(Boolean).join(" · ");
    return { symptoms: symptoms.join(", "), details };
}

function showChecks(uid, checks) {
    const count = checks.length >= HISTORY_LIMIT ? `${HISTORY_LIMIT}+` : String(checks.length);
    stat("checks").textContent = count;
    document.querySelector("[data-checks-loading]").hidden = true;
    document.querySelector("[data-checks-empty]").hidden = checks.length > 0;

    const template = document.getElementById("check-template");
    const list = document.querySelector("[data-check-list]");
    list.replaceChildren(...checks.slice(0, 5).map((check) => {
        const item = template.content.firstElementChild.cloneNode(true);
        const [tagClass, tagText] = LEVEL_TAGS[check.level] || ["", "Result"];
        const level = item.querySelector("[data-check-level]");
        level.classList.add(tagClass);
        level.textContent = tagText;

        const date = item.querySelector("[data-check-date]");
        date.dateTime = check.createdAt.toISOString();
        date.textContent = check.createdAt.toLocaleString(undefined, {
            day: "numeric", month: "short", hour: "numeric", minute: "2-digit",
        });

        const { symptoms, details } = describeCheck(check);
        item.querySelector("[data-check-symptoms]").textContent = symptoms;
        item.querySelector("[data-check-details]").textContent = details;

        const remove = item.querySelector("[data-check-delete]");
        remove.setAttribute("aria-label", `Delete saved check from ${date.textContent}`);
        remove.addEventListener("click", async () => {
            if (!window.confirm("Delete this saved symptom check? This can't be undone.")) {
                return;
            }
            remove.disabled = true;
            try {
                await deleteSymptomCheck(uid, check.id);
            } catch (error) {
                remove.disabled = false;
                showError(firestoreErrorMessage(error));
            }
        });
        return item;
    }));
}

// ---------- Start ----------

function failed(loadingSelector) {
    return (error) => {
        document.querySelector(loadingSelector).hidden = true;
        showError(firestoreErrorMessage(error));
    };
}

const user = await currentUser;
if (user) {
    reloadAtMidnight();
    watchHabits(user.uid, (state) => showHabits(user.uid, state), failed("[data-habits-loading]"))
        .catch(failed("[data-habits-loading]"));
    watchSymptomChecks(user.uid, (checks) => showChecks(user.uid, checks), failed("[data-checks-loading]"))
        .catch(failed("[data-checks-loading]"));
}
