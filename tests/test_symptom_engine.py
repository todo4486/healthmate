"""Safety tests for the Symptom Guide rules (services/symptom_engine.py)."""

import pytest

from services import symptom_engine as engine


def answers(**changes):
    """Valid answers for a mild, short, everyday illness; override as needed."""
    base = {
        "warning_signs": [],
        "no_warning_signs": True,
        "symptoms": ["runny_nose"],
        "details": "",
        "duration": "1_3_days",
        "severity": "mild",
        "age_group": "18_64",
    }
    base.update(changes)
    return base


def level_for(**changes):
    return engine.assess(engine.validate(answers(**changes)))["level"]


# ---------- Normal inputs ----------

def test_mild_short_common_cold_is_self_care_with_caution():
    result = engine.assess(engine.validate(answers(symptoms=["runny_nose", "sore_throat", "cough"])))
    assert result["level"] == "self_care"
    assert "may be enough" in result["heading"]
    assert "does not mean nothing is wrong" in result["summary"]
    assert result["watch_for"], "self-care must always say when to get help"
    assert "not a diagnosis" in result["disclaimer"]


def test_results_never_claim_diagnosis_or_certainty():
    for case in [answers(), answers(symptoms=["chest_discomfort"]), answers(severity="severe")]:
        result = engine.assess(engine.validate(case))
        text = " ".join([result["heading"], result["summary"], *result["next_steps"]]).lower()
        for word in ["you have", "diagnos", "nothing to worry", "you are fine", "definitely"]:
            assert word not in text.replace("not a diagnosis", ""), word


# ---------- Potentially serious symptoms ----------

@pytest.mark.parametrize("sign", [item["id"] for item in engine.GUIDE["warning_signs"]])
def test_every_warning_sign_is_urgent(sign):
    assert level_for(warning_signs=[sign], no_warning_signs=False) == "urgent"


@pytest.mark.parametrize("symptom", ["chest_discomfort", "breathing_difficulty"])
@pytest.mark.parametrize("severity", ["mild", "moderate", "severe"])
@pytest.mark.parametrize("duration", ["under_1_day", "over_1_week"])
def test_chest_and_breathing_are_urgent_even_when_mild(symptom, severity, duration):
    assert level_for(symptoms=[symptom], severity=severity, duration=duration) == "urgent"


def test_warning_sign_wins_even_if_none_of_these_also_sent():
    # If a buggy or tampered form sends both, the safe answer wins.
    assert level_for(warning_signs=["chest_pain"], no_warning_signs=True) == "urgent"


def test_urgent_result_tells_user_to_call_112():
    result = engine.assess(engine.validate(answers(symptoms=["chest_discomfort"])))
    assert "112" in result["next_steps"][0]
    assert result["heading"] == "Get medical help now"


def test_self_harm_warning_sign_shows_crisis_support():
    result = engine.assess(engine.validate(answers(warning_signs=["self_harm"], no_warning_signs=False)))
    assert result["level"] == "urgent"
    assert result["crisis_support"] is True
    assert "14416" in result["next_steps"][0]


# ---------- Free text: can only add caution, never remove it ----------

def test_severity_is_not_read_from_the_word_severe():
    # Typing "severe" does not make it urgent, and typing "mild" does not lower it.
    assert level_for(details="severe sniffles") == "self_care"
    assert level_for(symptoms=["chest_discomfort"], details="very mild, nothing serious") == "urgent"


@pytest.mark.parametrize("text", [
    "I have chest pain when I walk",
    "I can't breathe properly",
    "I fainted this morning",
    "coughing up blood",
])
def test_emergency_words_in_description_block_a_self_care_result(text):
    result = engine.assess(engine.validate(answers(details=text)))
    assert result["level"] != "self_care"
    assert result["text_alerts"]["emergency"]


def test_negated_emergency_words_still_add_caution_not_reassurance():
    # Word matching can't understand "no". It must err on the safe side.
    result = engine.assess(engine.validate(answers(details="no chest pain at all")))
    assert result["level"] == "doctor"
    assert result["text_alerts"]["emergency"] == ["chest pain"]


def test_crisis_words_in_description_show_support():
    result = engine.assess(engine.validate(answers(details="I want to hurt myself")))
    assert result["crisis_support"] is True
    assert result["level"] != "self_care"


def test_words_inside_other_words_do_not_match():
    # "benefit" contains "fit" and "unstroked" contains "stroke": whole words only.
    assert level_for(details="I noticed a benefit from resting, the cat was unstroked") == "self_care"


# ---------- Situations the guide can't assess ----------

def test_children_under_five_always_see_a_doctor():
    assert level_for(age_group="under_5") == "doctor"


def test_other_symptoms_are_not_given_self_care():
    assert level_for(symptoms=["other"], details="itchy ear") == "doctor"


def test_description_only_counts_as_other_symptoms():
    validated = engine.validate(answers(symptoms=[], details="itchy ear"))
    assert validated["symptoms"] == ["other"]
    assert engine.assess(validated)["level"] == "doctor"


# ---------- Doctor-level rules ----------

@pytest.mark.parametrize("changes", [
    {"severity": "severe"},
    {"duration": "over_1_week"},
    {"duration": "4_7_days"},
    {"symptoms": ["dizziness"]},
    {"symptoms": ["fever", "rash"]},
    {"symptoms": ["vomiting", "diarrhoea"], "severity": "moderate"},
    {"symptoms": ["stomach_pain"], "severity": "moderate"},
    {"symptoms": ["fever"], "age_group": "65_plus"},
])
def test_doctor_rules(changes):
    assert level_for(**changes) == "doctor"


def test_severe_symptoms_say_today():
    result = engine.assess(engine.validate(answers(severity="severe")))
    assert result["heading"] == "Speak to a doctor today"
    assert result["next_steps"][0] == "Contact a doctor today."


def test_every_rule_that_fires_gives_a_reason():
    result = engine.assess(engine.validate(answers(
        symptoms=["dizziness", "fever", "rash"], duration="over_1_week", age_group="65_plus")))
    assert len(result["reasons"]) >= 4


# ---------- Empty and malformed input ----------

@pytest.mark.parametrize("payload, message", [
    (None, "fill in the form"),
    ([], "fill in the form"),
    ("text", "fill in the form"),
    ({}, "warning signs"),
    (answers(no_warning_signs=False), "warning signs"),
    (answers(no_warning_signs="yes"), "warning signs"),       # must be true, not just "truthy"
    (answers(symptoms=[], details=""), "at least one symptom"),
    (answers(symptoms=[], details="     "), "at least one symptom"),
    (answers(symptoms=["made_up"]), "from the list"),
    (answers(symptoms="fever"), "from the list"),
    (answers(symptoms=[{"id": "fever"}]), "from the list"),
    (answers(symptoms=["fever"] * 100), "from the list"),
    (answers(warning_signs=["fake"], no_warning_signs=False), "warning signs"),
    (answers(details=123), "must be text"),
    (answers(details="x" * 501), "under 500"),
    (answers(duration="forever"), "how long"),
    (answers(duration=None), "how long"),
    (answers(severity=""), "how severe"),
    (answers(age_group="adult"), "age group"),
])
def test_invalid_answers_are_rejected(payload, message):
    with pytest.raises(engine.InvalidAnswers, match=message):
        engine.validate(payload)


def test_description_is_cleaned_and_duplicates_removed():
    validated = engine.validate(answers(symptoms=["cough", "cough"], details="  a\n\n  b  "))
    assert validated["symptoms"] == ["cough"]
    assert validated["details"] == "a b"


def test_saveable_data_contains_no_free_text_or_warning_signs():
    result = engine.assess(engine.validate(answers(details="private note", warning_signs=["stroke"],
                                                   no_warning_signs=False)))
    assert set(result["saveable"]) == {"symptoms", "duration", "severity", "ageGroup", "level"}
    assert "private note" not in str(result["saveable"])
