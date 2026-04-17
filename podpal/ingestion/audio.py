from contextlib import contextmanager
import os
import tempfile
import requests


@contextmanager
def _download_to_tempfile(url: str):
    """
    Stream-download audio to a temporary file.

    This is a proper context manager that guarantees cleanup.
    """
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    suffix = os.path.splitext(url)[-1] or ".mp3"

    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    )

    try:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                tmp.write(chunk)

        tmp.flush()
        tmp.close()

        yield tmp.name

    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)
