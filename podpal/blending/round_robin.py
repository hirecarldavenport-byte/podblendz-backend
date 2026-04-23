from typing import Dict, List, Any, Optional


def round_robin_blend(
    episodes_by_podcaster: Dict[Any, List[Any]],
    max_per_podcaster: int = 1,
    max_total: Optional[int] = None,
) -> List[Any]:
    """
    Fairly interleave episodes across podcasters.

    Args:
        episodes_by_podcaster:
            Dictionary mapping podcaster_id -> list of episode rows.
            Lists should already be ordered (e.g., latest first).

        max_per_podcaster:
            Maximum number of episodes each podcaster may contribute.

        max_total:
            Optional hard cap on total episodes returned.

    Returns:
        A list of blended episode rows.
    """

    blended: List[Any] = []

    # Track how many episodes we have taken per podcaster
    taken_count = {pid: 0 for pid in episodes_by_podcaster}

    while True:
        added_any = False

        for podcaster_id, episode_list in episodes_by_podcaster.items():
            # Skip empty episode lists
            if not episode_list:
                continue

            # Respect per-podcaster cap
            if taken_count[podcaster_id] >= max_per_podcaster:
                continue

            # Respect available episodes
            if taken_count[podcaster_id] >= len(episode_list):
                continue

            # Take the next episode
            blended.append(episode_list[taken_count[podcaster_id]])
            taken_count[podcaster_id] += 1
            added_any = True

            # Respect global cap
            if max_total is not None and len(blended) >= max_total:
                return blended

        # Stop if no podcaster could add an episode this round
        if not added_any:
            break

    return blended
