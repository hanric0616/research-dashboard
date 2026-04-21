import re
import json
import os
import subprocess
import tempfile
import streamlit as st
from config import YT_CHANNEL


@st.cache_data(ttl=3600)
def fetch_youtube_transcript() -> tuple[str, str]:
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--playlist-end", "1", "-J", YT_CHANNEL],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout)
        entry = data["entries"][0]
        video_id = entry["id"]
        title = entry.get("title", "")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "sub")
            subprocess.run(
                [
                    "yt-dlp", "--write-auto-sub", "--sub-lang", "zh-TW",
                    "--skip-download", "--sub-format", "vtt",
                    "-o", out_path,
                    f"https://www.youtube.com/watch?v={video_id}",
                ],
                capture_output=True, timeout=60,
            )
            vtt_files = [f for f in os.listdir(tmpdir) if f.endswith(".vtt")]
            if not vtt_files:
                return title, "(無字幕)"
            with open(os.path.join(tmpdir, vtt_files[0]), encoding="utf-8") as f:
                vtt_content = f.read()

        content = []
        for line in vtt_content.split("\n"):
            line = line.strip()
            if (not line or line.startswith("WEBVTT") or line.startswith("Language:")
                    or re.match(r"^\d{2}:\d{2}", line)
                    or line.startswith("align:") or line.startswith("Kind:")):
                continue
            line = re.sub(r"<[^>]+>", "", line)
            if line:
                content.append(line)

        deduped, prev = [], None
        for c in content:
            if c != prev:
                deduped.append(c)
                prev = c

        return title, "\n".join(deduped)[:3000]

    except Exception as e:
        return "無法取得 YouTube 資料", str(e)
