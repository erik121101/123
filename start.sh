#!/usr/bin/env bash
# ─────────────────────────────────────────────────
#  YouTube Shorts Processor - Start Script
# ─────────────────────────────────────────────────

echo ""
echo "🎬  YouTube Shorts Processor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌  Python3 not found. Please install Python 3.8+"
  exit 1
fi

# Check ffmpeg
if ! command -v ffmpeg &>/dev/null; then
  echo "❌  ffmpeg not found."
  echo "    Install: brew install ffmpeg  OR  sudo apt install ffmpeg"
  exit 1
fi

# Install yt-dlp if missing
if ! command -v yt-dlp &>/dev/null; then
  echo "📦  Installing yt-dlp..."
  pip3 install yt-dlp --break-system-packages -q || pip3 install yt-dlp -q
fi

# Install Python deps
echo "📦  Checking Python packages..."
pip3 install flask requests --break-system-packages -q 2>/dev/null || pip3 install flask requests -q

echo ""
echo "✅  All good! Starting server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Open in browser: http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

python3 app.py
