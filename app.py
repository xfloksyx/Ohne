import customtkinter as ctk
import subprocess
import threading
import os
import shutil
from pathlib import Path

# -----------------------------
# Processing Functions
# -----------------------------
DEMUCS_MODEL = "htdemucs"  # Pretrained Demucs model

def process_video(youtube_url, log_func):
    try:
        log_func("📥 Downloading video...")
        # Download video using yt-dlp
        subprocess.run(
            ["yt-dlp", "-f", "bestvideo+bestaudio", "-o", "video.%(ext)s", youtube_url],
            check=True
        )

        # Find downloaded video
        video_file = next(Path(".").glob("video.*"))
        log_func(f"✅ Video downloaded: {video_file.name}")

        # Extract audio as WAV
        audio_file = "audio.wav"
        log_func("🎵 Extracting audio...")
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_file),
            "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            audio_file
        ], check=True)
        log_func(f"✅ Audio extracted: {audio_file}")

        # Run Demucs for vocals only
        log_func("🎤 Isolating vocals with Demucs...")
        subprocess.run([
            "demucs", "--two-stems=vocals", "-n", DEMUCS_MODEL, audio_file
        ], check=True)

        # Locate the vocals file
        separated_dir = Path("separated") / DEMUCS_MODEL
        vocals_path = None
        for root, dirs, files in os.walk(separated_dir):
            if "vocals.wav" in files:
                vocals_path = os.path.join(root, "vocals.wav")
                break

        if not vocals_path or not os.path.exists(vocals_path):
            log_func("❌ Vocals file not found!")
            return

        # Merge vocals with video
        output_video = "final_video.mp4"
        log_func("🎬 Merging vocals with video...")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(video_file),
            "-i", vocals_path,
            "-c:v", "copy",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_video
        ], check=True)

        log_func(f"✅ Done! Saved as {output_video}")

        # Cleanup intermediate files
        os.remove(audio_file)
        shutil.rmtree(separated_dir, ignore_errors=True)

    except subprocess.CalledProcessError as e:
        log_func(f"❌ Command failed: {e}")
    except Exception as e:
        log_func(f"❌ Unexpected error: {e}")

# -----------------------------
# UI Functions
# -----------------------------
def start_processing():
    url = url_entry.get().strip()
    if not url:
        log("❌ Please enter a valid YouTube URL.")
        return
    threading.Thread(target=process_video, args=(url, log), daemon=True).start()


def log(message):
    log_textbox.insert("end", message + "\n")
    log_textbox.see("end")

# -----------------------------
# UI Setup
# -----------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("YouTube Vocal Extractor")
app.geometry("500x350")

frame = ctk.CTkFrame(app)
frame.pack(pady=20, padx=20, fill="both", expand=True)

label = ctk.CTkLabel(frame, text="Enter YouTube Link:")
label.pack(pady=10)

url_entry = ctk.CTkEntry(frame, width=400)
url_entry.pack(pady=5)

start_btn = ctk.CTkButton(frame, text="Download & Process", command=start_processing)
start_btn.pack(pady=10)

log_textbox = ctk.CTkTextbox(frame, width=450, height=200)
log_textbox.pack(pady=10)

app.mainloop()
