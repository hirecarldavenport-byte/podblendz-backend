"""
Narration utilities for PodBlendz.

Purpose:
- Generate short, connective narration from RSS episode summaries
- Convert narration text into audio files
- Never repeat podcast clip content
- Act as an editorial guide between real podcast audio clips

Design principles:
- Deterministic (no hallucination)
- Summary-driven (RSS is source of truth)
- Short and respectful (10–20 seconds of narration)
"""

from typing import Dict
import pyttsx3


# -------------------------------------------------
# TEXT GENERATION
# -------------------------------------------------

def extract_key_idea(summary: str) -> str:
    """
    Extract a concise key idea from an RSS summary.
    Current heuristic: first sentence.
    This can later be upgraded to NLP / LLM while
    keeping the same interface.
    """
    if not summary:
        return "a central idea in the episode"

    sentence = summary.split(".")[0].strip()
    return sentence


def build_transition_narration(
    episode_a: Dict,
    episode_b: Dict,
) -> str:
    """
    Build a narration bridge between two podcast clips.

    Expected episode dict shape:
    {
        "podcast": "Podcast Name",
        "summary": "RSS summary text..."
    }
    """

    idea_a = extract_key_idea(episode_a.get("summary", ""))
    idea_b = extract_key_idea(episode_b.get("summary", ""))

    podcast_a = episode_a.get("podcast", "this podcast")
    podcast_b = episode_b.get("podcast", "the next podcast")

    narration = (
        f"In this clip from {podcast_a}, the focus is on {idea_a}. "
        f"A related perspective comes next from {podcast_b}, "
        f"where the conversation turns to {idea_b}."
    )

    return narration


def build_closing_narration(topic: str) -> str:
    """
    Optional closing narration to conclude a Blendz.
    """

    return (
        f"Taken together, these perspectives offer a deeper look "
        f"at how {topic} shapes the way we think, live, and decide."
    )


# -------------------------------------------------
# AUDIO GENERATION
# -------------------------------------------------

def narrate_to_file(
    text: str,
    output_file: str,
    rate: int = 150,
    volume: float = 0.95,
) -> None:
    """
    Convert narration text into an audio file.

    - Uses offline TTS (pyttsx3)
    - Safe for local development and prototyping
    - Easy to swap for higher-quality voices later
    """

    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)

    engine.save_to_file(text, output_file)
    engine.runAndWait()

    print(f"✅ Narration audio saved → {output_file}")

