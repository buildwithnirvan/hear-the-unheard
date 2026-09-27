import sys
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

BACKEND_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
from app.ml.translation.isl_to_text import translate  # noqa: E402

router = APIRouter(prefix="/translate", tags=["translate"])


class TranslateRequest(BaseModel):
    tokens: list[str]


@router.post("")
def translate_tokens(body: TranslateRequest):
    """
    Phase 5: turns a recognized ISL gloss sequence into a natural English
    sentence via rule-based grammar normalization (not an LLM — see
    app/ml/translation/isl_to_text.py docstring for why). Returns which
    rule fired so callers/debugging can see exactly why a given sentence
    came out the way it did, rather than a black box.
    """
    result = translate(body.tokens)
    return {
        "input_tokens": result.tokens,
        "sentence": result.sentence,
        "rule_applied": result.rule_applied,
    }
