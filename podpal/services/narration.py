from typing import List, Dict


def generate_podcast_list_sentence(podcasts: List[Dict]) -> str:
    titles = [p["title"] for p in podcasts if p.get("title")]

    if not titles:
        return "This blend brings together selected podcast moments."

    if len(titles) == 1:
        return f"This blend brings together moments from {titles[0]}."

    return (
        "This blend brings together moments from "
        + ", ".join(titles[:-1])
        + f", and {titles[-1]}."
    )


def generate_topics_sentence(podcasts: List[Dict]) -> str:
    # Very simple v1 topic extraction (safe, deterministic)
    keywords = set()

    for podcast in podcasts:
        for episode in podcast.get("episodes", []):
            title = episode.get("title", "")
            for word in title.split():
                if len(word) > 5:
                    keywords.add(word.lower())

    top_topics = list(keywords)[:3]

    if not top_topics:
        return "The moments you’re about to hear span recent discussions."

    return (
        "The moments you’re about to hear span recent discussions on "
        + ", ".join(top_topics)
        + "."
    )


def generate_blend_narration(podcasts: List[Dict]) -> str:
    return "\n\n".join([
        generate_podcast_list_sentence(podcasts),
        "Together, these podcasts examine how current events and ideas shape modern life.",
        generate_topics_sentence(podcasts),
        "This is your blendz."
    ])

