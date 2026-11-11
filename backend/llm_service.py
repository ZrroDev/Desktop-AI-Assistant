"""LLM calls made by the backend. The only module that knows which AI provider is used."""

import anthropic
from dotenv import load_dotenv

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

def generate_answer(history, question, voice=False):
    """Send the history plus the new question to Claude and return the answer text."""
    system_prompt = LANGUAGE_PROMPT
    if voice:
        system_prompt += "\n" + VOICE_PROMPT

    response = client.messages.create(
        model = MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=history + [{"role": "user", "content": question}]
    )

    return "".join(block.text for block in response.content if block.type == "text")