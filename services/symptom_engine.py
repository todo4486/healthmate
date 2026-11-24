"""Symptom Guide: safety-first, rule-based guidance. NOT a diagnosis.

How it works
------------
1. validate()  checks the answers and turns them into a clean dictionary.
2. assess()    runs every rule in RULES. Each rule can raise the result to
               "doctor" or "urgent" and gives a plain-English reason.
               The highest level wins. If no rule fires, the result is
               "self_care", worded carefully so it never sounds like an all-clear.

Safety principles
-----------------
* An explicit warning-sign question is asked first. Any "yes" means urgent.
* Chest discomfort and breathing difficulties are always urgent.
* The free-text description can only ADD caution (see text_safety.py).
  It is never used to lower a result, because simple word matching cannot
  understand meaning (for example "no chest pain").
* When the guide cannot assess something (children under 5, "Other
  symptoms"), it says so and recommends a doctor instead of guessing.
"""

from content import load_data
from services.text_safety import find_urgent_phrases

GUIDE = load_data("symptom_guide.json")

LEVELS = ["self_care", "doctor", "urgent"]  # lowest to highest
MAX_DETAILS_LENGTH = 500

_LABELS = {
    group: {item["id"]: item["label"] for item in GUIDE[group]}
    for group in ["warning_signs", "symptoms", "durations", "severities", "age_groups"]
}


class InvalidAnswers(ValueError):
    """The submitted answers are missing or not in the expected format."""


# ---------------------------------------------------------------------------
# 1. Validation
# ---------------------------------------------------------------------------

def _choice(payload, field, group, message):
    value = payload.get(field)
    if not isinstance(value, str) or value not in _LABELS[group]:
        raise InvalidAnswers(message)
    return value


def _id_list(payload, field, group, message):
    value = payload.get(field, [])
    if not isinstance(value, list) or len(value) > len(_LABELS[group]):
        raise InvalidAnswers(message)
    if any(not isinstance(item, str) or item not in _LABELS[group] for item in value):
        raise InvalidAnswers(message)
    return list(dict.fromkeys(value))  # remove duplicates, keep order


def validate(payload):
    """Check the submitted answers. Raises InvalidAnswers with a friendly message."""
    if not isinstance(payload, dict):
        raise InvalidAnswers("Please fill in the form and try again.")

    warning_signs = _id_list(payload, "warning_signs", "warning_signs",
                             "Please answer the warning signs question.")
    no_warning_signs = payload.get("no_warning_signs") is True
    if not warning_signs and not no_warning_signs:
        raise InvalidAnswers("Please tell us whether you have any of the warning signs.")

    symptoms = _id_list(payload, "symptoms", "symptoms", "Please choose symptoms from the list.")

    details = payload.get("details", "")
    if details is None:
        details = ""
    if not isinstance(details, str):
        raise InvalidAnswers("The description must be text.")
    details = " ".join(details.split())
    if len(details) > MAX_DETAILS_LENGTH:
        raise InvalidAnswers(f"Please keep the description under {MAX_DETAILS_LENGTH} characters.")

    if not symptoms and not details:
        raise InvalidAnswers("Please choose at least one symptom or describe how you feel.")
    if not symptoms:
        symptoms = ["other"]  # described in words only

    return {
        "warning_signs": warning_signs,
        "symptoms": symptoms,
        "details": details,
        "duration": _choice(payload, "duration", "durations", "Please choose how long you've had symptoms."),
        "severity": _choice(payload, "severity", "severities", "Please choose how severe your symptoms are."),
        "age_group": _choice(payload, "age_group", "age_groups", "Please choose an age group."),
    }


# ---------------------------------------------------------------------------
# 2. Rules
# ---------------------------------------------------------------------------
# Each rule receives the validated answers (plus "text_alerts") and returns
# None, or (level, reason, today) where today=True means "see a doctor today".

def _has(answers, *symptom_ids):
    return any(item in answers["symptoms"] for item in symptom_ids)


def rule_warning_signs(answers):
    if answers["warning_signs"]:
        names = "; ".join(_LABELS["warning_signs"][item].lower() for item in answers["warning_signs"])
        return "urgent", f"You told us you have a warning sign: {names}. This needs checking in person straight away.", True
    return None


def rule_chest_or_breathing(answers):
    if _has(answers, "chest_discomfort"):
        return "urgent", "Chest discomfort can have serious causes that must be checked in person straight away, even if it feels mild.", True
    if _has(answers, "breathing_difficulty"):
        return "urgent", "Breathing difficulties need to be checked in person straight away.", True
    return None


def rule_words_in_description(answers):
    found = answers["text_alerts"]["emergency"] + answers["text_alerts"]["crisis"]
    if found:
        return "doctor", f"Your description mentions “{found[0]}”. We can't judge from words how serious that is, so we won't suggest self-care alone.", True
    return None


def rule_young_child(answers):
    if answers["age_group"] == "under_5":
        return "doctor", "This guide is not designed for children under 5. Young children can become unwell quickly, so please speak to a doctor.", True
    return None


def rule_severe(answers):
    if answers["severity"] == "severe":
        return "doctor", "You said your symptoms are severe enough to stop your usual activities.", True
    return None


def rule_older_adult(answers):
    if answers["age_group"] == "65_plus" and (
        _has(answers, "fever", "vomiting", "diarrhoea", "dizziness") or answers["severity"] == "moderate"
    ):
        return "doctor", "People aged 65 or over can be more affected by these symptoms, so it is best to get them checked.", True
    return None


def rule_fever_with_rash(answers):
    if _has(answers, "fever") and _has(answers, "rash"):
        return "doctor", "A fever together with a rash should be checked by a doctor the same day.", True
    return None


def rule_vomiting_and_diarrhoea(answers):
    if _has(answers, "vomiting") and _has(answers, "diarrhoea") and (
        answers["severity"] != "mild" or answers["duration"] != "under_1_day"
    ):
        return "doctor", "Vomiting and diarrhoea together can quickly lead to dehydration.", False
    return None


def rule_dizziness(answers):
    if _has(answers, "dizziness"):
        return "doctor", "Dizziness can have many causes and is best checked by a doctor.", False
    return None


def rule_stomach_pain(answers):
    if _has(answers, "stomach_pain") and answers["severity"] != "mild":
        return "doctor", "Stomach pain that is affecting your day should be checked by a doctor.", False
    return None


def rule_long_duration(answers):
    if answers["duration"] == "over_1_week":
        return "doctor", "Symptoms that last more than a week should be checked by a doctor.", False
    if answers["duration"] == "4_7_days":
        return "doctor", "Your symptoms have lasted several days without settling.", False
    return None


def rule_other_symptoms(answers):
    if _has(answers, "other"):
        return "doctor", "You mentioned symptoms that aren't on our list. This guide only covers a few common symptoms, so it can't assess them.", False
    return None


RULES = [
    rule_warning_signs,
    rule_chest_or_breathing,
    rule_words_in_description,
    rule_young_child,
    rule_severe,
    rule_older_adult,
    rule_fever_with_rash,
    rule_vomiting_and_diarrhoea,
    rule_dizziness,
    rule_stomach_pain,
    rule_long_duration,
    rule_other_symptoms,
]


# ---------------------------------------------------------------------------
# 3. Result
# ---------------------------------------------------------------------------

URGENT_STEPS = [
    "Call 112 now, or 108 for an ambulance, or go to the nearest emergency department.",
    "Don't drive yourself if you feel very unwell. Ask someone to take you or call an ambulance.",
    "If someone is with you, tell them how you are feeling.",
]
CRISIS_STEP = (
    "If you are having thoughts of harming yourself, you are not alone. Call Tele-MANAS on "
    "14416 (free, 24/7) to talk to someone, or 112 if you are in immediate danger."
)
SELF_CARE_STEPS = [
    "Rest, and drink enough fluids.",
    "Keep an eye on how you feel over the next day or two.",
    "Speak to a doctor if things don't improve within 3 days, get worse, or worry you.",
]
ALWAYS_WATCH_FOR = [
    "Any warning sign, such as chest pain, trouble breathing, fainting, confusion or a seizure: call 112.",
    "Symptoms that get worse, or new symptoms.",
    "If you are pregnant, have a long-term health condition or a weakened immune system, "
    "get medical advice sooner than this guide suggests.",
]


def _watch_for(answers):
    items = list(ALWAYS_WATCH_FOR)
    if _has(answers, "fever"):
        items.insert(1, "A fever that lasts more than 3 days, or keeps coming back.")
    if _has(answers, "vomiting", "diarrhoea"):
        items.insert(1, "Not being able to keep fluids down, or passing very little urine.")
    return items


def assess(answers):
    """Return the guidance for validated answers (see validate())."""
    answers = dict(answers, text_alerts=find_urgent_phrases(answers["details"]))

    level, reasons, today = "self_care", [], False
    for rule in RULES:
        outcome = rule(answers)
        if outcome:
            rule_level, reason, rule_today = outcome
            reasons.append(reason)
            today = today or rule_today
            if LEVELS.index(rule_level) > LEVELS.index(level):
                level = rule_level

    crisis = "self_harm" in answers["warning_signs"] or bool(answers["text_alerts"]["crisis"])

    if level == "urgent":
        heading = "Get medical help now"
        summary = ("Based on your answers, you should be seen by a medical professional urgently. "
                   "This tool cannot judge how serious this is.")
        steps = list(URGENT_STEPS)
    elif level == "doctor":
        heading = "Speak to a doctor today" if today else "Speak to a doctor soon"
        summary = ("Your answers suggest getting advice from a doctor. This doesn't mean something is "
                   "seriously wrong, but these symptoms should be checked by a professional.")
        steps = [
            "Contact a doctor today." if today else "Book an appointment with a doctor in the next day or two.",
            "Note down your symptoms and when they started, to share with the doctor.",
            "If you get worse or notice any warning sign, call 112.",
        ]
    else:
        heading = "Self-care may be enough for now"
        summary = ("None of your answers matched our rules for seeing a doctor. That does not mean nothing "
                   "is wrong: this guide can't examine you and only covers common, short-term symptoms.")
        reasons = ["You reported no warning signs, and none of the rules for seeing a doctor matched your answers."]
        steps = list(SELF_CARE_STEPS)

    if crisis:
        steps.insert(0, CRISIS_STEP)

    return {
        "level": level,
        "heading": heading,
        "summary": summary,
        "reasons": reasons,
        "next_steps": steps,
        "watch_for": _watch_for(answers),
        "text_alerts": answers["text_alerts"],
        "crisis_support": crisis,
        "submitted": {
            "warning_signs": [_LABELS["warning_signs"][item] for item in answers["warning_signs"]],
            "symptoms": [_LABELS["symptoms"][item] for item in answers["symptoms"]],
            "details": answers["details"],
            "duration": _LABELS["durations"][answers["duration"]],
            "severity": _LABELS["severities"][answers["severity"]],
            "age_group": _LABELS["age_groups"][answers["age_group"]],
        },
        # Ids for the optional "Save to my history" (only these are ever saved).
        "saveable": {
            "symptoms": answers["symptoms"],
            "duration": answers["duration"],
            "severity": answers["severity"],
            "ageGroup": answers["age_group"],
            "level": level,
        },
        "disclaimer": ("This is general information from a short list of written rules, not a diagnosis. "
                       "It cannot examine you or replace a healthcare professional. If you are worried, "
                       "contact a doctor."),
    }


def labels():
    """Id-to-label maps, used by the dashboard to show saved checks."""
    return {
        "symptoms": _LABELS["symptoms"],
        "durations": _LABELS["durations"],
        "severities": _LABELS["severities"],
    }
