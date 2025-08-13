import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import shutil
from pathlib import Path
from PIL import Image, ImageTk
import re
import sys

# -----------------------------
# Processing Functions
# -----------------------------
DEMUCS_MODEL = "htdemucs"

def process_video(youtube_url, local_video_path, final_title, action, log_func, progress_func):
    try:
        progress_func(0, "Initializing...")
        
        if local_video_path:
            video_file = Path(local_video_path)
            log_func(f"Using local video: {video_file.name}")
            progress_func(10, "Using local video file")
        else:
            log_func("Downloading video...")
            progress_func(10, "Downloading video...")
            
            # Download with progress tracking
            process = subprocess.Popen(
                ["yt-dlp", "-f", "bestvideo+bestaudio", "-o", "video.%(ext)s", youtube_url],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            
            for line in process.stdout:
                # Only show download progress, not all verbose output
                if "[download]" in line and "%" in line:
                    log_func(line.strip())
                    match = re.search(r'(\d+(?:\.\d+)?)%', line)
                    if match:
                        percent = float(match.group(1))
                        progress_func(10 + (percent * 0.2), f"Downloading: {percent:.1f}%")
                        
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "yt-dlp")
                
            video_file = next(Path(".").glob("video.*"))
            log_func(f"Video downloaded: {video_file.name}")
            progress_func(30, "Video download complete")

        audio_file = "audio.wav"
        log_func("Extracting audio...")
        progress_func(35, "Extracting audio...")
        
        # Extract audio with minimal logging
        process = subprocess.Popen([
            "ffmpeg", "-y", "-i", str(video_file),
            "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            audio_file
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        for line in process.stdout:
            if "time=" in line:
                # Parse ffmpeg progress
                time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                if time_match:
                    hours, minutes, seconds = time_match.groups()
                    current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    progress_func(35 + min(15, current_time / 10), f"Extracting audio: {int(hours):02d}:{int(minutes):02d}:{int(float(seconds)):02d}")
                    
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, "ffmpeg")
            
        log_func(f"Audio extracted: {audio_file}")
        progress_func(50, "Audio extraction complete")

        log_func("Isolating vocals with Demucs...")
        progress_func(55, "Starting vocal separation...")
        
        # Demucs with filtered progress output
        process = subprocess.Popen([
            "demucs", "--two-stems=vocals", "-n", DEMUCS_MODEL, audio_file
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        for line in process.stdout:
            if "Separating track" in line or ("%" in line and "|" in line):
                log_func(line.strip())
                # Parse demucs progress bar
                if "%" in line and "|" in line:
                    match = re.search(r'(\d+)%\|[█▉▊▋▌▍▎▏ ]*\|', line)
                    if match:
                        percent = int(match.group(1))
                        progress_func(55 + (percent * 0.35), f"Separating vocals: {percent}%")
                    
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, "demucs")
            
        progress_func(90, "Vocal separation complete")

        separated_dir = Path("separated") / DEMUCS_MODEL
        vocals_path = None
        for root, dirs, files in os.walk(separated_dir):
            if "vocals.wav" in files:
                vocals_path = os.path.join(root, "vocals.wav")
                break

        if not vocals_path or not os.path.exists(vocals_path):
            log_func("Vocals file not found!")
            progress_func(0, "Error: Vocals file not found")
            return

        if action == "extract":
            output_audio = f"{final_title}.wav"
            shutil.copy(vocals_path, output_audio)
            log_func(f"Vocals extracted: {output_audio}")
            progress_func(100, "Complete! Vocals extracted")
        elif action == "merge":
            output_video = f"{final_title}.mp4"
            log_func(f"Merging vocals into video as {output_video}...")
            progress_func(95, "Merging vocals with video...")
            
            # Final merge with progress
            process = subprocess.Popen([
                "ffmpeg", "-y",
                "-i", str(video_file),
                "-i", vocals_path,
                "-c:v", "copy",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                output_video
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            
            for line in process.stdout:
                if "time=" in line:
                    time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                    if time_match:
                        hours, minutes, seconds = time_match.groups()
                        progress_func(97, f"Merging: {int(hours):02d}:{int(minutes):02d}:{int(float(seconds)):02d}")
                        
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "ffmpeg merge")
                
            log_func(f"Done! Saved as {output_video}")
            progress_func(100, f"Complete! Saved as {output_video}")

        # Cleanup
        os.remove(audio_file)
        shutil.rmtree(separated_dir, ignore_errors=True)

    except subprocess.CalledProcessError as e:
        log_func(f"Command failed: {e}")
        progress_func(0, f"Error: Command failed")
    except Exception as e:
        log_func(f"Unexpected error: {e}")
        progress_func(0, f"Error: {str(e)}")

# -----------------------------
# Simple Theme Management
# -----------------------------
class SimpleTheme:
    def __init__(self):
        self.is_dark = True
        
    def get_colors(self):
        if self.is_dark:
            return {
                "bg": "#1a1a1a",
                "surface": "#2d2d2d", 
                "primary": "#4A90E2",
                "text": "#ffffff",
                "text_secondary": "#b0b0b0",
                "success": "#10b981",
                "warning": "#f59e0b"
            }
        else:
            return {
                "bg": "#ffffff",
                "surface": "#f8f9fa",
                "primary": "#4A90E2", 
                "text": "#1a1a1a",
                "text_secondary": "#6b7280",
                "success": "#059669",
                "warning": "#d97706"
            }
    
    def toggle(self):
        self.is_dark = not self.is_dark
        ctk.set_appearance_mode("dark" if self.is_dark else "light")

theme = SimpleTheme()

# -----------------------------
# UI Functions
# -----------------------------
local_video_path = ""

def select_file():
    global local_video_path
    path = filedialog.askopenfilename(
        title="Select a video file",
        filetypes=[("Video files", "*.mp4 *.mov *.mkv *.webm")]
    )
    if path:
        local_video_path = path
        file_label.configure(text=f"Selected: {os.path.basename(path)}")
        url_entry.delete(0, "end")

def start_processing():
    url = url_entry.get().strip()
    final_title = title_entry.get().strip()
    action = action_var.get()

    if not url and not local_video_path:
        log("Please enter a YouTube URL or select a local video.")
        return
    if not final_title:
        log("Please enter a title for the output file.")
        return

    log_textbox.delete("1.0", "end")
    log("Starting processing...")
    
    progress_bar.set(0)
    progress_label.configure(text="Starting...")
    
    threading.Thread(target=process_video, args=(url, local_video_path, final_title, action, log, update_progress), daemon=True).start()

def update_progress(value, status):
    """Update progress bar and status label"""
    progress_bar.set(value / 100.0)  # CTkProgressBar expects 0-1 range
    progress_label.configure(text=status)
    app.update_idletasks()

def log(message):
    log_textbox.insert("end", message + "\n")
    log_textbox.see("end")
    app.update_idletasks()

def toggle_theme():
    theme.toggle()
    colors = theme.get_colors()
    
    app.configure(fg_color=colors["bg"])
    main_frame.configure(fg_color=colors["surface"])
    
    # Update buttons
    theme_btn.configure(text="☀️ Light" if theme.is_dark else "🌙 Dark")
    start_btn.configure(fg_color=colors["success"])
    clear_btn.configure(fg_color=colors["warning"])
    
    # Update text colors
    for widget in [title_label, url_label, file_label, output_label, log_label]:
        widget.configure(text_color=colors["text"])

def about_dialog():
    colors = theme.get_colors()
    about_window = ctk.CTkToplevel(app)
    about_window.title("About")
    about_window.geometry("400x300")
    about_window.configure(fg_color=colors["bg"])
    
    try:
        logo_image = ctk.CTkImage(Image.open("icon.png"), size=(64, 64))
        logo_label = ctk.CTkLabel(about_window, image=logo_image, text="")
        logo_label.pack(pady=20)
    except:
        logo_label = ctk.CTkLabel(about_window, text="🎵", font=ctk.CTkFont(size=48))
        logo_label.pack(pady=20)
    
    ctk.CTkLabel(about_window, text="Ohne - Only Vocals", 
                font=ctk.CTkFont(size=24, weight="bold")).pack(pady=10)
    
    ctk.CTkLabel(about_window, text="Professional vocal extraction tool\nPowered by Demucs AI", 
                font=ctk.CTkFont(size=14), justify="center").pack(pady=10)
    
    ctk.CTkLabel(about_window, text="Created by: Marouane Elhizabri\nLinkedIn: linkedin.com/in/marouaneelhizabri", 
                font=ctk.CTkFont(size=12), justify="center").pack(pady=20)
    
    ctk.CTkButton(about_window, text="Close", command=about_window.destroy).pack(pady=20)

def help_dialog():
    colors = theme.get_colors()
    help_window = ctk.CTkToplevel(app)
    help_window.title("Help")
    help_window.geometry("500x400")
    help_window.configure(fg_color=colors["bg"])
    
    ctk.CTkLabel(help_window, text="How to Use", 
                font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
    
    help_text = """1. Enter a YouTube URL or select a local video file
2. Enter a name for your output file
3. Choose processing mode:
   • Extract Vocals Only: Creates a WAV audio file
   • Merge with Video: Creates an MP4 with vocals only
4. Click 'Start Processing' and wait for completion

Supported formats: MP4, MOV, MKV, WEBM
Processing time varies based on video length."""
    
    ctk.CTkLabel(help_window, text=help_text, font=ctk.CTkFont(size=12), 
                justify="left", anchor="w").pack(pady=20, padx=30, fill="both")
    
    ctk.CTkButton(help_window, text="Close", command=help_window.destroy).pack(pady=20)

def clear_logs():
    log_textbox.delete("1.0", "end")
    log("Logs cleared")

# -----------------------------
# Simple UI Setup
# -----------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Ohne - Only Vocals")
app.geometry("800x700")
app.minsize(750, 650)

try:
    icon_image = Image.open("icon.png")
    icon_photo = ImageTk.PhotoImage(icon_image.resize((32, 32)))
    app.iconphoto(True, icon_photo)
except:
    pass

colors = theme.get_colors()
app.configure(fg_color=colors["bg"])

main_frame = ctk.CTkFrame(app, corner_radius=15)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Header with logo and theme toggle
header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
header_frame.pack(fill="x", padx=20, pady=20)

header_left = ctk.CTkFrame(header_frame, fg_color="transparent")
header_left.pack(side="left", fill="x", expand=True)

try:
    logo_image = ctk.CTkImage(Image.open("icon.png"), size=(40, 40))
    logo_label = ctk.CTkLabel(header_left, image=logo_image, text="")
    logo_label.pack(side="left", padx=(0, 10))
except:
    logo_label = ctk.CTkLabel(header_left, text="🎵", font=ctk.CTkFont(size=32))
    logo_label.pack(side="left", padx=(0, 10))

title_label = ctk.CTkLabel(header_left, text="Ohne - Only Vocals", 
                          font=ctk.CTkFont(size=24, weight="bold"))
title_label.pack(side="left", anchor="w")

theme_btn = ctk.CTkButton(header_frame, text="☀️ Light", command=toggle_theme, 
                         width=100, height=32)
theme_btn.pack(side="right")

# Input section
input_frame = ctk.CTkFrame(main_frame)
input_frame.pack(fill="x", padx=20, pady=(0, 20))

url_label = ctk.CTkLabel(input_frame, text="YouTube URL:", font=ctk.CTkFont(size=14, weight="bold"))
url_label.pack(anchor="w", padx=20, pady=(20, 5))

url_entry = ctk.CTkEntry(input_frame, placeholder_text="https://youtube.com/watch?v=...", height=40)
url_entry.pack(fill="x", padx=20, pady=(0, 15))

file_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
file_frame.pack(fill="x", padx=20, pady=(0, 15))

ctk.CTkButton(file_frame, text="Select Local File", command=select_file, 
             height=40, width=150).pack(side="left")

file_label = ctk.CTkLabel(file_frame, text="No file selected")
file_label.pack(side="left", padx=(15, 0))

output_label = ctk.CTkLabel(input_frame, text="Output filename:", font=ctk.CTkFont(size=14, weight="bold"))
output_label.pack(anchor="w", padx=20, pady=(15, 5))

title_entry = ctk.CTkEntry(input_frame, placeholder_text="my_vocals", height=40)
title_entry.pack(fill="x", padx=20, pady=(0, 15))

# Action selection
action_var = ctk.StringVar(value="merge")
action_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
action_frame.pack(fill="x", padx=20, pady=(0, 20))

ctk.CTkRadioButton(action_frame, text="Extract Vocals Only (WAV)", 
                  variable=action_var, value="extract").pack(anchor="w", pady=2)
ctk.CTkRadioButton(action_frame, text="Merge with Video (MP4)", 
                  variable=action_var, value="merge").pack(anchor="w", pady=2)

# Control buttons
button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
button_frame.pack(fill="x", padx=20, pady=(0, 20))

start_btn = ctk.CTkButton(button_frame, text="Start Processing", command=start_processing, 
                         height=45, fg_color=colors["success"])
start_btn.pack(side="left", padx=(0, 10))

clear_btn = ctk.CTkButton(button_frame, text="Clear Logs", command=clear_logs, 
                         height=45, fg_color=colors["warning"])
clear_btn.pack(side="left", padx=(0, 10))

ctk.CTkButton(button_frame, text="Help", command=help_dialog, height=45).pack(side="left", padx=(0, 10))
ctk.CTkButton(button_frame, text="About", command=about_dialog, height=45).pack(side="left")

# Log section
log_frame = ctk.CTkFrame(main_frame)
log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

log_label = ctk.CTkLabel(log_frame, text="Processing Log:", font=ctk.CTkFont(size=14, weight="bold"))
log_label.pack(anchor="w", padx=20, pady=(15, 5))

progress_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
progress_frame.pack(fill="x", padx=20, pady=(0, 10))

progress_label = ctk.CTkLabel(progress_frame, text="Ready to start", font=ctk.CTkFont(size=12))
progress_label.pack(anchor="w", pady=(0, 5))

progress_bar = ctk.CTkProgressBar(progress_frame, height=20)
progress_bar.pack(fill="x", pady=(0, 10))
progress_bar.set(0)

log_textbox = ctk.CTkTextbox(log_frame, height=150, font=ctk.CTkFont(family="Courier", size=11))
log_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))

log("Welcome to Ohne - Only Vocals")
log("Select a video source and click 'Start Processing' to begin")

if __name__ == "__main__":
    app.mainloop()
