"""
Seeds the vocabulary database with an initial set of ISL sign entries.

IMPORTANT: this is vocabulary METADATA (gloss, category, English/Hindi/
Kannada meaning) — it is NOT training data. No video/landmark samples are
attached, and model_label is left None for every entry here, so these
signs show up as "documented but not yet recognizable" (see
/api/v1/model/status and /api/v1/vocabulary/stats/summary) until real
labeled training clips are collected and a model is trained on them
(ml/training/, Phase 3).

The gloss/meaning list below reflects common, widely-documented ISL
vocabulary. It has NOT been reviewed by a certified ISL
interpreter/native signer — treat it as a reasonable starting seed, and
have a qualified reviewer validate gloss accuracy, regional variation,
and hand/movement description before this is used for anything
production-facing (§21 admin review workflow exists precisely for this).

Idempotent — safe to re-run; uses sign_id as the natural key.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database.mongo import get_database, ensure_indexes
from app.models.vocabulary import SignType, SignCategory, new_sign_document

SEED = [
    # sign_id, gloss, category, type, english, required_hands
    ("ISL_00001", "HELLO", SignCategory.GREETING, SignType.DYNAMIC, "hello", "single"),
    ("ISL_00002", "THANK_YOU", SignCategory.GREETING, SignType.DYNAMIC, "thank you", "single"),
    ("ISL_00003", "PLEASE", SignCategory.GREETING, SignType.DYNAMIC, "please", "single"),
    ("ISL_00004", "SORRY", SignCategory.GREETING, SignType.DYNAMIC, "sorry", "single"),
    ("ISL_00005", "YES", SignCategory.CONVERSATIONAL_PHRASE, SignType.DYNAMIC, "yes", "single"),
    ("ISL_00006", "NO", SignCategory.CONVERSATIONAL_PHRASE, SignType.DYNAMIC, "no", "single"),
    ("ISL_00007", "GOOD_MORNING", SignCategory.GREETING, SignType.DYNAMIC, "good morning", "both"),
    ("ISL_00008", "GOODBYE", SignCategory.GREETING, SignType.DYNAMIC, "goodbye", "single"),

    ("ISL_00010", "I_ME", SignCategory.PRONOUN, SignType.STATIC, "I / me", "single"),
    ("ISL_00011", "YOU", SignCategory.PRONOUN, SignType.STATIC, "you", "single"),
    ("ISL_00012", "WE", SignCategory.PRONOUN, SignType.DYNAMIC, "we", "single"),
    ("ISL_00013", "THEY", SignCategory.PRONOUN, SignType.DYNAMIC, "they", "single"),

    ("ISL_00020", "WHAT", SignCategory.QUESTION, SignType.DYNAMIC, "what", "single"),
    ("ISL_00021", "WHERE", SignCategory.QUESTION, SignType.DYNAMIC, "where", "single"),
    ("ISL_00022", "WHO", SignCategory.QUESTION, SignType.DYNAMIC, "who", "single"),
    ("ISL_00023", "WHY", SignCategory.QUESTION, SignType.DYNAMIC, "why", "single"),
    ("ISL_00024", "HOW", SignCategory.QUESTION, SignType.DYNAMIC, "how", "single"),
    ("ISL_00025", "NAME", SignCategory.QUESTION, SignType.STATIC, "name", "both"),

    ("ISL_00030", "HELP", SignCategory.EMERGENCY, SignType.DYNAMIC, "help", "both"),
    ("ISL_00031", "EMERGENCY", SignCategory.EMERGENCY, SignType.DYNAMIC, "emergency", "both"),
    ("ISL_00032", "DANGER", SignCategory.EMERGENCY, SignType.DYNAMIC, "danger", "single"),
    ("ISL_00033", "POLICE", SignCategory.EMERGENCY, SignType.STATIC, "police", "single"),
    ("ISL_00034", "FIRE", SignCategory.EMERGENCY, SignType.DYNAMIC, "fire", "both"),

    ("ISL_00040", "HOSPITAL", SignCategory.MEDICAL, SignType.STATIC, "hospital", "single"),
    ("ISL_00041", "DOCTOR", SignCategory.MEDICAL, SignType.DYNAMIC, "doctor", "single"),
    ("ISL_00042", "MEDICINE", SignCategory.MEDICAL, SignType.DYNAMIC, "medicine", "single"),
    ("ISL_00043", "PAIN", SignCategory.MEDICAL, SignType.DYNAMIC, "pain", "both"),
    ("ISL_00044", "SICK", SignCategory.MEDICAL, SignType.STATIC, "sick / unwell", "single"),

    ("ISL_00050", "SCHOOL", SignCategory.EDUCATION, SignType.DYNAMIC, "school", "both"),
    ("ISL_00051", "TEACHER", SignCategory.EDUCATION, SignType.DYNAMIC, "teacher", "both"),
    ("ISL_00052", "STUDENT", SignCategory.EDUCATION, SignType.DYNAMIC, "student", "both"),
    ("ISL_00053", "BOOK", SignCategory.EDUCATION, SignType.STATIC, "book", "both"),
    ("ISL_00054", "STUDY", SignCategory.EDUCATION, SignType.DYNAMIC, "study", "both"),

    ("ISL_00060", "MOTHER", SignCategory.FAMILY, SignType.STATIC, "mother", "single"),
    ("ISL_00061", "FATHER", SignCategory.FAMILY, SignType.STATIC, "father", "single"),
    ("ISL_00062", "SISTER", SignCategory.FAMILY, SignType.DYNAMIC, "sister", "single"),
    ("ISL_00063", "BROTHER", SignCategory.FAMILY, SignType.DYNAMIC, "brother", "single"),
    ("ISL_00064", "FAMILY", SignCategory.FAMILY, SignType.DYNAMIC, "family", "both"),
    ("ISL_00065", "FRIEND", SignCategory.FAMILY, SignType.DYNAMIC, "friend", "both"),

    ("ISL_00070", "HOME", SignCategory.TRAVEL, SignType.STATIC, "home", "single"),
    ("ISL_00071", "GO", SignCategory.VERB, SignType.DYNAMIC, "go", "single"),
    ("ISL_00072", "COME", SignCategory.VERB, SignType.DYNAMIC, "come", "single"),
    ("ISL_00073", "BUS", SignCategory.TRAVEL, SignType.DYNAMIC, "bus", "single"),
    ("ISL_00074", "TRAIN", SignCategory.TRAVEL, SignType.DYNAMIC, "train", "both"),

    ("ISL_00080", "EAT", SignCategory.VERB, SignType.DYNAMIC, "eat", "single"),
    ("ISL_00081", "DRINK", SignCategory.VERB, SignType.DYNAMIC, "drink", "single"),
    ("ISL_00082", "WATER", SignCategory.NOUN, SignType.DYNAMIC, "water", "single"),
    ("ISL_00083", "FOOD", SignCategory.NOUN, SignType.DYNAMIC, "food", "both"),

    ("ISL_00090", "GOOD", SignCategory.ADJECTIVE, SignType.STATIC, "good", "single"),
    ("ISL_00091", "BAD", SignCategory.ADJECTIVE, SignType.STATIC, "bad", "single"),
    ("ISL_00092", "HAPPY", SignCategory.ADJECTIVE, SignType.DYNAMIC, "happy", "both"),
    ("ISL_00093", "SAD", SignCategory.ADJECTIVE, SignType.DYNAMIC, "sad", "single"),

    ("ISL_00100", "TODAY", SignCategory.TIME_DATE, SignType.DYNAMIC, "today", "single"),
    ("ISL_00101", "TOMORROW", SignCategory.TIME_DATE, SignType.DYNAMIC, "tomorrow", "single"),
    ("ISL_00102", "YESTERDAY", SignCategory.TIME_DATE, SignType.DYNAMIC, "yesterday", "single"),
    ("ISL_00103", "TIME", SignCategory.TIME_DATE, SignType.STATIC, "time", "single"),

    ("ISL_00110", "OFFICE", SignCategory.WORKPLACE, SignType.STATIC, "office", "both"),
    ("ISL_00111", "WORK", SignCategory.WORKPLACE, SignType.DYNAMIC, "work", "both"),
    ("ISL_00112", "MEETING", SignCategory.WORKPLACE, SignType.DYNAMIC, "meeting", "both"),

    ("ISL_00120", "GOVERNMENT", SignCategory.GOVERNMENT, SignType.STATIC, "government", "single"),
    ("ISL_00121", "ID_CARD", SignCategory.GOVERNMENT, SignType.STATIC, "ID card", "both"),
]

ALPHABET = [
    (f"ISL_ALPHA_{chr(65+i)}", chr(65 + i), SignCategory.ALPHABET, SignType.STATIC, chr(65 + i), "single")
    for i in range(26)
]

NUMBERS = [
    (f"ISL_NUM_{i:02d}", str(i), SignCategory.NUMBER, SignType.STATIC, str(i), "single")
    for i in range(11)
]


def run():
    db = get_database()
    ensure_indexes()

    added = 0
    for sign_id, gloss, category, sign_type, english, hands in SEED + ALPHABET + NUMBERS:
        if db.signs.find_one({"sign_id": sign_id}):
            continue
        doc = new_sign_document(
            sign_id=sign_id,
            gloss=gloss,
            category=category,
            sign_type=sign_type,
            english_meaning=english,
            required_hands=hands,
        )
        db.signs.insert_one(doc)
        added += 1

    print(f"Seeded {added} new vocabulary entries "
          f"({len(SEED)} general + {len(ALPHABET)} alphabet + {len(NUMBERS)} numbers defined).")


if __name__ == "__main__":
    run()
