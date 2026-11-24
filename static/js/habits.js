// Habit Tracker page: lists the user's habits from Firestore and lets them
// add, tick off, untick and delete habits.

import { currentUser } from "./auth.js";
import {
    CATEGORIES, MAX_HABITS, MAX_NAME_LENGTH,
    addHabit, deleteHabit, reloadAtMidnight, watchHabits,
} from "./habits-store.js";
import { firestoreErrorMessage } from "./firebase.js";
import { renderHabits, renderProgress } from "./habit-view.js";
import { clearFieldErrors, setBusy, setFieldError, showMessage } from "./forms.js";

const list = document.querySelector("[data-habit-list]");
const loading = document.querySelector("[data-habits-loading]");
const emptyState = document.querySelector("[data-habits-empty]");
const progressCard = document.querySelector("[data-habit-summary]");
const errorBanner = document.querySelector("[data-habits-error]");

const addDialog = document.getElementById("add-dialog");
const form = document.getElementById("habit-form");
const formMessage = form.querySelector("[data-form-message]");
const deleteDialog = document.getElementById("delete-dialog");
const deleteMessage = deleteDialog.querySelector("[data-delete-message]");

let uid = null;
let state = { habits: [], completedIds: new Set() };
let habitToDelete = null;

function showError(message) {
    errorBanner.querySelector("[data-habits-error-text]").textContent = message;
    errorBanner.hidden = !message;
}

function render() {
    loading.hidden = true;
    emptyState.hidden = state.habits.length > 0;
    renderProgress(progressCard, state);
    renderHabits(list, state, { uid, onDelete: confirmDelete, onError: showError });
}

// ---------- Add a habit ----------

function openAddDialog() {
    form.reset();
    clearFieldErrors(form);
    showMessage(formMessage, "");
    addDialog.showModal();
    form.elements.name.focus();
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearFieldErrors(form);
    showMessage(formMessage, "");

    const name = form.elements.name.value.trim().replace(/\s+/g, " ");
    const category = form.elements.category.value;

    if (!name) {
        setFieldError(form, "name", "Enter a name for your habit.");
    } else if (name.length > MAX_NAME_LENGTH) {
        setFieldError(form, "name", `Keep it to ${MAX_NAME_LENGTH} characters or fewer.`);
    } else if (state.habits.some((habit) => habit.name.toLowerCase() === name.toLowerCase())) {
        setFieldError(form, "name", "You already have a habit with this name.");
    }
    if (form.querySelector('[aria-invalid="true"]')) {
        form.elements.name.focus();
        return;
    }
    if (!CATEGORIES.includes(category)) {
        showMessage(formMessage, "Please choose a category.");
        return;
    }
    if (state.habits.length >= MAX_HABITS) {
        showMessage(formMessage, `You can have up to ${MAX_HABITS} habits. Delete one to add another.`);
        return;
    }

    const button = form.querySelector('[type="submit"]');
    setBusy(button, true, "Adding…");
    try {
        await addHabit(uid, name, category);
        addDialog.close();
    } catch (error) {
        showMessage(formMessage, firestoreErrorMessage(error));
    } finally {
        setBusy(button, false);
    }
});

// "Ideas" buttons fill in the form.
form.querySelectorAll("[data-habit-idea]").forEach((button) => {
    button.addEventListener("click", () => {
        form.elements.name.value = button.dataset.habitIdea;
        form.elements.category.value = button.dataset.habitIdeaCategory;
        form.elements.name.focus();
    });
});

// ---------- Delete a habit ----------

function confirmDelete(habit) {
    habitToDelete = habit;
    deleteDialog.querySelector("[data-delete-name]").textContent = `"${habit.name}"`;
    showMessage(deleteMessage, "");
    deleteDialog.showModal();
}

deleteDialog.querySelector("[data-confirm-delete]").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    setBusy(button, true, "Deleting…");
    try {
        await deleteHabit(uid, habitToDelete.id);
        deleteDialog.close();
    } catch (error) {
        showMessage(deleteMessage, firestoreErrorMessage(error));
    } finally {
        setBusy(button, false);
    }
});

// ---------- Dialog buttons ----------

document.querySelectorAll("[data-open-add]").forEach((button) => {
    button.addEventListener("click", openAddDialog);
});
document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => button.closest("dialog").close());
});

// ---------- Start ----------

const user = await currentUser;
if (user) {
    reloadAtMidnight();
    uid = user.uid;
    try {
        await watchHabits(
            uid,
            (newState) => {
                state = newState;
                showError("");
                render();
            },
            (error) => {
                loading.hidden = true;
                showError(firestoreErrorMessage(error));
            },
        );
    } catch (error) {
        loading.hidden = true;
        showError(firestoreErrorMessage(error));
    }
}
