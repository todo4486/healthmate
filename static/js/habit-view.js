// Draws today's habit progress and habit cards. Shared by the Habit Tracker
// and the Dashboard so both look and behave the same.

import { firestoreErrorMessage } from "./firebase.js";
import { setHabitDone } from "./habits-store.js";

export const CATEGORY_LABELS = {
    hydration: "Hydration",
    sleep: "Sleep",
    exercise: "Exercise",
    nutrition: "Nutrition",
    mental: "Mental wellness",
    other: "Other",
};

// Fills in the "Today's progress" card.
export function renderProgress(card, { habits, completedIds }) {
    const total = habits.length;
    const done = habits.filter((habit) => completedIds.has(habit.id)).length;
    const percent = total ? Math.round((done / total) * 100) : 0;

    card.querySelector("[data-today-date]").textContent = new Date().toLocaleDateString(undefined, {
        weekday: "long", day: "numeric", month: "long",
    });
    card.querySelector("[data-habit-count]").textContent = total
        ? `${done} of ${total} habits done`
        : "No habits yet";
    card.querySelector("[data-habit-percent]").textContent = total ? `· ${percent}%` : "";
    card.querySelector("[data-habit-bar]").style.width = `${percent}%`;
    card.querySelector('[role="progressbar"]').setAttribute("aria-valuenow", String(percent));
}

/**
 * Draws one card per habit into `list`.
 * options.uid       the signed-in user's id
 * options.onDelete  called with the habit when its delete button is pressed;
 *                   leave out to hide delete buttons (Dashboard)
 * options.onError   called with a message if saving a tick fails
 */
export function renderHabits(list, { habits, completedIds }, options) {
    const template = document.getElementById("habit-template");
    const focusedId = document.activeElement?.closest?.("[data-id]")?.dataset.id;

    list.replaceChildren(...habits.map((habit) => {
        const done = completedIds.has(habit.id);
        const item = template.content.firstElementChild.cloneNode(true);
        item.dataset.id = habit.id;
        item.classList.toggle("habit--done", done);

        // textContent never interprets HTML, so habit names can't inject code.
        item.querySelector(".habit__name").textContent = habit.name;
        // Unknown categories (e.g. a write the server is about to reject) show as "Other".
        const category = habit.category in CATEGORY_LABELS ? habit.category : "other";
        item.querySelector(".habit__category").textContent = CATEGORY_LABELS[category];
        item.querySelector(".dot").classList.add(`dot--${category}`);

        const check = item.querySelector(".habit__check");
        check.setAttribute("aria-pressed", String(done));
        check.setAttribute("aria-label", done
            ? `Undo: mark "${habit.name}" as not done today`
            : `Mark "${habit.name}" as done today`);
        check.addEventListener("click", async () => {
            check.disabled = true;
            check.setAttribute("aria-busy", "true");
            try {
                await setHabitDone(options.uid, habit.id, !done);
            } catch (error) {
                options.onError?.(firestoreErrorMessage(error));
                check.disabled = false;
                check.removeAttribute("aria-busy");
            }
        });

        const remove = item.querySelector("[data-habit-delete]");
        if (options.onDelete) {
            remove.setAttribute("aria-label", `Delete "${habit.name}"`);
            remove.addEventListener("click", () => options.onDelete(habit));
        } else {
            remove.remove();
        }
        return item;
    }));

    // Keep keyboard focus on the same habit after the list is redrawn.
    if (focusedId) {
        list.querySelector(`[data-id="${CSS.escape(focusedId)}"] .habit__check`)?.focus();
    }
}
