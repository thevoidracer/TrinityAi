from app.backends import call_local

_EXTRACT_SYSTEM = (
    "Read the exchange below. If it contains one concrete, memorable fact worth "
    "permanently remembering about the user, their project, or their preferences "
    "(not small talk, not something already obvious, not an opinion/instruction), "
    "reply with exactly that fact as one plain sentence. "
    "Otherwise reply with exactly: NONE"
)


def extract_fact(user_message: str, assistant_message: str) -> str | None:
    messages = [
        {"role": "system", "content": _EXTRACT_SYSTEM},
        {
            "role": "user",
            "content": f"User said: {user_message}\n\nAssistant replied: {assistant_message}",
        },
    ]
    try:
        reply = call_local(messages, max_tokens=120).strip()
    except Exception:
        return None
    if not reply or reply.upper().startswith("NONE"):
        return None
    return reply
