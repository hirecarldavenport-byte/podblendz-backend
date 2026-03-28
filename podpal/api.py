from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime
from pathlib import Path
from typing import Literal

# ------------------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------------------

app = FastAPI(
    title="Pod Blendz API",
    description="Backend services for Pod Blendz audio generation",
    version="0.1.0",
)

# ------------------------------------------------------------------------------
# Directories
# ------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
MEDIA_DIR = BASE_DIR / "media"

OUTPUT_DIR.mkdir(exist_ok=True)
MEDIA_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------------------
# Meta / Health
# ------------------------------------------------------------------------------

@app.get("/health", include_in_schema=False)
def health():
    return {
        "status": "ok",
        "service": "pod-blendz",
        "time": datetime.utcnow().isoformat(),
    }

@app.get("/version", include_in_schema=False)
def version():
    return {
        "version": "0.1.0",
        "build": "render",
    }

@app.get("/info", include_in_schema=False)
def info():
    return {
        "service": "Pod Blendz",
        "status": "running",
        "output_dir": str(OUTPUT_DIR),
    }

# ------------------------------------------------------------------------------
# 🚫 IMPORTANT: NO ROOT ("/") ROUTE
# ------------------------------------------------------------------------------
# DO NOT add @app.get("/")
# CloudFront/S3 owns "/" and "/index.html"
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# API ROUTES
# ------------------------------------------------------------------------------

@app.get("/rss/search")
def rss_search(
    q: str = Query(..., description="Search term"),
    source: Literal["itunes", "podcastindex"] = "itunes",
    country: str = Query("US", min_length=2, max_length=2),
    limit: int = Query(25, ge=1, le=50),
):
    """
    Search podcast feeds.
    """
    # Stubbed search response (replace with real implementation)
    results = [
        {
            "title": f"Sample podcast result for '{q}'",
            "source": source,
            "country": country,
        }
    ]

    return {
        "query": q,
        "source": source,
        "results": results[:limit],
    }

# ------------------------------------------------------------------------------
# Generated Output Files
# ------------------------------------------------------------------------------

@app.get("/blend/file")
def get_blend_file(name: str):
    """
    Retrieve a generated blend file
    """
    file_path = OUTPUT_DIR / name
    if not file_path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": f"File not found: {name}"},
        )

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=name,
    )

@app.get("/output/files")
def list_output_files():
    """
    List generated output files
    """
    if not OUTPUT_DIR.exists():
        return []

    return sorted(
        f.name for f in OUTPUT_DIR.iterdir() if f.is_file()
    )

@app.get("/media/clips")
def list_media_clips():
    """
    List uploaded or generated media clips
    """
    if not MEDIA_DIR.exists():
        return []

    return sorted(
        f.name for f in MEDIA_DIR.iterdir() if f.is_file()
    )

# ------------------------------------------------------------------------------
# END OF FILE
# ------------------------------------------------------------------------------