"""
Turn a blend into a 30-second vertical video for TikTok, Reels and Shorts,
with captions, a moving sound wave, the shows in it, and a ready-to-post caption
that @tags the podcasters.

Run from the podblendz-backend folder:

    python scripts/make_clip.py 8eefdea6-c382-42f4-82a6-...
    python scripts/make_clip.py <blend_id> --start 40 --length 25
    python scripts/make_clip.py <blend_id> --audio C:\\path\\final.mp3

Captions need faster-whisper once:   pip install faster-whisper
Output goes to clips/<blend_id>/  (clip.mp4 + caption.txt)
"""

import argparse
import array
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "podpal", "assets", "fonts")
BLEND_API = "https://api.podblendz.com/blend/"
AUDIO_URL = "https://podblendz-episode-audio.s3.us-east-1.amazonaws.com/blends/{id}/final.mp3"
BACKEND = "https://podblendz-backend.onrender.com"
SHARE = BACKEND + "/b/{id}?src={src}"

W, H, FPS = 1080, 1920, 30
ORANGE = (255, 106, 0)
HASHTAGS = {
    "brain health": "#brainhealth #sleep #wellness",
    "ai": "#ai #tech #futureofwork",
    "business": "#business #entrepreneur #career",
    "science": "#science #learnontiktok",
    "neurodiversity": "#neurodiversity #autism #actuallyautistic",
}


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("ffmpeg not found. Install it, or: pip install imageio-ffmpeg")


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "PodBlendz clip maker"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def pretty(name):
    return name.replace("_", " ").title() if name == name.lower() else name


# ---------------------------------------------------------------- audio

def cut_audio(src, start, length, folder):
    """the clip's audio (m4a) and a 16 kHz mono copy for captions and the wave"""
    ff = ffmpeg()
    m4a = os.path.join(folder, "clip.m4a")
    wav = os.path.join(folder, "clip16k.wav")
    fade = max(0.0, length - 0.6)
    subprocess.run([ff, "-loglevel", "error", "-y", "-ss", str(start), "-t", str(length), "-i", src,
                    "-af", f"afade=t=in:d=0.3,afade=t=out:st={fade}:d=0.6", "-c:a", "aac", "-b:a", "160k", m4a], check=True)
    subprocess.run([ff, "-loglevel", "error", "-y", "-i", m4a, "-ac", "1", "-ar", "16000", wav], check=True)
    return m4a, wav


def loudness_per_frame(wav, frames):
    """0..1 loudness for each video frame, to drive the wave"""
    with open(wav, "rb") as f:
        data = f.read()[44:]
    pcm = array.array("h"); pcm.frombytes(data[: len(data) // 2 * 2])
    per = max(1, len(pcm) // frames)
    levels = []
    for i in range(frames):
        chunk = pcm[i * per:(i + 1) * per] or array.array("h", [0])
        levels.append(math.sqrt(sum(s * s for s in chunk[::8]) / max(1, len(chunk[::8]))))
    peak = max(levels) or 1
    return [min(1.0, (v / peak) ** 0.7) for v in levels]


def transcribe(wav):
    """word-by-word captions with timings, or [] if faster-whisper isn't installed"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("  (no captions: run  pip install faster-whisper  to add them)")
        return []
    print("  writing captions…")
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(wav, word_timestamps=True, vad_filter=True)
    words = []
    for seg in segments:
        for w in seg.words or []:
            t = w.word.strip()
            if t:
                words.append({"start": w.start, "end": w.end, "text": t})
    return words


def caption_groups(words, max_chars=26):
    """split words into on-screen lines of a few words each"""
    groups, cur = [], []
    for w in words:
        test = " ".join(x["text"] for x in cur + [w])
        gap = cur and w["start"] - cur[-1]["end"] > 0.6
        if cur and (len(test) > max_chars or gap or cur[-1]["text"][-1:] in ".?!"):
            groups.append(cur); cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


# ---------------------------------------------------------------- drawing

def wrap(draw, text, fnt, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]; lines[-1] = lines[-1].rstrip(",.") + "…"
    return lines


def background(title, board, shows):
    img = Image.new("RGB", (W, H), (8, 8, 8))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse((-200, 700, 1280, 1900), fill=(110, 44, 0))
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(220)), 0.9)
    d = ImageDraw.Draw(img)

    d.ellipse((80, 120, 116, 156), fill=ORANGE)
    d.text((134, 110), "PodBlendz", font=font("Inter-ExtraBold.otf", 50), fill="white")

    y = 240
    if board:
        f = font("Inter-Bold.otf", 34)
        tw = d.textlength(board.upper(), font=f)
        d.rounded_rectangle((80, y, 80 + tw + 52, y + 64), 32, outline=ORANGE, width=3)
        d.text((106, y + 11), board.upper(), font=f, fill=ORANGE)
        y += 100

    for size in (78, 70, 62, 56):
        f = font("Inter-ExtraBold.otf", size)
        lines = wrap(d, title, f, W - 160, 4)
        if not lines[-1].endswith("…"):
            break
    for ln in lines:
        d.text((80, y), ln, font=f, fill="white")
        y += int(size * 1.17)

    if shows:
        f = font("Inter-Medium.otf", 36)
        d.text((80, 1610), "Featuring", font=f, fill=(170, 170, 170))
        fb = font("Inter-Bold.otf", 40)
        line = " · ".join(shows)
        while d.textlength(line, font=fb) > W - 160 and len(line) > 10:
            line = line[:-2]
        if line != " · ".join(shows):
            line = line.rstrip(" ·") + "…"
        d.text((80, 1660), line, font=fb, fill="white")
    return img, y


def wave(d, level, t, top):
    """a row of bars that move with the voice"""
    n, gap = 31, 26
    x0 = (W - (n - 1) * gap) // 2
    cy = top + 170
    for k in range(n):
        shape = 0.35 + 0.65 * abs(math.sin(k * 0.42 + t * 3.1)) * (1 - abs(k - n // 2) / (n * 0.75))
        h = 18 + 230 * level * shape
        x = x0 + k * gap
        d.rounded_rectangle((x - 7, cy - h / 2, x + 7, cy + h / 2), 7, fill=ORANGE if k % 4 else (255, 160, 90))


def caption(d, group, t):
    if not group:
        return
    f = font("Inter-ExtraBold.otf", 64)
    words = [w["text"] for w in group]
    widths = [d.textlength(w, font=f) for w in words]
    space = d.textlength(" ", font=f)
    total = sum(widths) + space * (len(words) - 1)
    if total > W - 120:   # two lines
        mid = len(words) // 2
        rows = [list(range(0, mid)), list(range(mid, len(words)))]
    else:
        rows = [list(range(len(words)))]
    y = 1330 - (len(rows) - 1) * 44
    for row in rows:
        rw = sum(widths[i] for i in row) + space * (len(row) - 1)
        x = (W - rw) / 2
        for i in row:
            on = group[i]["start"] <= t + 0.05
            colour = ORANGE if group[i]["start"] <= t <= group[i]["end"] + 0.15 else ("white" if on else (150, 150, 150))
            d.text((x + 3, y + 4), words[i], font=f, fill=(0, 0, 0))
            d.text((x, y), words[i], font=f, fill=colour)
            x += widths[i] + space
        y += 88


def end_card(shows):
    img = Image.new("RGB", (W, H), (8, 8, 8))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse((90, 520, 990, 1420), fill=(130, 52, 0))
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(200)), 0.9)
    d = ImageDraw.Draw(img)
    def centre(text, f, y, fill="white"):
        d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)
    centre("PodBlendz", font("Inter-ExtraBold.otf", 96), 700)
    centre("One question. Many voices.", font("Inter-Medium.otf", 46), 830, (220, 220, 220))
    f = font("Inter-Bold.otf", 48)
    label = "Hear the full blend"
    tw = d.textlength(label, font=f)
    d.rounded_rectangle(((W - tw) / 2 - 50, 960, (W + tw) / 2 + 50, 1060), 50, fill=ORANGE)
    centre(label, f, 982)
    centre("podblendz.com", font("Inter-Bold.otf", 44), 1110, (220, 220, 220))
    if shows:
        centre("with " + " · ".join(shows[:3]) + (" and more" if len(shows) > 3 else ""),
               font("Inter-Medium.otf", 34), 1240, (170, 170, 170))
    return img


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Make a 30-second social clip from a blend")
    ap.add_argument("blend_id")
    ap.add_argument("--start", type=float, default=12, help="seconds into the blend (default 12, after the intro)")
    ap.add_argument("--length", type=float, default=30, help="clip length in seconds (default 30)")
    ap.add_argument("--audio", help="use a local blend MP3 instead of downloading it")
    ap.add_argument("--captions", help="(testing) a JSON file of words instead of running Whisper")
    ap.add_argument("--out", default="clips")
    a = ap.parse_args()

    print(f"Making a clip for {a.blend_id}")
    blend = get_json(BLEND_API + urllib.parse.quote(a.blend_id))
    title, board = blend.get("title") or "A PodBlendz blend", blend.get("board") or ""
    names = blend.get("creators") or []

    socials = {}
    if names:
        try:
            socials = get_json(BACKEND + "/creators/socials?names=" + urllib.parse.quote(",".join(names)))
        except Exception:
            print("  (couldn't load social handles; the caption will use show names)")
    shows = [(socials.get(n) or {}).get("display_name") or pretty(n) for n in names]

    out = os.path.join(a.out, a.blend_id)
    os.makedirs(out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = a.audio
        if not src:
            print("  downloading the blend audio…")
            src = os.path.join(tmp, "final.mp3")
            urllib.request.urlretrieve(AUDIO_URL.format(id=urllib.parse.quote(a.blend_id)), src)
        m4a, wav = cut_audio(src, a.start, a.length, tmp)

        words = json.load(open(a.captions)) if a.captions else transcribe(wav)
        groups = caption_groups(words)

        end_len = 2.5
        total = int(a.length * FPS)
        end_from = int((a.length - end_len) * FPS)
        levels = loudness_per_frame(wav, total)
        base, title_bottom = background(title, board, shows)
        wave_top = max(title_bottom + 40, 900)
        last = end_card(shows)

        print("  drawing the video…")
        tmp_mp4 = os.path.join(out, "clip.part.mp4")
        proc = subprocess.Popen([ffmpeg(), "-loglevel", "error", "-y",
                                 "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                 "-i", m4a, "-map", "0:v", "-map", "1:a",
                                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                                 "-c:a", "copy", "-shortest", "-movflags", "+faststart", tmp_mp4],
                                stdin=subprocess.PIPE)
        gi = 0
        for i in range(total):
            t = i / FPS
            if i >= end_from:
                k = min(1.0, (i - end_from) / 8)
                frame = Image.blend(base, last, k) if k < 1 else last
            else:
                frame = base.copy()
                d = ImageDraw.Draw(frame)
                wave(d, levels[i], t, wave_top)
                while gi + 1 < len(groups) and groups[gi + 1][0]["start"] <= t:
                    gi += 1
                g = groups[gi] if groups and groups[gi][0]["start"] <= t + 0.2 and t <= groups[gi][-1]["end"] + 0.8 else None
                caption(d, g, t)
                # progress line along the bottom
                d.rounded_rectangle((80, 1800, W - 80, 1808), 4, fill=(45, 45, 45))
                d.rounded_rectangle((80, 1800, 80 + (W - 160) * (i / end_from), 1808), 4, fill=ORANGE)
            if i < 6:
                frame = Image.blend(Image.new("RGB", (W, H)), frame, (i + 1) / 6)
            buf = io.BytesIO(); frame.save(buf, "JPEG", quality=90)
            proc.stdin.write(buf.getvalue())
        proc.stdin.close()
        if proc.wait() != 0:
            sys.exit("ffmpeg failed")
        final = os.path.join(out, "clip.mp4")
        os.replace(tmp_mp4, final)

    # the post caption, with @tags where we have them
    tags = []
    for n in names:
        s = socials.get(n) or {}
        h = s.get("tiktok") or s.get("instagram") or s.get("x")
        tags.append("@" + h if h else ((s.get("display_name")) or pretty(n)))
    text = (f"{title}\n\n"
            f"{len(names) or 'Several'} podcasts, one answer 🎧 Featuring {', '.join(tags)}\n\n"
            f"Full blend: {SHARE.format(id=a.blend_id, src='tiktok')}\n\n"
            f"#podcast #podblendz {HASHTAGS.get(board.lower(), '')}").strip()
    with open(os.path.join(out, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n\n(Instagram: swap ?src=tiktok for ?src=instagram in the link.)\n")
    print(f"Done:\n  {final}\n  {os.path.join(out, 'caption.txt')}")


if __name__ == "__main__":
    main()
