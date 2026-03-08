# 🎵 FileFinder

**FileFinder** scans your hard drive for video and audio files that contain a specific song — just like Shazam, but for your local files.

It downloads the song from YouTube as a reference, creates an audio fingerprint, and compares it against every video/audio file in a folder you choose.

---

## ✨ Features

- 🔍 Detects songs inside video files (MP4, MOV, MKV, AVI and more)
- 🎵 Also scans audio files (MP3, WAV, FLAC, M4A and more)
- 📂 Simple GUI — pick a folder and paste a YouTube URL
- 📊 Shows a match percentage for every hit
- ⚙️ Adjustable sensitivity slider

---

## 📋 Requirements

- macOS (tested on Mac)
- Python 3.9+
- [Homebrew](https://brew.sh)

---

## 🚀 Installation

**1. Install system dependencies:**
```bash
brew install ffmpeg chromaprint python-tk
```

**2. Install Python dependencies:**
```bash
pip3 install yt-dlp
```

---

## ▶️ Usage

```bash
python3 song_finder.py
```

A window will open:

1. **Paste the YouTube URL** of the song you're looking for
2. **Select the folder** you want to scan (e.g. an external hard drive)
3. **Adjust the sensitivity** slider if needed
4. Click **"Suche starten"** and wait for results

Matches are shown in green with a percentage score.

> 💡 **Tip:** If you're not sure which version of the song was used, lower the sensitivity to ~0.10–0.15 to catch similar versions too.

---

## 🎬 Supported File Formats

| Video | Audio |
|-------|-------|
| .mp4, .mov, .avi, .mkv, .wmv | .mp3, .m4a, .aac, .wav |
| .flv, .m4v, .webm, .mpg | .flac, .ogg, .wma, .opus |
| .ts, .mts, .vob, .ogv, .rmvb | |

---

## 🛠 How It Works

1. Downloads the reference song from YouTube using `yt-dlp`
2. Generates an audio fingerprint using `Chromaprint` (`fpcalc`)
3. Extracts the audio track from each video file using `ffmpeg`
4. Compares fingerprints and reports files above the similarity threshold

---

## 📄 License

MIT License — free to use and modify.
