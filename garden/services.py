import json
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from .models import ErrorCode, FAQ

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "an", "and", "are", "can", "do", "does", "for", "how", "i", "in",
    "is", "it", "me", "my", "of", "on", "or", "the", "to", "what", "when",
    "where", "which", "who", "why", "with", "you", "plotpal", "assistant",
    "add", "create", "edit", "remove", "update", "garden", "entry", "site",
    "website", "please", "help", "know", "tell",
}


def _words(text):
    return {
        word for word in re.findall(r"[a-z0-9]+", text.lower())
        if len(word) > 1 and word not in STOP_WORDS
    }


def find_error_code(message):
    match = re.search(r"\b(?:400|401|403|404|429|500|503|PP-?001)\b", message, re.I)
    if not match:
        return None
    code = match.group(0).upper().replace("PP001", "PP-001")
    return ErrorCode.objects.filter(code=code).first()


def find_faq(message):
    query_words = _words(message)
    if not query_words:
        return None

    best_faq = None
    best_score = 0
    for faq in FAQ.objects.all():
        question_words = _words(f"{faq.question} {faq.keywords}")
        overlap = query_words & question_words
        score = len(overlap) / max(len(query_words), 1)
        if score > best_score:
            best_faq, best_score = faq, score

    return best_faq if best_score >= 0.25 else None


def _generate_grounded_answer(message, faq, error_code):
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        return None

    if error_code:
        source = f"{error_code.code} — {error_code.title}\n{error_code.explanation}\n{error_code.suggestion}"
    else:
        source = f"FAQ: {faq.question}\nAnswer: {faq.answer}"

    payload = json.dumps({
        "model": settings.AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are PlotPal's garden support assistant. Answer using only the "
                    "provided PlotPal FAQ or error-code information. If it does not "
                    "contain the answer, say you cannot answer and do not guess. Keep "
                    "the response concise and friendly."
                ),
            },
            {"role": "user", "content": f"Reference information:\n{source}\n\nQuestion: {message}"},
        ],
        "temperature": 0.2,
        "max_tokens": 180,
    }).encode("utf-8")
    request = Request(
        settings.AI_API_URL,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        answer = data["choices"][0]["message"]["content"].strip()
        return answer or None
    except (
        HTTPError,
        URLError,
        TimeoutError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError,
        AttributeError,
        ValueError,
    ):
        logger.exception("AI answer generation failed; using the matched database answer.")
        return None


def answer_question(message):
    error_code = find_error_code(message)
    faq = None if error_code else find_faq(message)
    if not error_code and not faq:
        return None

    generated = _generate_grounded_answer(message, faq, error_code)
    if generated:
        return generated
    if error_code:
        return f"{error_code.title}: {error_code.explanation}\n\nWhat to try: {error_code.suggestion}"
    return faq.answer


def get_weather():
    fallback = {
        "available": False,
        "temperature": None,
        "description": "Live weather is temporarily unavailable.",
        "advice": "Check the soil before watering; if the top layer feels dry, water gently.",
    }
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={settings.WEATHER_LATITUDE}&longitude={settings.WEATHER_LONGITUDE}"
        "&current=temperature_2m,weather_code"
    )
    try:
        with urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        current = data["current"]
        temperature = float(current["temperature_2m"])
        return {
            "available": True,
            "temperature": temperature,
            "description": f"Current temperature: {temperature:g}°C",
            "advice": "Use the forecast as a guide and check soil moisture before watering.",
        }
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        logger.exception("Weather provider unavailable; showing the safe garden-care fallback.")
        return fallback
