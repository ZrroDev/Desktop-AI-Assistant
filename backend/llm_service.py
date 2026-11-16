"""LLM calls made by the backend. The only module that knows which AI provider is used."""

import anthropic
from dotenv import load_dotenv


class LLMError(Exception):
    """Raised when the AI provider fails, whatever provider it is."""


# Model settings
MODEL = "claude-opus-5-5"
LANGUAGE_PROMPT = "Always answer in Spanish."  # PROVISIONAL
# Added to the system prompt when the reply will be spoken
VOICE_PROMPT = (
    "Your reply will be read aloud by a text-to-speech engine, so write it to be heard, not read. "
    "Answer in 1 to 3 short sentences of plain conversational text: no markdown, lists, tables, "
    "code, URLs or emojis. If the question needs a longer answer, give the key point and offer "
    "to go into more detail."
)
MAX_TOKENS = 2048

load_dotenv()  # Reads ANTHROPIC_API_KEY from .env
client = anthropic.Anthropic()


def generate_answer(history, question, voice=False, image=None):
    """Send the history plus the new question to the AI and return the answer text."""
    system_prompt = _system_prompt(voice)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=history + [_user_message(question, image)]
        )
    except anthropic.APIError as e:
        raise LLMError(str(e)) from e

    return "".join(block.text for block in response.content if block.type == "text")


def stream_answer(history, question, voice=False, image=None):
    """Like generate_answer, but yields the answer text piece by piece as it is generated."""
    system_prompt = _system_prompt(voice)

    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=history + [_user_message(question, image)]
    ) as stream:
        yield from stream.text_stream


def _system_prompt(voice):
    """Build the system prompt, adding the spoken-answer rules when voice is True."""
    system_prompt = LANGUAGE_PROMPT
    if voice:
        system_prompt += "\n" + VOICE_PROMPT
    return system_prompt


def _user_message(question, image=None):
    """Build the new user message, with the screenshot before the text if there is one."""
    content = [{"type": "text", "text": question}]
    if image: content.insert(0, {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": image},
    })
    return {"role": "user", "content": content}
