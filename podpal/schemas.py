# podpal/schemas.py
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime

BlendStyle = Literal["narrative", "bullet", "ai_summary"]

class ClipRef(BaseModel):
    clip_id: str = Field(..., description="Unique id of the clip (db id, guid, etc.)")
    source: Optional[str] = Field(None, description="Optional source/podcast identifier")
    start_ms: int = Field(ge=0, description="Start position within this clip, in milliseconds")
    end_ms: int = Field(gt=0, description="End position within this clip, in milliseconds")
    transcript: Optional[str] = Field(
        None,
        description="Optional known transcript for this clip; used for text-only blend stubs."
    )

class BlendSettings(BaseModel):
    temperature: float = Field(0.3, ge=0.0, le=1.0, description="Creativity for AI summarization")
    max_words: int = Field(250, ge=10, le=2000, description="Max words in combined output")
    include_timestamps: bool = Field(True, description="Include timestamps per segment in result")
    language: str = Field("en", description="Target language for summaries")
class AudioSettings(BaseModel):
    make_audio: bool = Field(False, description="Generate a stitched audio file")
    output_format: Literal["mp3", "wav"] = "mp3"
    bitrate_kbps: int = Field(160, description="MP3 bitrate when exporting audio")
    target_lufs: float = Field(-16.0, description="Target loudness for podcast audio")
    crossfade_ms: int = Field(300, description="Crossfade duration between clips")
    fade_in_ms: int = Field(50)
    fade_out_ms: int = Field(50)
    music_bed: Optional[str] = Field(None, description="Path or URL to optional background music")
    music_bed_gain_db: float = Field(-18.0)
    guided_voice: Optional[Literal["none", "tts", "uploaded"]] = "none"
    guided_voice_style: Optional[str] = None
    guided_voice_lang: str = "en-US"
    guided_voice_ducking_db: float = Field(-12.0)
class BlendRequest(BaseModel):
 class BlendRequest(BaseModel):
    title: Optional[str]
    style: BlendStyle
    output: Literal["json", "text"]
    clips: List[ClipRef]
    settings: BlendSettings = Field(default_factory=BlendSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)

class BlendSegment(BaseModel):
    index: int
    clip_id: str
    start_ms: int
    end_ms: int
    summary: str

class BlendResult(BaseModel):
    id: str
    title: Optional[str]
    style: BlendStyle
    segments: List[BlendSegment]
    combined_text: str
    created_at: datetime