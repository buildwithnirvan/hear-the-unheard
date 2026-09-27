import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ml.translation.isl_to_text import translate


def test_spec_example_1_name_question():
    """Spec's own example: YOU NAME WHAT -> 'What is your name?'"""
    result = translate(["YOU", "NAME", "WHAT"])
    assert result.sentence == "What is your name?", result.sentence
    print(f"PASS: YOU NAME WHAT -> {result.sentence!r} (rule={result.rule_applied})")


def test_spec_example_2_going_to_hospital():
    """Spec's own example: ME HOSPITAL GO -> 'I am going to the hospital.'"""
    result = translate(["ME", "HOSPITAL", "GO"])
    assert result.sentence == "I am going to the hospital.", result.sentence
    print(f"PASS: ME HOSPITAL GO -> {result.sentence!r} (rule={result.rule_applied})")


def test_where_question():
    result = translate(["YOU", "GO", "WHERE"])
    assert result.sentence == "Where are you going?", result.sentence
    print(f"PASS: YOU GO WHERE -> {result.sentence!r}")


def test_negation():
    result = translate(["I", "NO"])
    assert result.sentence == "I not.", result.sentence
    print(f"PASS: I NO -> {result.sentence!r}")


def test_time_marker():
    result = translate(["TOMORROW", "I", "SCHOOL", "GO"])
    assert result.sentence.startswith("Tomorrow,"), result.sentence
    print(f"PASS: TOMORROW I SCHOOL GO -> {result.sentence!r}")


def test_fallback_never_drops_tokens():
    """An unrecognized pattern must still surface every token, not vanish."""
    result = translate(["BUTTERFLY", "PURPLE", "DANCE"])
    assert result.rule_applied == "fallback_literal_join"
    for t in ["butterfly", "purple", "dance"]:
        assert t in result.sentence.lower(), f"{t} missing from fallback output {result.sentence!r}"
    print(f"PASS: unrecognized pattern falls back safely -> {result.sentence!r}")


def test_empty_input_does_not_crash():
    result = translate([])
    assert result.sentence == ""
    print("PASS: empty input handled without crashing")


def test_single_question_word():
    result = translate(["WHY"])
    assert result.sentence == "Why?", result.sentence
    print(f"PASS: WHY alone -> {result.sentence!r}")


if __name__ == "__main__":
    test_spec_example_1_name_question()
    test_spec_example_2_going_to_hospital()
    test_where_question()
    test_negation()
    test_time_marker()
    test_fallback_never_drops_tokens()
    test_empty_input_does_not_crash()
    test_single_question_word()
    print("\nAll translation tests passed.")
