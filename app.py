import os
import uuid
import shutil
import subprocess
import requests
import threading
from flask import Flask, request, jsonify, send_file, send_from_directory
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
    print("✅ static-ffmpeg loaded")
except Exception as e:
    print(f"⚠️ static-ffmpeg error: {e}")

FFMPEG_BIN = shutil.which("ffmpeg") or "ffmpeg"
COOKIES_FILE = Path("cookies.txt")
print(f"🎬 ffmpeg: {FFMPEG_BIN}")
print(f"🍪 cookies: {'found' if COOKIES_FILE.exists() else 'NOT FOUND'}")

app = Flask(__name__, static_folder='static')

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

jobs = {}
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")

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

def run_pipeline(job_id, url):
    job_dir = DOWNLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    try:
        # ── STEP 1: Download ──────────────────────────────────────────────
        update_job(job_id, step="Se descarcă videoclipul...", progress=10)
        video_path = job_dir / "video.mp4"

        cmd = ["yt-dlp",
               "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
               "--merge-output-format", "mp4"]

        if COOKIES_FILE.exists():
            cmd += ["--cookies", str(COOKIES_FILE)]

        cmd += ["-o", str(video_path), url]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        if result.returncode != 0:
            # fallback fără format specific
            cmd2 = ["yt-dlp"]
            if COOKIES_FILE.exists():
                cmd2 += ["--cookies", str(COOKIES_FILE)]
            cmd2 += ["-f", "best", "-o", str(video_path), url]
            result = subprocess.run(cmd2, capture_output=True, text=True, timeout=180)

        if result.returncode != 0:
            raise Exception(f"Download eșuat: {result.stderr[:500]}")

        if not video_path.exists():
            all_videos = (list(job_dir.glob("*.mp4")) +
                          list(job_dir.glob("*.webm")) +
                          list(job_dir.glob("*.mkv")))
            if all_videos:
                video_path = all_videos[0]
            else:
                raise Exception("Niciun fișier video găsit după download.")

        # ── STEP 2: Extract audio ─────────────────────────────────────────
        update_job(job_id, step="Se extrage audio...", progress=25)
        audio_path = job_dir / "audio.mp3"

        result = subprocess.run(
            [FFMPEG_BIN, "-y", "-i", str(video_path),
             "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(audio_path)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise Exception(f"Extragere audio eșuată: {result.stderr[:300]}")

        # ── STEP 3: Remove vocals ─────────────────────────────────────────
        update_job(job_id, step="Se elimină vocile...", progress=40)
        no_vocals_path = job_dir / "no_vocals.mp4"

        result = subprocess.run(
            [FFMPEG_BIN, "-y", "-i", str(video_path),
             "-af", "pan=stereo|c0=c0-c1|c1=c1-c0",
             "-c:v", "copy", str(no_vocals_path)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            result = subprocess.run(
                [FFMPEG_BIN, "-y", "-i", str(video_path),
                 "-af", "pan=mono|c0=c0-c1",
                 "-c:v", "copy", str(no_vocals_path)],
                capture_output=True, text=True, timeout=120
            )
        if result.returncode != 0:
            raise Exception(f"Eliminare vocale eșuată: {result.stderr[:300]}")

        # ── STEP 4: Transcribe ────────────────────────────────────────────
        update_job(job_id, step="Se transcrie cu ElevenLabs...", progress=60)
        key = ELEVENLABS_API_KEY
        if not key:
            raise Exception("ELEVENLABS_API_KEY lipsă. Adaugă-l în Railway → Variables.")

        with open(audio_path, "rb") as f:
            audio_data = f.read()

        response = requests.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": key},
            files={"file": ("audio.mp3", audio_data, "audio/mpeg")},
            data={"model_id": "scribe_v1"},
            timeout=120
        )
        if response.status_code != 200:
            raise Exception(f"ElevenLabs eroare {response.status_code}: {response.text[:300]}")

        transcript_text = response.json().get("text", "")
        if not transcript_text:
            raise Exception("ElevenLabs a returnat o transcriere goală.")

        transcript_orig_path = job_dir / "transcript_original.txt"
        transcript_orig_path.write_text(transcript_text, encoding="utf-8")

        # ── STEP 5: Translate ─────────────────────────────────────────────
        update_job(job_id, step="Se traduce în română...", progress=80)
        romanian_text = translate_to_romanian(transcript_text)

        transcript_ro_path = job_dir / "transcript_romana.txt"
        transcript_ro_path.write_text(romanian_text, encoding="utf-8")

        # ── DONE ──────────────────────────────────────────────────────────
        update_job(
            job_id,
            step="Gata!",
            progress=100,
            status="done",
            files={
                "video_no_vocals": no_vocals_path.name,
                "transcript_original": transcript_orig_path.name,
                "transcript_romanian": transcript_ro_path.name,
            },
            preview={
                "original": transcript_text[:600],
                "romanian": romanian_text[:600],
            }
        )

    except Exception as e:
        update_job(job_id, status="error", error=str(e), step="Eroare")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Niciun URL furnizat"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "step": "Se pornește...", "progress": 0}
    threading.Thread(target=run_pipeline, args=(job_id, url), daemon=True).start()
    return jsonify({"job_id": job_id})

@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job negăsit"}), 404
    return jsonify(job)

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
    if not ELEVENLABS_API_KEY:
        print("\n⚠️ ELEVENLABS_API_KEY lipsă!")
    else:
        print("\n✅ ElevenLabs API Key detectat.")
    port = int(os.environ.get("PORT", 5000))
    print(f"🎬 Pornire server la http://0.0.0.0:{port}\n")
    app.run(debug=False, host="0.0.0.0", port=port)
