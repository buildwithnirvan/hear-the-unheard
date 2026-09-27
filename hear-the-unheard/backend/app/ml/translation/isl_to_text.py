"""
isl_to_text.py

Phase 5: ISL recognized-token sequence -> natural language sentence.

ISL (like ASL and many sign languages) commonly uses topic-comment and
OSV/SOV-leaning word order and drops copulas ("to be") and articles that
English requires. A sequence of recognized glosses like
["YOU", "NAME", "WHAT"] needs real grammar normalization, not just
joining words with spaces, to become "What is your name?"

APPROACH: rule-based pattern matching, not an LLM. Per the spec (§10):
an LLM may be used later purely as a language-normalization *layer* on
top of recognized tokens, but it must never be allowed to invent tokens
that weren't actually recognized. Starting with explicit rules means
every output is traceable to the input tokens — nothing hallucinated —
and rules can be added incrementally as real recognized-sequence
patterns are observed in use, rather than trusting an LLM's guess about
ISL grammar it likely has little real training data on.

This module is intentionally modest: it implements question-fronting,
basic pronoun+object+verb -> pronoun+verb+object reordering, negation
placement, and tense/time-marker handling, covering the two worked
examples in the spec plus their variations. It falls back to a plain
space-joined, capitalized sentence for anything it doesn't have a rule
for — never silently drops tokens, never invents ones that weren't
there.
"""
from __future__ import annotations

import dataclasses
from typing import Optional

QUESTION_WORDS = {"WHAT", "WHERE", "WHO", "WHY", "HOW", "WHEN"}
PRONOUNS = {"I": "I", "ME": "I", "YOU": "you", "WE": "we", "THEY": "they", "HE": "he", "SHE": "she"}
NEGATION_WORDS = {"NO", "NOT"}
PAST_MARKERS = {"YESTERDAY", "BEFORE", "ALREADY"}
FUTURE_MARKERS = {"TOMORROW", "WILL", "LATER"}

# Minimal lemma/gloss -> natural-English-word map for tokens that need a
# different surface form (verbs needing "-ing", nouns needing an article,
# etc.). Anything not listed here is lowercased as-is. This is meant to
# grow from real vocabulary, not be exhaustive on day one.
GLOSS_TO_SURFACE = {
    "GO": "going",
    "COME": "coming",
    "EAT": "eating",
    "DRINK": "drinking",
    "HOSPITAL": "the hospital",
    "SCHOOL": "school",
    "HOME": "home",
    "DOCTOR": "the doctor",
    "NAME": "name",
    "HELP": "help",
}


@dataclasses.dataclass
class TranslationResult:
    sentence: str
    rule_applied: str  # which rule fired, for debugging/tracing — never hidden from the caller
    tokens: list[str]  # the original input, unmodified, so nothing is ever silently lost


def _surface(token: str) -> str:
    surface = GLOSS_TO_SURFACE.get(token.upper(), token.lower())
    if surface == "i":  # "I" is always capitalized in English, not just sentence-initially
        return "I"
    return surface


def _is_pronoun(token: str) -> bool:
    return token.upper() in PRONOUNS


def translate(tokens: list[str]) -> TranslationResult:
    """
    tokens: recognized ISL gloss sequence, e.g. ["YOU", "NAME", "WHAT"].
    Returns a TranslationResult — never raises on an unrecognized pattern,
    falls back to a safe default instead.
    """
    if not tokens:
        return TranslationResult(sentence="", rule_applied="empty_input", tokens=tokens)

    upper = [t.upper() for t in tokens]

    # Rule 1: question word anywhere in the sequence -> front it, insert
    # a copula if a pronoun is present. Covers "YOU NAME WHAT" -> "What
    # is your name?" and "YOU GO WHERE" -> "Where are you going?"
    question_words_present = [t for t in upper if t in QUESTION_WORDS]
    if question_words_present:
        qword = question_words_present[0]
        rest = [t for t in tokens if t.upper() != qword]
        result = _build_question(qword, rest)
        if result:
            return TranslationResult(sentence=result, rule_applied="question_fronting", tokens=tokens)

    # Rule 2: PRONOUN + LOCATION/OBJECT + VERB -> PRONOUN + be-verb(VERB)
    # + OBJECT. Covers "ME HOSPITAL GO" -> "I am going to the hospital."
    if len(upper) == 3 and _is_pronoun(upper[0]):
        pronoun, obj, verb = tokens[0], tokens[1], tokens[2]
        if verb.upper() in ("GO", "COME") and obj.upper() not in QUESTION_WORDS:
            be_verb = "am" if PRONOUNS[upper[0]] == "I" else ("are" if PRONOUNS[upper[0]] in ("you", "we", "they") else "is")
            prep = "to " if verb.upper() == "GO" else "from "
            sentence = f"{PRONOUNS[upper[0]].capitalize()} {be_verb} {_surface(verb)} {prep}{_surface(obj)}."
            return TranslationResult(sentence=sentence, rule_applied="pronoun_object_verb", tokens=tokens)

    # Rule 3: negation — NO/NOT immediately before or after a
    # pronoun+verb pair gets folded into "don't/doesn't/isn't" rather
    # than left as a bare extra word.
    if any(t in NEGATION_WORDS for t in upper):
        sentence = _apply_negation(tokens, upper)
        if sentence:
            return TranslationResult(sentence=sentence, rule_applied="negation", tokens=tokens)

    # Rule 4: time marker prefix — YESTERDAY/TOMORROW etc. at the start
    # just prepends naturally rather than needing full reordering.
    if upper[0] in PAST_MARKERS or upper[0] in FUTURE_MARKERS:
        rest_sentence = " ".join(_surface(t) for t in tokens[1:])
        sentence = f"{tokens[0].capitalize()}, {rest_sentence}." if rest_sentence else f"{tokens[0].capitalize()}."
        return TranslationResult(sentence=sentence, rule_applied="time_marker_prefix", tokens=tokens)

    # Fallback: no specific rule matched. Join tokens as-written, in
    # order, capitalized — never drop or invent tokens.
    sentence = " ".join(_surface(t) for t in tokens)
    sentence = sentence[0].upper() + sentence[1:] + "." if sentence else ""
    return TranslationResult(sentence=sentence, rule_applied="fallback_literal_join", tokens=tokens)


def _build_question(qword: str, rest: list[str]) -> Optional[str]:
    rest_upper = [t.upper() for t in rest]
    pronoun_idx = next((i for i, t in enumerate(rest_upper) if _is_pronoun(t)), None)

    if qword == "WHAT" and pronoun_idx is not None and len(rest) == 2:
        # "YOU NAME WHAT" -> pronoun=YOU(idx0), other=NAME(idx1)
        pronoun = rest[pronoun_idx]
        other = rest[1 - pronoun_idx]
        possessive = "your" if PRONOUNS[pronoun.upper()] == "you" else f"{PRONOUNS[pronoun.upper()]}'s"
        return f"What is {possessive} {_surface(other)}?"

    if qword == "WHERE" and pronoun_idx is not None:
        pronoun = rest[pronoun_idx]
        verbs = [t for i, t in enumerate(rest) if i != pronoun_idx]
        if verbs:
            be_verb = "are" if PRONOUNS[pronoun.upper()] in ("you", "we", "they") else "is"
            verb_phrase = " ".join(_surface(v) for v in verbs)
            return f"Where {be_verb} {PRONOUNS[pronoun.upper()]} {verb_phrase}?"

    if qword in ("WHO", "WHY", "HOW") and rest:
        rest_phrase = " ".join(_surface(t) for t in rest)
        return f"{qword.capitalize()} {rest_phrase}?"

    if not rest:
        return f"{qword.capitalize()}?"

    return None


def _apply_negation(tokens: list[str], upper: list[str]) -> Optional[str]:
    neg_idx = next(i for i, t in enumerate(upper) if t in NEGATION_WORDS)
    others = [t for i, t in enumerate(tokens) if i != neg_idx]
    if not others:
        return "No."
    if len(others) == 1 and _is_pronoun(others[0]):
        return f"{PRONOUNS[others[0].upper()].capitalize()} not."
    phrase = " ".join(_surface(t) for t in others)
    return f"Not {phrase}."
