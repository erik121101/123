import os
import uuid
import subprocess
import requests
import threading
import json
import math
from flask import Flask, request, jsonify, send_file, send_from_directory, session, redirect
from pathlib import Path

# Load .env if present
env_path = Path(".env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ── Setup static-ffmpeg ───────────────────────────────────────────────────────
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    print("✅ static-ffmpeg loaded")
except Exception as e:
    print(f"⚠️ static-ffmpeg error: {e}")

app = Flask(__name__, static_folder='static')
app.secret_key = "xK9#mP2$vL7nQ4wR"

PASSWORD = "9357"

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
MUSIC_DIR = Path("music")
MUSIC_DIR.mkdir(exist_ok=True)

jobs = {}

GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
CARTESIA_API_KEY   = os.environ.get("CARTESIA_API_KEY", "")
CARTESIA_VOICE_ID  = os.environ.get("CARTESIA_VOICE_ID", "e1def6dd-c945-4630-bb41-d29c79e1e489")


def update_job(job_id, **kwargs):
    jobs[job_id].update(kwargs)


def translate_to_romanian(text):
    chunks = []
    while len(text) > 4500:
        split_at = text.rfind('. ', 0, 4500)
        if split_at == -1:
            split_at = 4500
        chunks.append(text[:split_at + 1])
        text = text[split_at + 1:]
    chunks.append(text)

    translated_chunks = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        resp = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "ro", "dt": "t", "q": chunk},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        translated = "".join(part[0] for part in data[0] if part[0])
        translated_chunks.append(translated)

    return " ".join(translated_chunks)


def generate_tts_cartesia(text, output_path):
    key = CARTESIA_API_KEY
    if not key:
        raise Exception("CARTESIA_API_KEY lipsă. Adaugă-l în Railway → Variables.")

    MAX_CHARS = 4500
    chunks = []
    while len(text) > MAX_CHARS:
        split_at = text.rfind('. ', 0, MAX_CHARS)
        if split_at == -1:
            split_at = MAX_CHARS
        chunks.append(text[:split_at + 1].strip())
        text = text[split_at + 1:].strip()
    if text:
        chunks.append(text)

    audio_parts = []
    for chunk in chunks:
        if not chunk:
            continue
        resp = requests.post(
            "https://api.cartesia.ai/tts/bytes",
            headers={
                "Cartesia-Version": "2026-03-01",
                "X-API-Key": key,
                "Content-Type": "application/json",
            },
            json={
                "model_id": "sonic-3.5",
                "transcript": chunk,
                "voice": {
                    "mode": "id",
                    "id": CARTESIA_VOICE_ID,
                },
                "output_format": {
                    "container": "mp3",
                    "encoding": "mp3",
                    "sample_rate": 44100,
                },
                "language": "ro",
            },
            timeout=120
        )
        if resp.status_code != 200:
            raise Exception(f"Cartesia eroare {resp.status_code}: {resp.text[:300]}")
        audio_parts.append(resp.content)

    with open(output_path, "wb") as f:
        for part in audio_parts:
            f.write(part)


def get_duration(path):
    """Returns duration in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=30
    )
    try:
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def text_to_srt(text, audio_duration, output_path):
    """
    Splits text into caption chunks and generates a .srt file
    timed to match the audio duration.
    """
    words = text.split()
    if not words:
        return

    # ~3 words per caption line, adjust as needed
    WORDS_PER_LINE = 6
    lines = []
    for i in range(0, len(words), WORDS_PER_LINE):
        lines.append(" ".join(words[i:i + WORDS_PER_LINE]))

    time_per_line = audio_duration / len(lines) if lines else 1.0

    def fmt_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    srt_content = ""
    for i, line in enumerate(lines):
        start = i * time_per_line
        end = (i + 1) * time_per_line
        srt_content += f"{i+1}\n{fmt_time(start)} --> {fmt_time(end)}\n{line}\n\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)


def run_pipeline(job_id, url, music_filename=None, bg_volume=0.08, custom_text=None):
    job_dir = DOWNLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    try:
        # ── STEP 1: Download ──────────────────────────────────────────────
        update_job(job_id, step="Se descarcă videoclipul...", progress=10)
        video_path = job_dir / "video.mp4"

        ytdlp_attempts = [
            ["yt-dlp", "--js-runtimes", "deno",
             "--extractor-args", "youtube:player_client=ios",
             "-f", "b[ext=mp4]/b", "-o", str(video_path), url],
            ["yt-dlp", "--js-runtimes", "deno",
             "--extractor-args", "youtube:player_client=android",
             "-f", "b[ext=mp4]/b", "-o", str(video_path), url],
            ["yt-dlp", "--js-runtimes", "deno",
             "-f", "b[ext=mp4]/b", "-o", str(video_path), url],
        ]

        last_err = ""
        for attempt in ytdlp_attempts:
            result = subprocess.run(attempt, capture_output=True, text=True, timeout=180)
            if result.returncode == 0:
                break
            last_err = result.stderr[:500]
        else:
            raise Exception(f"Download eșuat: {last_err}")

        if not video_path.exists():
            all_videos = (list(job_dir.glob("*.mp4")) +
                         list(job_dir.glob("*.webm")) +
                         list(job_dir.glob("*.mkv")))
            if all_videos:
                video_path = all_videos[0]
            else:
                raise Exception("Niciun fișier video găsit după download.")

        # ── STEP 2: Mute video ────────────────────────────────────────────
        update_job(job_id, step="Se pune video pe mut...", progress=22)
        muted_path = job_dir / "video_muted.mp4"

        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path),
             "-an", "-c:v", "copy", str(muted_path)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise Exception(f"Mute video eșuat: {result.stderr[:300]}")

        video_duration = get_duration(muted_path)

        # ── STEP 3: Extract audio for transcription ───────────────────────
        update_job(job_id, step="Se extrage audio pentru transcriere...", progress=30)
        audio_path = job_dir / "audio.mp3"

        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path),
             "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(audio_path)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise Exception(f"Extragere audio eșuată: {result.stderr[:300]}")

        # ── STEP 4: Transcribe cu Groq Whisper ────────────────────────────
        update_job(job_id, step="Se transcrie cu Groq Whisper...", progress=42)

        key = GROQ_API_KEY
        if not key:
            raise Exception("GROQ_API_KEY lipsă. Adaugă-l în Railway → Variables.")

        with open(audio_path, "rb") as f:
            audio_data = f.read()

        response = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {key}"},
            files={"file": ("audio.mp3", audio_data, "audio/mpeg")},
            data={"model": "whisper-large-v3", "response_format": "json"},
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"Groq eroare {response.status_code}: {response.text[:300]}")

        transcript_text = response.json().get("text", "")
        if not transcript_text:
            raise Exception("Groq a returnat o transcriere goală.")

        transcript_orig_path = job_dir / "transcript_original.txt"
        transcript_orig_path.write_text(transcript_text, encoding="utf-8")

        # ── STEP 5: Translate ─────────────────────────────────────────────
        update_job(job_id, step="Se traduce în română...", progress=55)
        romanian_text = translate_to_romanian(transcript_text)

        transcript_ro_path = job_dir / "transcript_romana.txt"
        transcript_ro_path.write_text(romanian_text, encoding="utf-8")

        # Use custom text if user edited it in the mini-editor
        tts_text = custom_text if custom_text and custom_text.strip() else romanian_text
        update_job(job_id, step="Traducere gata. Așteptăm confirmarea textului...", progress=60,
                   status="awaiting_confirmation",
                   preview={
                       "original": transcript_text[:800],
                       "romanian": romanian_text[:800],
                   },
                   romanian_text=romanian_text)
        return  # Pause here — user must confirm/edit text before continuing

    except Exception as e:
        update_job(job_id, status="error", error=str(e), step="Eroare")


def run_pipeline_part2(job_id, tts_text, music_filename=None, bg_volume=0.08):
    """Called after user confirms/edits the Romanian text."""
    job_dir = DOWNLOAD_DIR / job_id

    try:
        muted_path = job_dir / "video_muted.mp4"
        video_duration = get_duration(muted_path)

        # ── STEP 6: TTS cu Cartesia ───────────────────────────────────────
        update_job(job_id, step="Se generează vocea în română (Cartesia)...", progress=68,
                   status="running")
        tts_path = job_dir / "voce_romana.mp3"
        generate_tts_cartesia(tts_text, tts_path)

        tts_duration = get_duration(tts_path)

        # ── STEP 7: Generate SRT captions ────────────────────────────────
        update_job(job_id, step="Se generează captionurile...", progress=76)
        srt_path = job_dir / "captions.srt"
        text_to_srt(tts_text, tts_duration, srt_path)

        # ── STEP 8: Mix audio ─────────────────────────────────────────────
        update_job(job_id, step="Se mixează audio-ul...", progress=82)

        music_path = MUSIC_DIR / music_filename if music_filename else None
        mixed_audio_path = job_dir / "mixed_audio.mp3"

        if music_path and music_path.exists():
            # Loop music to match TTS duration, lower volume
            result = subprocess.run(
                ["ffmpeg", "-y",
                 "-stream_loop", "-1", "-i", str(music_path),
                 "-i", str(tts_path),
                 "-filter_complex",
                 f"[0:a]volume={bg_volume}[bg];[bg][1:a]amix=inputs=2:duration=first:dropout_transition=2[out]",
                 "-map", "[out]",
                 "-t", str(tts_duration),
                 "-acodec", "libmp3lame", "-q:a", "2",
                 str(mixed_audio_path)],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                raise Exception(f"Mix audio eșuat: {result.stderr[:300]}")
            final_audio = mixed_audio_path
        else:
            final_audio = tts_path

        # ── STEP 9: Combine video + audio + captions ──────────────────────
        update_job(job_id, step="Se compilează videoclipul final...", progress=90)
        final_path = job_dir / "final.mp4"

        # Use subtitles filter to burn captions into video
        # Loop video if TTS is longer than video
        srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
        # Use force_style for nice-looking captions
        subtitle_filter = (
            f"subtitles='{srt_escaped}':"
            f"force_style='FontName=Arial,FontSize=18,Bold=1,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            f"BackColour=&H80000000,Outline=2,Shadow=1,"
            f"Alignment=2,MarginV=30'"
        )

        result = subprocess.run(
            ["ffmpeg", "-y",
             "-stream_loop", "-1", "-i", str(muted_path),
             "-i", str(final_audio),
             "-filter_complex",
             f"[0:v]{subtitle_filter}[v]",
             "-map", "[v]",
             "-map", "1:a",
             "-c:v", "libx264", "-crf", "20", "-preset", "fast",
             "-c:a", "aac", "-b:a", "128k",
             "-t", str(tts_duration),
             "-shortest",
             str(final_path)],
            capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0:
            # Fallback: without burned-in captions
            print(f"Caption burn failed, trying without: {result.stderr[:200]}")
            result = subprocess.run(
                ["ffmpeg", "-y",
                 "-stream_loop", "-1", "-i", str(muted_path),
                 "-i", str(final_audio),
                 "-c:v", "libx264", "-crf", "20", "-preset", "fast",
                 "-c:a", "aac", "-b:a", "128k",
                 "-t", str(tts_duration),
                 "-shortest",
                 str(final_path)],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise Exception(f"Compilare video eșuată: {result.stderr[:300]}")

        # ── DONE ──────────────────────────────────────────────────────────
        transcript_orig_path = job_dir / "transcript_original.txt"
        transcript_ro_path = job_dir / "transcript_romana.txt"

        update_job(
            job_id,
            step="Gata!",
            progress=100,
            status="done",
            files={
                "final_video":           final_path.name,
                "tts_romanian":          tts_path.name,
                "captions_srt":          srt_path.name,
                "transcript_original":   transcript_orig_path.name,
                "transcript_romanian":   transcript_ro_path.name,
            },
        )

    except Exception as e:
        update_job(job_id, status="error", error=str(e), step="Eroare")


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.before_request
def check_password():
    public_paths = ('/login', '/static')
    if any(request.path.startswith(p) for p in public_paths):
        return None
    if not session.get('authenticated'):
        return redirect('/login')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("parola", "") == PASSWORD:
            session['authenticated'] = True
            return redirect('/')
        return redirect('/login?error=1')
    return send_from_directory("static", "login.html")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/upload-music", methods=["POST"])
def upload_music():
    f = request.files.get("music")
    if not f:
        return jsonify({"error": "Niciun fișier primit"}), 400
    safe_name = "".join(c for c in f.filename if c.isalnum() or c in "._- ").strip()
    if not safe_name:
        safe_name = "music.mp3"
    save_path = MUSIC_DIR / safe_name
    f.save(str(save_path))
    return jsonify({"filename": safe_name})


@app.route("/list-music")
def list_music():
    files = [p.name for p in MUSIC_DIR.iterdir() if p.is_file()]
    return jsonify({"files": files})


@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Niciun URL furnizat"}), 400

    music_filename = data.get("music_filename") or None
    bg_volume = float(data.get("bg_volume", 0.08))

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "running",
        "step": "Se pornește...",
        "progress": 0,
        "music_filename": music_filename,
        "bg_volume": bg_volume,
    }
    threading.Thread(
        target=run_pipeline,
        args=(job_id, url, music_filename, bg_volume),
        daemon=True
    ).start()
    return jsonify({"job_id": job_id})


@app.route("/confirm", methods=["POST"])
def confirm():
    """User confirms (or edits) the Romanian text, pipeline continues."""
    data = request.get_json()
    job_id = data.get("job_id", "")
    tts_text = data.get("tts_text", "").strip()

    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job negăsit"}), 404
    if job.get("status") != "awaiting_confirmation":
        return jsonify({"error": "Job-ul nu așteaptă confirmare"}), 400

    music_filename = job.get("music_filename")
    bg_volume = job.get("bg_volume", 0.08)

    update_job(job_id, status="running", step="Se continuă procesarea...", progress=62)
    threading.Thread(
        target=run_pipeline_part2,
        args=(job_id, tts_text, music_filename, bg_volume),
        daemon=True
    ).start()
    return jsonify({"ok": True})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job negăsit"}), 404
    return jsonify(job)


@app.route("/edit")
def edit():
    return send_from_directory("static", "edit.html")


@app.route("/export", methods=["POST"])
def export_video():
    data = request.get_json()
    job_id = data.get("job_id", "")
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job negăsit"}), 404
    if job.get("status") != "done":
        return jsonify({"error": "Job-ul sursă nu este terminat"}), 400

    trim_start    = float(data.get("trim_start", 0))
    trim_end      = float(data.get("trim_end", 0))
    captions_srt  = data.get("captions", "")
    caption_size  = int(data.get("caption_font_size", 15))
    music_filename = data.get("music_filename") or None
    music_start   = float(data.get("music_start", 0))
    music_volume  = float(data.get("music_volume", 0.08))

    export_job_id = "exp_" + str(uuid.uuid4())
    jobs[export_job_id] = {
        "status": "running",
        "step": "Se pregătește exportul...",
        "progress": 10,
    }
    threading.Thread(
        target=run_export_pipeline,
        args=(export_job_id, job_id, trim_start, trim_end,
              captions_srt, caption_size, music_filename, music_start, music_volume),
        daemon=True
    ).start()
    return jsonify({"export_job_id": export_job_id})


def run_export_pipeline(export_job_id, source_job_id, trim_start, trim_end,
                        captions_srt, caption_size, music_filename, music_start, music_volume):
    src_dir = DOWNLOAD_DIR / source_job_id
    out_dir = DOWNLOAD_DIR / export_job_id
    out_dir.mkdir(exist_ok=True)

    try:
        # ── Source files ──────────────────────────────────────────────────
        src_job = jobs[source_job_id]
        src_files = src_job.get("files", {})

        muted_src = src_dir / "video_muted.mp4"
        tts_src   = src_dir / (src_files.get("tts_romanian") or "voce_romana.mp3")

        if not muted_src.exists():
            raise Exception("Video mut sursă negăsit.")
        if not tts_src.exists():
            raise Exception("Audio TTS sursă negăsit.")

        # ── STEP 1: Trim video ────────────────────────────────────────────
        update_job(export_job_id, step="Se taie videoclipul...", progress=20)
        trimmed_video = out_dir / "trimmed_video.mp4"
        duration = trim_end - trim_start if trim_end > trim_start else None

        trim_cmd = ["ffmpeg", "-y", "-i", str(muted_src)]
        if trim_start > 0:
            trim_cmd += ["-ss", str(trim_start)]
        if duration:
            trim_cmd += ["-t", str(duration)]
        trim_cmd += ["-c:v", "copy", str(trimmed_video)]

        result = subprocess.run(trim_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise Exception(f"Trim video eșuat: {result.stderr[:300]}")

        # ── STEP 2: Write new SRT ─────────────────────────────────────────
        update_job(export_job_id, step="Se scriu captionurile...", progress=35)
        srt_path = out_dir / "captions.srt"
        # Adjust caption times if trimmed
        if trim_start > 0 and captions_srt:
            adjusted = _shift_srt(captions_srt, -trim_start)
        else:
            adjusted = captions_srt
        srt_path.write_text(adjusted or "", encoding="utf-8")

        # ── STEP 3: Mix audio ──────────────────────────────────────────────
        update_job(export_job_id, step="Se mixează audio-ul...", progress=50)

        # Trim TTS if needed
        trimmed_tts = out_dir / "tts_trimmed.mp3"
        tts_trim_cmd = ["ffmpeg", "-y", "-i", str(tts_src)]
        if trim_start > 0:
            tts_trim_cmd += ["-ss", str(trim_start)]
        if duration:
            tts_trim_cmd += ["-t", str(duration)]
        tts_trim_cmd += ["-acodec", "libmp3lame", "-q:a", "2", str(trimmed_tts)]
        subprocess.run(tts_trim_cmd, capture_output=True, text=True, timeout=60)
        tts_final = trimmed_tts if trimmed_tts.exists() else tts_src

        tts_duration = get_duration(tts_final)
        mixed_audio  = out_dir / "mixed_audio.mp3"

        music_path = MUSIC_DIR / music_filename if music_filename else None
        if music_path and music_path.exists():
            result = subprocess.run(
                ["ffmpeg", "-y",
                 "-ss", str(music_start),
                 "-stream_loop", "-1", "-i", str(music_path),
                 "-i", str(tts_final),
                 "-filter_complex",
                 f"[0:a]volume={music_volume}[bg];[bg][1:a]amix=inputs=2:duration=first:dropout_transition=2[out]",
                 "-map", "[out]",
                 "-t", str(tts_duration),
                 "-acodec", "libmp3lame", "-q:a", "2",
                 str(mixed_audio)],
                capture_output=True, text=True, timeout=120
            )
            final_audio = mixed_audio if result.returncode == 0 else tts_final
        else:
            final_audio = tts_final

        # ── STEP 4: Burn captions + combine ──────────────────────────────
        update_job(export_job_id, step="Se compilează videoclipul final...", progress=70)
        final_path = out_dir / "final.mp4"

        srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
        subtitle_filter = (
            f"subtitles='{srt_escaped}':"
            f"force_style='FontName=Arial,FontSize={caption_size},Bold=1,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            f"BackColour=&H80000000,Outline=2,Shadow=1,"
            f"Alignment=2,MarginV=30'"
        )

        result = subprocess.run(
            ["ffmpeg", "-y",
             "-stream_loop", "-1", "-i", str(trimmed_video),
             "-i", str(final_audio),
             "-filter_complex", f"[0:v]{subtitle_filter}[v]",
             "-map", "[v]", "-map", "1:a",
             "-c:v", "libx264", "-crf", "20", "-preset", "fast",
             "-c:a", "aac", "-b:a", "128k",
             "-t", str(tts_duration), "-shortest",
             str(final_path)],
            capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0:
            # Fallback without captions
            result = subprocess.run(
                ["ffmpeg", "-y",
                 "-stream_loop", "-1", "-i", str(trimmed_video),
                 "-i", str(final_audio),
                 "-c:v", "libx264", "-crf", "20", "-preset", "fast",
                 "-c:a", "aac", "-b:a", "128k",
                 "-t", str(tts_duration), "-shortest",
                 str(final_path)],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise Exception(f"Compilare finală eșuată: {result.stderr[:300]}")

        update_job(export_job_id,
                   step="Gata!", progress=100, status="done",
                   files={"final_video": final_path.name})

    except Exception as e:
        update_job(export_job_id, status="error", error=str(e), step="Eroare")


def _shift_srt(srt_text, offset_sec):
    """Shift all SRT timestamps by offset_sec (can be negative)."""
    import re
    def shift_ts(ts, off):
        h, m, s_ms = ts.split(':')
        s, ms = s_ms.split(',')
        total = int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000 + off
        total = max(0, total)
        hh = int(total // 3600)
        mm = int((total % 3600) // 60)
        ss = int(total % 60)
        ms2 = int(round((total - int(total)) * 1000))
        return f"{hh:02d}:{mm:02d}:{ss:02d},{ms2:03d}"
    def replace_ts(m):
        return f"{shift_ts(m.group(1), offset_sec)} --> {shift_ts(m.group(2), offset_sec)}"
    return re.sub(
        r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})',
        replace_ts, srt_text
    )


@app.route("/download/<job_id>/<filename>")
def download(job_id, filename):
    safe = all(c.isalnum() or c in "._-" for c in filename)
    if not safe or ".." in filename:
        return jsonify({"error": "Nume fișier invalid"}), 400
    file_path = DOWNLOAD_DIR / job_id / filename
    if not file_path.exists():
        return jsonify({"error": "Fișier negăsit"}), 404
    return send_file(str(file_path), as_attachment=True, download_name=filename)


if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("\n⚠️  GROQ_API_KEY lipsă!")
    else:
        print("\n✅  Groq API Key detectat.")
    if not CARTESIA_API_KEY:
        print("⚠️  CARTESIA_API_KEY lipsă!")
    else:
        print("✅  Cartesia API Key detectat.")
    port = int(os.environ.get("PORT", 5000))
    print(f"🎬  Pornire server la http://0.0.0.0:{port}\n")
    app.run(debug=False, host="0.0.0.0", port=port)
