import hashlib
import hmac
import time
import requests
import os


# -------------------------------------------------
# Load PodcastIndex credentials
# -------------------------------------------------

PODCASTINDEX_API_KEY = os.environ.get("PODCASTINDEX_API_KEY")
PODCASTINDEX_API_SECRET = os.environ.get("PODCASTINDEX_API_SECRET")

if not PODCASTINDEX_API_KEY or not PODCASTINDEX_API_SECRET:
    raise RuntimeError(
        "PodcastIndex API credentials are not set. "
        "Please set PODCASTINDEX_API_KEY and PODCASTINDEX_API_SECRET."
    )


BASE_URL = "https://api.podcastindex.org/api/1.0"


# -------------------------------------------------
# PodcastIndex authentication headers
# -------------------------------------------------

def _auth_headers() -> dict:
    # ✅ Strong type guarantee for Pylance *and* runtime
    assert PODCASTINDEX_API_SECRET is not None
    assert PODCASTINDEX_API_KEY is not None

    epoch = str(int(time.time()))

    auth_string = PODCASTINDEX_API_KEY + PODCASTINDEX_API_SECRET + epoch
    digest = hashlib.sha1(auth_string.encode("utf-8")).hexdigest()

    return {
        "X-Auth-Date": epoch,
        "X-Auth-Key": PODCASTINDEX_API_KEY,
        "Authorization": digest,
        "User-Agent": "PodBlendz/1.0",
    }


# -------------------------------------------------
# PodcastIndex search wrapper
# -------------------------------------------------

def search_podcasts(query: str, limit: int = 20) -> list:
    """
    Search PodcastIndex by term and return RSS feed URLs.
    """
    url = f"{BASE_URL}/search/byterm"
    params = {
        "q": query,
        "max": limit,
        "clean": True,
    }

    response = requests.get(
        url,
        headers=_auth_headers(),
        params=params,
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    feeds = data.get("feeds", [])

    return [f["url"] for f in feeds if isinstance(f, dict) and "url" in f]
def search_podcasts_by_title(query: str, limit: int = 10) -> list:
    """
    Search PodcastIndex by podcast TITLE only and return RSS feed URLs.
    High-precision, low-noise search.
    """
    url = f"{BASE_URL}/search/bytitle"
    params = {
        "q": query,
        "max": limit,
        "clean": True,
    }

    response = requests.get(
        url,
        headers=_auth_headers(),
        params=params,
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    feeds = data.get("feeds", [])

    return [f["url"] for f in feeds if isinstance(f, dict) and "url" in f]