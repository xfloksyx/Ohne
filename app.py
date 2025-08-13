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

def process_video(youtube_url, final_title, action, log_func):
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

        # Decide action
        if action == "extract":
            output_audio = f"{final_title}_vocals.wav"
            shutil.copy(vocals_path, output_audio)
            log_func(f"✅ Vocals extracted: {output_audio}")
        elif action == "merge":
            output_video = f"{final_title}.mp4"
            log_func(f"🎬 Merging vocals into video as {output_video}...")
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
    final_title = title_entry.get().strip()
    action = action_var.get()
    if not url:
        log("❌ Please enter a valid YouTube URL.")
        return
    if not final_title:
        log("❌ Please enter a title for the output file.")
        return
    threading.Thread(target=process_video, args=(url, final_title, action, log), daemon=True).start()

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
app.geometry("600x450")

frame = ctk.CTkFrame(app)
frame.pack(pady=20, padx=20, fill="both", expand=True)

ctk.CTkLabel(frame, text="Enter YouTube Link:").pack(pady=5)
url_entry = ctk.CTkEntry(frame, width=500)
url_entry.pack(pady=5)

ctk.CTkLabel(frame, text="Enter output title:").pack(pady=5)
title_entry = ctk.CTkEntry(frame, width=500)
title_entry.pack(pady=5)

# Action selection
action_var = ctk.StringVar(value="merge")
ctk.CTkLabel(frame, text="Select action:").pack(pady=5)
ctk.CTkRadioButton(frame, text="Extract Vocals Only", variable=action_var, value="extract").pack()
ctk.CTkRadioButton(frame, text="Merge Vocals with Video", variable=action_var, value="merge").pack()

ctk.CTkButton(frame, text="Start Processing", command=start_processing).pack(pady=10)

log_textbox = ctk.CTkTextbox(frame, width=550, height=250)
log_textbox.pack(pady=10)

app.mainloop()
