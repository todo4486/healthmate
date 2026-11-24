// Symptom Guide: checks the answers, asks the server for guidance
// (/api/symptom-check), shows the result, and can save it to the user's history.

import { currentUser } from "./auth.js";
import { firestoreErrorMessage } from "./firebase.js";
import { saveSymptomCheck } from "./symptoms-store.js";
import { clearFieldErrors, setBusy, setFieldError, showMessage } from "./forms.js";

const MAX_DETAILS = 500;
const LEVEL_STYLE = { urgent: "banner--danger", doctor: "banner--warn", self_care: "banner--ok" };

const form = document.getElementById("symptom-form");
const formMessage = form.querySelector("[data-form-message]");
const resultArea = document.getElementById("symptom-result");
const template = document.getElementById("result-template");
const noneBox = form.elements.no_warning_signs;

// "None of these" and the warning signs can't both be ticked.
form.addEventListener("change", (event) => {
    if (event.target === noneBox && noneBox.checked) {
        form.querySelectorAll('[name="warning_signs"]').forEach((box) => { box.checked = false; });
    } else if (event.target.name === "warning_signs" && event.target.checked) {
        noneBox.checked = false;
    }
});

// ---------- Validation (the server checks everything again) ----------

function readAnswers() {
    const data = new FormData(form);
    return {
        warning_signs: data.getAll("warning_signs"),
        no_warning_signs: noneBox.checked,
        symptoms: data.getAll("symptoms"),
        details: (data.get("details") || "").trim(),
        duration: data.get("duration"),
        severity: data.get("severity"),
        age_group: data.get("age_group"),
    };
}

function validate(answers) {
    clearFieldErrors(form);
    if (!answers.warning_signs.length && !answers.no_warning_signs) {
        setFieldError(form, "warning_signs", "Tick any warning signs you have, or “None of these”.");
    }
    if (!answers.symptoms.length && !answers.details) {
        setFieldError(form, "symptoms", "Choose at least one symptom, or describe how you feel in step 3.");
    }
    if (answers.details.length > MAX_DETAILS) {
        setFieldError(form, "details", `Please keep this under ${MAX_DETAILS} characters.`);
    }
    if (!answers.duration) {
        setFieldError(form, "duration", "Choose how long you've had your symptoms.");
    }
    if (!answers.severity) {
        setFieldError(form, "severity", "Choose how severe your symptoms are.");
    }
    if (!answers.age_group) {
        setFieldError(form, "age_group", "Choose an age group.");
    }
    const firstError = form.querySelector('[aria-invalid="true"]');
    firstError?.focus();
    return !firstError;
}

// ---------- Result ----------

function fillList(list, items, tag = "li") {
    list.replaceChildren(...items.map((text) => {
        const item = document.createElement(tag);
        item.textContent = text; // textContent: never treated as HTML
        return item;
    }));
}

function addSummaryRow(list, label, value) {
    if (!value || (Array.isArray(value) && !value.length)) {
        return;
    }
    const term = document.createElement("dt");
    term.textContent = label;
    const detail = document.createElement("dd");
    detail.textContent = Array.isArray(value) ? value.join(", ") : value;
    list.append(term, detail);
}

function showResult(result) {
    const view = template.content.firstElementChild.cloneNode(true);
    const q = (selector) => view.querySelector(selector);

    q("[data-level-banner]").classList.add(LEVEL_STYLE[result.level]);
    q("[data-level-icon]").remove();
    q("[data-heading]").textContent = result.heading;
    q("[data-summary]").textContent = result.summary;

    const phrase = result.text_alerts.emergency[0];
    if (phrase) {
        q("[data-text-alert]").hidden = false;
        q("[data-text-alert-text]").textContent = `Your description mentions “${phrase}”. `
            + "If this is happening now, call 112 or go to the nearest emergency department.";
    }
    q("[data-crisis]").hidden = !result.crisis_support;

    fillList(q("[data-next-steps]"), result.next_steps);
    fillList(q("[data-reasons]"), result.reasons);
    fillList(q("[data-watch-for]"), result.watch_for);

    const submitted = q("[data-submitted]");
    addSummaryRow(submitted, "Warning signs", result.submitted.warning_signs.length
        ? result.submitted.warning_signs : "None");
    addSummaryRow(submitted, "Symptoms", result.submitted.symptoms);
    addSummaryRow(submitted, "Your description", result.submitted.details);
    addSummaryRow(submitted, "How long", result.submitted.duration);
    addSummaryRow(submitted, "How severe", result.submitted.severity);
    addSummaryRow(submitted, "Age group", result.submitted.age_group);

    q("[data-disclaimer]").textContent = result.disclaimer;

    // Optional save to history
    const saveButton = q("[data-save-check]");
    const saveMessage = q("[data-save-message]");
    saveButton.addEventListener("click", async () => {
        const user = await currentUser;
        if (!user) {
            showMessage(saveMessage, "Please log in to save results.", "warn");
            return;
        }
        setBusy(saveButton, true, "Saving…");
        try {
            await saveSymptomCheck(user.uid, result.saveable);
            setBusy(saveButton, false);
            saveButton.disabled = true;
            saveButton.textContent = "Saved";
            showMessage(saveMessage, "Saved to your history. You can see or delete it on your dashboard.", "ok");
        } catch (error) {
            setBusy(saveButton, false);
            showMessage(saveMessage, firestoreErrorMessage(error), "warn");
        }
    });

    q("[data-start-again]").addEventListener("click", () => {
        form.reset();
        clearFieldErrors(form);
        resultArea.hidden = true;
        resultArea.replaceChildren();
        window.scrollTo({ top: 0 });
        form.querySelector("input").focus();
    });

    resultArea.replaceChildren(view);
    resultArea.hidden = false;
    resultArea.focus();
    resultArea.scrollIntoView({ block: "start" });
}

// ---------- Submit ----------

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage(formMessage, "");
    const answers = readAnswers();
    if (!validate(answers)) {
        return;
    }

    const button = form.querySelector('[type="submit"]');
    setBusy(button, true, "Checking…");
    try {
        const response = await fetch("/api/symptom-check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(answers),
        });
        const result = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(result.error || "We couldn't check your answers. Please try again.");
        }
        showResult(result);
    } catch (error) {
        const message = error instanceof TypeError
            ? "We couldn't reach HealthMate. Check your internet connection and try again."
            : error.message;
        showMessage(formMessage, `${message} If you feel very unwell, call 112.`, "warn");
        formMessage.scrollIntoView({ block: "center" });
    } finally {
        setBusy(button, false);
    }
});

form.addEventListener("reset", () => {
    clearFieldErrors(form);
    showMessage(formMessage, "");
});
