#!/usr/bin/env python3
"""
🎵 Song Finder – durchsucht deine Festplatte nach Videos mit einem bestimmten Song.
Funktioniert wie Shazam: Audio-Fingerabdruck-Vergleich via Chromaprint.

Voraussetzungen (einmalig installieren):
  brew install ffmpeg chromaprint
  pip3 install yt-dlp
"""

import os
import sys
import subprocess
import tempfile
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv",
    ".m4v", ".webm", ".mpg", ".mpeg", ".3gp", ".ts",
    ".mts", ".m2ts", ".vob", ".ogv", ".rmvb",
    ".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".wma", ".opus"
}

def check_dependencies():
    missing = []
    for tool in ["ffmpeg", "fpcalc"]:
        if not shutil.which(tool):
            missing.append(tool)
    if missing:
        messagebox.showerror(
            "Fehlende Tools",
            f"Bitte installieren:\n  brew install ffmpeg chromaprint\n\nFehlend: {', '.join(missing)}"
        )
        sys.exit(1)
    if not shutil.which("yt-dlp"):
        messagebox.showerror(
            "Fehlendes Tool",
            "yt-dlp nicht gefunden.\nBitte installieren:\n  pip3 install yt-dlp"
        )
        sys.exit(1)

def download_reference(youtube_url: str, out_dir: str) -> str:
    out_path = os.path.join(out_dir, "reference.wav")
    cmd = [
        "yt-dlp", youtube_url,
        "--extract-audio", "--audio-format", "wav", "--audio-quality", "0",
        "-o", out_path, "--no-playlist", "--quiet", "--no-warnings",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    for candidate in [out_path, out_path + ".wav", out_path.replace(".wav", ".wav.wav")]:
        if os.path.exists(candidate):
            if candidate != out_path:
                os.rename(candidate, out_path)
            return out_path
    raise RuntimeError(f"Download fehlgeschlagen:\n{result.stderr}")

def get_fingerprint(audio_path: str):
    result = subprocess.run(
        ["fpcalc", "-raw", "-length", "120", audio_path],
        capture_output=True, text=True
    )
    fingerprint, duration = "", 0
    for line in result.stdout.splitlines():
        if line.startswith("FINGERPRINT="):
            fingerprint = line.split("=", 1)[1].strip()
        elif line.startswith("DURATION="):
            duration = int(float(line.split("=", 1)[1].strip()))
    return fingerprint, duration

def fingerprint_similarity(fp1: str, fp2: str) -> float:
    if not fp1 or not fp2:
        return 0.0
    try:
        nums1 = list(map(int, fp1.split(",")))
        nums2 = list(map(int, fp2.split(",")))
        min_len = min(len(nums1), len(nums2))
        if min_len == 0:
            return 0.0
        matches = sum(1 for a, b in zip(nums1[:min_len], nums2[:min_len]) if a == b)
        return matches / min_len
    except Exception:
        return 0.0

def extract_audio_from_video(video_path: str, out_wav: str) -> bool:
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ac", "1", "-ar", "11025", "-t", "180",
        "-f", "wav", out_wav, "-loglevel", "error"
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0 and os.path.exists(out_wav)

def find_video_files(search_dir: str):
    found = []
    for root, dirs, files in os.walk(search_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if Path(f).suffix.lower() in VIDEO_EXTENSIONS:
                found.append(os.path.join(root, f))
    return found


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎵 Song Finder")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e", padx=24, pady=24)

        # ── YouTube URL ──
        tk.Label(self, text="YouTube URL des gesuchten Songs:",
                 bg="#1e1e2e", fg="#cdd6f4", font=("Helvetica", 13)).grid(row=0, column=0, sticky="w")

        self.url_var = tk.StringVar()
        url_entry = tk.Entry(self, textvariable=self.url_var, width=60,
                             font=("Helvetica", 12), bg="#313244", fg="#cdd6f4",
                             insertbackground="#cdd6f4", relief="flat", bd=6)
        url_entry.grid(row=1, column=0, sticky="ew", pady=(4, 16))

        # ── Ordner-Auswahl ──
        tk.Label(self, text="Ordner / Festplatte durchsuchen:",
                 bg="#1e1e2e", fg="#cdd6f4", font=("Helvetica", 13)).grid(row=2, column=0, sticky="w")

        dir_frame = tk.Frame(self, bg="#1e1e2e")
        dir_frame.grid(row=3, column=0, sticky="ew", pady=(4, 16))

        self.dir_var = tk.StringVar(value=str(Path.home()))
        dir_entry = tk.Entry(dir_frame, textvariable=self.dir_var, width=46,
                             font=("Helvetica", 12), bg="#313244", fg="#cdd6f4",
                             insertbackground="#cdd6f4", relief="flat", bd=6)
        dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(dir_frame, text="📂 Auswählen", command=self.browse_dir,
                  bg="#89b4fa", fg="#1e1e2e", font=("Helvetica", 11, "bold"),
                  relief="flat", padx=10, cursor="hand2").pack(side="left")

        # ── Schwellwert ──
        thresh_frame = tk.Frame(self, bg="#1e1e2e")
        thresh_frame.grid(row=4, column=0, sticky="ew", pady=(0, 16))

        tk.Label(thresh_frame, text="Empfindlichkeit:",
                 bg="#1e1e2e", fg="#a6adc8", font=("Helvetica", 11)).pack(side="left")
        self.thresh_var = tk.DoubleVar(value=0.25)
        tk.Scale(thresh_frame, variable=self.thresh_var, from_=0.05, to=0.60,
                 resolution=0.05, orient="horizontal", bg="#1e1e2e", fg="#cdd6f4",
                 troughcolor="#313244", highlightthickness=0, length=200).pack(side="left", padx=8)
        tk.Label(thresh_frame, text="(niedriger = mehr Treffer)",
                 bg="#1e1e2e", fg="#585b70", font=("Helvetica", 10)).pack(side="left")

        # ── Start ──
        self.start_btn = tk.Button(self, text="🔍  Suche starten", command=self.start_scan,
                                   bg="#a6e3a1", fg="#1e1e2e", font=("Helvetica", 13, "bold"),
                                   relief="flat", padx=16, pady=8, cursor="hand2")
        self.start_btn.grid(row=5, column=0, pady=(0, 16))

        # ── Fortschritt ──
        self.progress_label = tk.Label(self, text="", bg="#1e1e2e", fg="#a6adc8",
                                       font=("Helvetica", 11))
        self.progress_label.grid(row=6, column=0, sticky="w")
        self.progress = ttk.Progressbar(self, length=560, mode="determinate")
        self.progress.grid(row=7, column=0, sticky="ew", pady=(4, 12))

        # ── Ergebnisse ──
        tk.Label(self, text="Ergebnisse:", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Helvetica", 12)).grid(row=8, column=0, sticky="w")

        result_frame = tk.Frame(self, bg="#1e1e2e")
        result_frame.grid(row=9, column=0, sticky="ew", pady=(4, 0))
        scrollbar = tk.Scrollbar(result_frame)
        scrollbar.pack(side="right", fill="y")
        self.result_box = tk.Text(result_frame, height=12, width=72,
                                  font=("Courier", 11), bg="#181825", fg="#cdd6f4",
                                  relief="flat", bd=6, yscrollcommand=scrollbar.set,
                                  state="disabled")
        self.result_box.pack(side="left")
        scrollbar.config(command=self.result_box.yview)
        self.result_box.tag_config("match", foreground="#a6e3a1")
        self.result_box.tag_config("info",  foreground="#89b4fa")
        self.result_box.tag_config("warn",  foreground="#f9e2af")
        self.result_box.tag_config("error", foreground="#f38ba8")

    def browse_dir(self):
        path = filedialog.askdirectory(initialdir=self.dir_var.get(), title="Ordner auswählen")
        if path:
            self.dir_var.set(path)

    def log(self, text, tag=""):
        self.result_box.config(state="normal")
        self.result_box.insert("end", text + "\n", tag)
        self.result_box.see("end")
        self.result_box.config(state="disabled")

    def start_scan(self):
        url = self.url_var.get().strip()
        directory = self.dir_var.get().strip()
        if not url:
            messagebox.showwarning("Eingabe fehlt", "Bitte eine YouTube-URL eingeben.")
            return
        if not os.path.isdir(directory):
            messagebox.showwarning("Ungültiger Pfad", "Bitte einen gültigen Ordner auswählen.")
            return
        self.start_btn.config(state="disabled")
        self.result_box.config(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.config(state="disabled")
        self.progress["value"] = 0
        threading.Thread(target=self.run_scan, args=(url, directory), daemon=True).start()

    def run_scan(self, youtube_url: str, search_dir: str):
        threshold = self.thresh_var.get()
        try:
            check_dependencies()
            with tempfile.TemporaryDirectory() as tmp:
                self.progress_label.config(text="⬇️  Lade Song von YouTube...")
                self.log("⬇️  Lade Referenz-Song von YouTube...", "info")
                try:
                    ref_wav = download_reference(youtube_url, tmp)
                except RuntimeError as e:
                    self.log(f"Fehler: {e}", "error")
                    return

                ref_fp, ref_dur = get_fingerprint(ref_wav)
                if not ref_fp:
                    self.log("Konnte keinen Fingerabdruck erstellen. Ist 'fpcalc' installiert?", "error")
                    return
                self.log(f"✔ Referenz geladen ({ref_dur}s)\n", "info")

                self.progress_label.config(text="📂 Suche Dateien...")
                files = find_video_files(search_dir)
                total = len(files)
                self.log(f"📂 {total} Dateien gefunden in:\n   {search_dir}\n", "info")
                if total == 0:
                    self.log("Keine Dateien gefunden.", "warn")
                    return

                self.progress["maximum"] = total
                matches = []
                tmp_wav = os.path.join(tmp, "current.wav")

                for i, fpath in enumerate(files, 1):
                    name = os.path.basename(fpath)
                    self.progress_label.config(text=f"[{i}/{total}] {name[:55]}")
                    self.progress["value"] = i

                    if not extract_audio_from_video(fpath, tmp_wav):
                        continue
                    fp, _ = get_fingerprint(tmp_wav)
                    score = fingerprint_similarity(ref_fp, fp)
                    if score >= threshold:
                        matches.append((score, fpath))
                        self.log(f"🎯 {score*100:.1f}%  {fpath}", "match")
                    try:
                        os.remove(tmp_wav)
                    except Exception:
                        pass

                self.log("\n" + "─" * 60)
                if matches:
                    self.log(f"✅ {len(matches)} Treffer gefunden!", "match")
                else:
                    self.log("Keine Treffer gefunden.", "warn")
                    self.log(f"Tipp: Empfindlichkeit erhöhen (aktuell: {threshold:.2f})", "warn")
                self.progress_label.config(text="✅ Fertig!")
        except Exception as e:
            self.log(f"Fehler: {e}", "error")
        finally:
            self.start_btn.config(state="normal")


if __name__ == "__main__":
    app = App()
    app.mainloop()
