import os
import uuid
import subprocess
import requests
import threading
import json
from flask import Flask, request, jsonify, send_file, send_from_directory, session, redirect
from pathlib import Path

env_path = Path(".env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    print("static-ffmpeg loaded")
except Exception as e:
    print(f"static-ffmpeg error: {e}")

app = Flask(__name__, static_folder='static')
app.secret_key = "xK9#mP2$vL7nQ4wR"

PASSWORD = "9357"
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
MUSIC_DIR = Path("music")
MUSIC_DIR.mkdir(exist_ok=True)

jobs = {}

GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
CARTESIA_API_KEY  = os.environ.get("CARTESIA_API_KEY", "")
CARTESIA_VOICE_ID = os.environ.get("CARTESIA_VOICE_ID", "e1def6dd-c945-4630-bb41-d29c79e1e489")


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
        raise Exception("CARTESIA_API_KEY lipsa.")
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
                "voice": {"mode": "id", "id": CARTESIA_VOICE_ID},
                "output_format": {"container": "mp3", "encoding": "mp3", "sample_rate": 44100},
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
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=30
    )
    try:
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def text_to_srt(text, audio_duration, output_path, words_per_line=6):
    words = text.split()
    if not words:
        return
    lines = []
    for i in range(0, len(words), words_per_line):
        lines.append(" ".join(words[i:i + words_per_line]))
    time_per_line = audio_duration / len(lines) if lines else 1.0

    def fmt(s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = int(s % 60)
        ms = int((s - int(s)) * 1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    srt = ""
    for i, line in enumerate(lines):
        srt += f"{i+1}\n{fmt(i*time_per_line)} --> {fmt((i+1)*time_per_line)}\n{line}\n\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt)


def run_pipeline(job_id, url, music_filename=None, bg_volume=0.08):
    job_dir = DOWNLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    try:
        # Step 1: Download
        update_job(job_id, step="Se descarca videoclipul...", progress=10)
        video_path = job_dir / "video.mp4"
        attempts = [
            ["yt-dlp", "--js-runtimes", "deno", "--extractor-args", "youtube:player_client=ios",
             "-f", "b[ext=mp4]/b", "-o", str(video_path), url],
            ["yt-dlp", "--js-runtimes", "deno", "--extractor-args", "youtube:player_client=android",
             "-f", "b[ext=mp4]/b", "-o", str(video_path), url],
            ["yt-dlp", "--js-runtimes", "deno", "-f", "b[ext=mp4]/b", "-o", str(video_path), url],
        ]
        last_err = ""
        for attempt in attempts:
            r = subprocess.run(attempt, capture_output=True, text=True, timeout=180)
            if r.returncode == 0:
                break
            last_err = r.stderr[:500]
        else:
            raise Exception(f"Download esuat: {last_err}")
        if not video_path.exists():
            all_v = list(job_dir.glob("*.mp4")) + list(job_dir.glob("*.webm")) + list(job_dir.glob("*.mkv"))
            if all_v:
                video_path = all_v[0]
            else:
                raise Exception("Niciun fisier video gasit.")

        # Step 2: Mute
        update_job(job_id, step="Se pune video pe mut...", progress=22)
        muted_path = job_dir / "video_muted.mp4"
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path), "-an", "-c:v", "copy", str(muted_path)],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode != 0:
            raise Exception(f"Mute esuat: {r.stderr[:300]}")

        # Step 3: Extract audio for transcription
        update_job(job_id, step="Se extrage audio...", progress=30)
        audio_path = job_dir / "audio.mp3"
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(audio_path)],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode != 0:
            raise Exception(f"Extragere audio esuata: {r.stderr[:300]}")

        # Step 4: Transcribe
        update_job(job_id, step="Se transcrie cu Groq Whisper...", progress=42)
        key = GROQ_API_KEY
        if not key:
            raise Exception("GROQ_API_KEY lipsa.")
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
            raise Exception("Groq a returnat o transcriere goala.")
        (job_dir / "transcript_original.txt").write_text(transcript_text, encoding="utf-8")

        # Step 5: Translate
        update_job(job_id, step="Se traduce in romana...", progress=55)
        romanian_text = translate_to_romanian(transcript_text)
        (job_dir / "transcript_romana.txt").write_text(romanian_text, encoding="utf-8")

        # Pause — wait for editor
        update_job(job_id,
                   step="Asteptam editorul...", progress=60,
                   status="awaiting_confirmation",
                   preview={"original": transcript_text[:800], "romanian": romanian_text[:800]},
                   romanian_text=romanian_text,
                   music_filename=music_filename,
                   bg_volume=bg_volume)

    except Exception as e:
        update_job(job_id, status="error", error=str(e), step="Eroare")


def run_export(job_id, tts_text, settings):
    """
    settings = {
      music_filename, bg_volume,
      tts_speed,           # float 0.5-2.0
      trim_start, trim_end,  # seconds
      cap_fontsize, cap_color, cap_outline_color, cap_position,
      cap_bg, cap_bold, words_per_line
    }
    """
    job_dir = DOWNLOAD_DIR / job_id
    try:
        update_job(job_id, status="exporting", step="Se genereaza TTS...", export_progress=10)

        # TTS
        tts_path = job_dir / "voce_romana.mp3"
        generate_tts_cartesia(tts_text, tts_path)
        tts_dur = get_duration(tts_path)

        # Speed adjustment
        tts_speed = float(settings.get("tts_speed", 1.0))
        if abs(tts_speed - 1.0) > 0.05:
            update_job(job_id, step="Se ajusteaza viteza TTS...", export_progress=22)
            sped_path = job_dir / "voce_sped.mp3"
            atempo = tts_speed
            # ffmpeg atempo filter only supports 0.5-2.0; chain if needed
            if atempo < 0.5:
                atempo_filter = f"atempo=0.5,atempo={tts_speed/0.5:.4f}"
            elif atempo > 2.0:
                atempo_filter = f"atempo=2.0,atempo={tts_speed/2.0:.4f}"
            else:
                atempo_filter = f"atempo={atempo:.4f}"
            r = subprocess.run(
                ["ffmpeg", "-y", "-i", str(tts_path), "-filter:a", atempo_filter, str(sped_path)],
                capture_output=True, text=True, timeout=60
            )
            if r.returncode == 0:
                tts_path = sped_path
                tts_dur = get_duration(tts_path)

        update_job(job_id, step="Se genereaza captionurile...", export_progress=32)
        srt_path = job_dir / "captions.srt"
        words_per_line = int(settings.get("words_per_line", 6))
        text_to_srt(tts_text, tts_dur, srt_path, words_per_line)

        # Mix audio
        update_job(job_id, step="Se mixeaza audio...", export_progress=44)
        music_filename = settings.get("music_filename")
        bg_volume = float(settings.get("bg_volume", 0.08))
        music_path = MUSIC_DIR / music_filename if music_filename else None
        mixed_audio = job_dir / "mixed_audio.aac"

        if music_path and music_path.exists():
            r = subprocess.run(
                ["ffmpeg", "-y",
                 "-stream_loop", "-1", "-i", str(music_path),
                 "-i", str(tts_path),
                 "-filter_complex",
                 f"[0:a]volume={bg_volume}[bg];[bg][1:a]amix=inputs=2:duration=first:dropout_transition=2[out]",
                 "-map", "[out]", "-t", str(tts_dur),
                 "-acodec", "aac", "-b:a", "128k", str(mixed_audio)],
                capture_output=True, text=True, timeout=120
            )
            if r.returncode != 0:
                mixed_audio = tts_path
        else:
            mixed_audio = tts_path

        # Trim + captions + combine
        update_job(job_id, step="Se compileaza videoclipul final...", export_progress=65)
        muted_path = job_dir / "video_muted.mp4"
        final_path = job_dir / "final.mp4"

        trim_start = float(settings.get("trim_start", 0))
        trim_end = float(settings.get("trim_end", 0))
        video_dur = get_duration(muted_path)
        effective_end = trim_end if trim_end > trim_start else video_dur

        # Caption style
        fontsize   = int(settings.get("cap_fontsize", 18))
        color      = settings.get("cap_color", "&H00FFFFFF")       # ABGR hex for ffmpeg
        outline_c  = settings.get("cap_outline_color", "&H00000000")
        position   = int(settings.get("cap_position", 2))           # 1=top 2=bottom 5=middle
        bold       = 1 if settings.get("cap_bold", True) else 0
        cap_bg     = settings.get("cap_bg", "&H80000000")

        srt_esc = str(srt_path).replace("\\", "/")
        force_style = (
            f"FontName=Arial,FontSize={fontsize},Bold={bold},"
            f"PrimaryColour={color},OutlineColour={outline_c},"
            f"BackColour={cap_bg},Outline=2,Shadow=1,"
            f"Alignment={position},MarginV=30"
        )
        subtitle_filter = f"subtitles='{srt_esc}':force_style='{force_style}'"

        r = subprocess.run(
            ["ffmpeg", "-y",
             "-ss", str(trim_start),
             "-stream_loop", "-1", "-i", str(muted_path),
             "-i", str(mixed_audio),
             "-filter_complex", f"[0:v]{subtitle_filter}[v]",
             "-map", "[v]", "-map", "1:a",
             "-c:v", "libx264", "-crf", "20", "-preset", "fast",
             "-c:a", "aac", "-b:a", "128k",
             "-t", str(tts_dur),
             "-shortest", str(final_path)],
            capture_output=True, text=True, timeout=300
        )
        if r.returncode != 0:
            # fallback without captions
            r2 = subprocess.run(
                ["ffmpeg", "-y",
                 "-ss", str(trim_start),
                 "-stream_loop", "-1", "-i", str(muted_path),
                 "-i", str(mixed_audio),
                 "-c:v", "libx264", "-crf", "20", "-preset", "fast",
                 "-c:a", "aac", "-b:a", "128k",
                 "-t", str(tts_dur), "-shortest", str(final_path)],
                capture_output=True, text=True, timeout=300
            )
            if r2.returncode != 0:
                raise Exception(f"Export esuat: {r2.stderr[:400]}")

        update_job(job_id, status="done", step="Gata!", export_progress=100,
                   files={"final_video": final_path.name})

    except Exception as e:
        update_job(job_id, status="error", error=str(e), step="Eroare export")


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
        return jsonify({"error": "Niciun fisier primit"}), 400
    safe_name = "".join(c for c in f.filename if c.isalnum() or c in "._- ").strip() or "music.mp3"
    f.save(str(MUSIC_DIR / safe_name))
    return jsonify({"filename": safe_name})


@app.route("/list-music")
def list_music():
    return jsonify({"files": [p.name for p in MUSIC_DIR.iterdir() if p.is_file()]})


@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Niciun URL furnizat"}), 400
    music_filename = data.get("music_filename") or None
    bg_volume = float(data.get("bg_volume", 0.08))
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "step": "Se porneste...", "progress": 0,
                    "music_filename": music_filename, "bg_volume": bg_volume}
    threading.Thread(target=run_pipeline, args=(job_id, url, music_filename, bg_volume), daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/export", methods=["POST"])
def export():
    data = request.get_json()
    job_id = data.get("job_id", "")
    tts_text = data.get("tts_text", "").strip()
    settings = data.get("settings", {})
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job negasit"}), 404
    if job.get("status") not in ("awaiting_confirmation", "done", "error"):
        return jsonify({"error": "Job-ul nu e gata pentru export"}), 400
    update_job(job_id, status="exporting", step="Se porneste exportul...", export_progress=0)
    threading.Thread(target=run_export, args=(job_id, tts_text, settings), daemon=True).start()
    return jsonify({"ok": True})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job negasit"}), 404
    return jsonify(job)


@app.route("/stream/<job_id>/<filename>")
def stream_file(job_id, filename):
    safe = all(c.isalnum() or c in "._-" for c in filename)
    if not safe or ".." in filename:
        return jsonify({"error": "Invalid"}), 400
    file_path = DOWNLOAD_DIR / job_id / filename
    if not file_path.exists():
        return jsonify({"error": "Fisier negasit"}), 404
    return send_file(str(file_path))


@app.route("/download/<job_id>/<filename>")
def download(job_id, filename):
    safe = all(c.isalnum() or c in "._-" for c in filename)
    if not safe or ".." in filename:
        return jsonify({"error": "Invalid"}), 400
    file_path = DOWNLOAD_DIR / job_id / filename
    if not file_path.exists():
        return jsonify({"error": "Fisier negasit"}), 404
    return send_file(str(file_path), as_attachment=True, download_name=filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Pornire server la http://0.0.0.0:{port}")
    app.run(debug=False, host="0.0.0.0", port=port)
