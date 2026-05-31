import os
import uuid
import subprocess
import requests
import threading
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



def remove_captions_ocr(input_path, output_path):
    """Detectează text cu OCR și aplică blur doar pe zonele cu captions."""
    try:
        import cv2
        import pytesseract
        from PIL import Image
        import numpy as np
    except ImportError:
        raise Exception("pytesseract/opencv nu sunt instalate")

    cap = cv2.VideoCapture(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Scanăm 1 frame pe secundă pentru a găsi zona cu text
    text_boxes = []
    frame_idx = 0
    sample_every = max(1, int(fps))  # 1 frame/secundă

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_every == 0:
            # Convertim la PIL pentru pytesseract
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            try:
                data = pytesseract.image_to_data(
                    pil_img, output_type=pytesseract.Output.DICT,
                    config='--psm 6'
                )
                for i, text in enumerate(data['text']):
                    if text.strip() and int(data['conf'][i]) > 40:
                        x, y = data['left'][i], data['top'][i]
                        w, h = data['width'][i], data['height'][i]
                        # Păstrăm doar textul din jumătatea de jos
                        if y > height * 0.5:
                            text_boxes.append((x, y, x+w, y+h))
            except Exception:
                pass
        frame_idx += 1

    cap.release()

    if not text_boxes:
        # Nu s-a găsit text — returnăm input-ul nemodificat
        return input_path

    # Calculăm bounding box-ul combinat al tuturor textelor găsite
    x1 = max(0, min(b[0] for b in text_boxes) - 10)
    y1 = max(0, min(b[1] for b in text_boxes) - 10)
    x2 = min(width, max(b[2] for b in text_boxes) + 10)
    y2 = min(height, max(b[3] for b in text_boxes) + 10)

    # Blur FFmpeg pe zona detectată
    bw = x2 - x1
    bh = y2 - y1
    blur_filter = (
        f"[0:v]split[bg][fg];"
        f"[fg]crop={bw}:{bh}:{x1}:{y1},boxblur=15:3[blurred];"
        f"[bg][blurred]overlay={x1}:{y1}[out]"
    )

    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path),
         "-filter_complex", blur_filter,
         "-map", "[out]", "-map", "0:a?",
         "-c:v", "libx264", "-crf", "18", "-preset", "fast",
         "-c:a", "copy", str(output_path)],
        capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
        raise Exception(f"FFmpeg blur eșuat: {result.stderr[:200]}")

    return output_path


def run_pipeline(job_id, url):
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

        # ── STEP 2: Extract audio ─────────────────────────────────────────
        update_job(job_id, step="Se extrage audio...", progress=20)
        audio_path = job_dir / "audio.mp3"

        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path),
             "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(audio_path)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise Exception(f"Extragere audio eșuată: {result.stderr[:300]}")

        # ── STEP 3: Remove vocals ─────────────────────────────────────────
        update_job(job_id, step="Se elimină vocile...", progress=35)
        no_vocals_path = job_dir / "no_vocals.mp4"

        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path),
             "-af", "pan=stereo|c0=c0-c1|c1=c1-c0",
             "-c:v", "copy", str(no_vocals_path)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", str(video_path),
                 "-af", "pan=mono|c0=c0-c1",
                 "-c:v", "copy", str(no_vocals_path)],
                capture_output=True, text=True, timeout=120
            )
        if result.returncode != 0:
            raise Exception(f"Eliminare vocale eșuată: {result.stderr[:300]}")

        # ── STEP 3b: Caption removal cu OCR ──────────────────────────────
        update_job(job_id, step="Se detectează și elimină captionurile...", progress=42)
        final_video_path = job_dir / "final.mp4"
        try:
            no_vocals_path = remove_captions_ocr(no_vocals_path, final_video_path)
        except Exception as ce:
            print(f"Caption removal eșuat (continuăm fără): {ce}")

        # ── STEP 4: Transcribe cu Groq Whisper ───────────────────────────
        update_job(job_id, step="Se transcrie cu Groq Whisper...", progress=55)

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
        update_job(job_id, step="Se traduce în română...", progress=70)
        romanian_text = translate_to_romanian(transcript_text)

        transcript_ro_path = job_dir / "transcript_romana.txt"
        transcript_ro_path.write_text(romanian_text, encoding="utf-8")

        # ── STEP 6: TTS cu Cartesia ───────────────────────────────────────
        update_job(job_id, step="Se generează vocea în română (Cartesia)...", progress=85)
        tts_path = job_dir / "voce_romana.mp3"
        generate_tts_cartesia(romanian_text, tts_path)

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
                "tts_romanian": tts_path.name,
            },
            preview={
                "original": transcript_text[:600],
                "romanian": romanian_text[:600],
            }
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
    error = ""
    if request.method == "POST":
        if request.form.get("parola", "") == PASSWORD:
            session['authenticated'] = True
            return redirect('/')
        error = "Parolă greșită. Încearcă din nou."

    return f"""<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Autentificare</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0f0f1a;
            display: flex; justify-content: center; align-items: center;
            min-height: 100vh;
        }}
        .card {{
            background: #1a1a2e;
            border: 1px solid #2a2a4a;
            border-radius: 16px;
            padding: 48px 40px;
            width: 100%;
            max-width: 380px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }}
        h1 {{ color: #fff; font-size: 1.5rem; margin-bottom: 8px; text-align: center; }}
        p.sub {{ color: #888; font-size: 0.9rem; text-align: center; margin-bottom: 32px; }}
        label {{ color: #aaa; font-size: 0.85rem; display: block; margin-bottom: 8px; }}
        input[type=password] {{
            width: 100%; padding: 12px 16px;
            background: #0f0f1a; border: 1px solid #333;
            border-radius: 8px; color: #fff;
            font-size: 1.1rem; letter-spacing: 4px;
            outline: none; transition: border 0.2s;
        }}
        input[type=password]:focus {{ border-color: #6c63ff; }}
        button {{
            width: 100%; margin-top: 20px; padding: 13px;
            background: #6c63ff; color: #fff; border: none;
            border-radius: 8px; font-size: 1rem; font-weight: 600;
            cursor: pointer; transition: background 0.2s;
        }}
        button:hover {{ background: #574fd6; }}
        .error {{ margin-top: 16px; color: #ff6b6b; font-size: 0.9rem; text-align: center; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🔒 Acces restricționat</h1>
        <p class="sub">Introduceți parola pentru a continua</p>
        <form method="POST">
            <label>Parolă</label>
            <input type="password" name="parola" autofocus placeholder="••••">
            <button type="submit">Intră</button>
        </form>
        {'<div class="error">⚠ ' + error + '</div>' if error else ''}
    </div>
</body>
</html>"""


# ── Routes ────────────────────────────────────────────────────────────────────

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
