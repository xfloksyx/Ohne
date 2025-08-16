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
# Detect platform-specific binaries
# -----------------------------
if sys.platform.startswith("win"):
    FFMPEG_BIN = os.path.join(os.getcwd(), "ffmpeg.exe")
    YTDLP_BIN = os.path.join(os.getcwd(), "yt-dlp.exe")
else:
    FFMPEG_BIN = os.path.join(os.getcwd(), "ffmpeg")
    YTDLP_BIN = os.path.join(os.getcwd(), "yt-dlp")

# Ensure binaries exist and are executable
if not os.path.exists(YTDLP_BIN):
    raise FileNotFoundError(f"yt-dlp not found at {YTDLP_BIN}")
if not os.path.exists(FFMPEG_BIN):
    raise FileNotFoundError(f"ffmpeg not found at {FFMPEG_BIN}")
os.chmod(YTDLP_BIN, 0o755)
os.chmod(FFMPEG_BIN, 0o755)

# -----------------------------
# Processing Functions
# -----------------------------
DEMUCS_MODEL = "htdemucs"

def process_video(youtube_url, local_video_path, final_title, action, log_func, progress_func):
    try:
        videos_folder = "videos"
        os.makedirs(videos_folder, exist_ok=True)
        
        progress_func(0, "Initializing...")

        if local_video_path:
            video_file = Path(local_video_path)
            progress_func(10, "Using local video file")
        else:
            # Cleanup old videos
            for existing_video in Path(".").glob("video.*"):
                try:
                    os.remove(existing_video)
                except:
                    pass
            
            progress_func(10, "Downloading video...")
            
            process = subprocess.Popen(
                [YTDLP_BIN, "-f", "bestvideo+bestaudio", "-o", "video.%(ext)s", youtube_url],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            
            for line in process.stdout:
                if "[download]" in line and "%" in line:
                    match = re.search(r'(\d+(?:\.\d+)?)%', line)
                    if match:
                        percent = float(match.group(1))
                        progress_func(10 + (percent * 0.2), f"Downloading: {percent:.1f}%")
                        
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "yt-dlp")
                
            video_file = next(Path(".").glob("video.*"))
            progress_func(30, "Video download complete")

        audio_file = "audio.wav"
        progress_func(35, "Extracting audio...")

        process = subprocess.Popen([
            FFMPEG_BIN, "-y", "-i", str(video_file),
            "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            audio_file
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        for line in process.stdout:
            if "time=" in line:
                time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                if time_match:
                    hours, minutes, seconds = time_match.groups()
                    current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    progress_func(35 + min(15, current_time / 10), f"Extracting audio: {int(hours):02d}:{int(minutes):02d}:{int(float(seconds)):02d}")
                    
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, "ffmpeg")
        
        progress_func(50, "Audio extraction complete")

        # -----------------------------
        # Vocal separation with Demucs
        # -----------------------------
        log_func("Starting vocal separation...")
        progress_func(55, "Starting vocal separation...")

        process = subprocess.Popen([
            "demucs", "--two-stems=vocals", "-n", DEMUCS_MODEL, audio_file
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

        for line in process.stdout:
            if "Separating track" in line or ("%" in line and "|" in line):
                log_func(line.strip())
                if "%" in line and "|" in line:
                    match = re.search(r'(\d+)%\|[█▉▊▋▌▍▎▏ ]*\|', line)
                    if match:
                        percent = int(match.group(1))
                        progress_func(55 + (percent * 0.35), f"Separating vocals ...")

        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, "demucs")

        progress_func(90, "Vocal separation complete")
        # Continue with merge/extract logic...



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
            output_audio = os.path.join(videos_folder, f"{final_title}.wav")
            shutil.copy(vocals_path, output_audio)
            
            # Get full path and display it
            full_path = os.path.abspath(output_audio)
            log_func(f"Vocals extracted: {output_audio}")
            log_func(f"Full path: {full_path}")
            progress_func(100, "Complete! Vocals extracted")
            
            # Auto-open the audio file
            try:
                if sys.platform.startswith('win'):
                    os.startfile(full_path)
                elif sys.platform.startswith('darwin'):
                    subprocess.call(["open", full_path])
                else:
                    subprocess.call(["xdg-open", full_path])
                log_func("Opening audio file...")
            except Exception as e:
                log_func(f"Could not open file automatically: {e}")
                
        elif action == "merge":
            output_video = os.path.join(videos_folder, f"{final_title}.mp4")
            progress_func(95, "Merging vocals with video...")
            
            process = subprocess.Popen([
                FFMPEG_BIN, "-y",
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
            
            # Get full path and display it
            full_path = os.path.abspath(output_video)
            log_func(f"Done! Saved as {output_video}")
            log_func(f"Full path: {full_path}")
            progress_func(100, f"Complete! Saved as {output_video}")
            
            # Auto-open the video file
            try:
                if sys.platform.startswith('win'):
                    os.startfile(full_path)
                elif sys.platform.startswith('darwin'):
                    subprocess.call(["open", full_path])
                else:
                    subprocess.call(["xdg-open", full_path])
                log_func("Opening video file...")
            except Exception as e:
                log_func(f"Could not open file automatically: {e}")

        try:
            os.remove(audio_file)
        except:
            pass
        
        if not local_video_path:
            for video_cleanup in Path(".").glob("video.*"):
                try:
                    os.remove(video_cleanup)
                except:
                    pass
        
        shutil.rmtree(separated_dir, ignore_errors=True)
        
        app.after(1000, reset_inputs)

    except subprocess.CalledProcessError as e:
        log_func(f"Command failed: {e}")
        progress_func(0, f"Error: Command failed")
    except Exception as e:
        log_func(f"Unexpected error: {e}")
        progress_func(0, f"Error: {str(e)}")

# -----------------------------
# UI Functions
# -----------------------------
local_video_path = ""

def reset_inputs():
    global local_video_path
    local_video_path = ""
    url_entry.delete(0, "end")
    title_entry.delete(0, "end")
    file_label.configure(text="No file selected")
    progress_bar.set(0)
    progress_label.configure(text="Ready to start")

def on_url_change(*args):
    global local_video_path
    if url_entry.get().strip():
        local_video_path = ""
        file_label.configure(text="No file selected")

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

    log_textbox.configure(state="normal")
    log_textbox.delete("1.0", "end")
    log_textbox.configure(state="disabled")
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
    log_textbox.configure(state="normal")
    log_textbox.insert("end", message + "\n")
    log_textbox.see("end")
    log_textbox.configure(state="disabled")
    app.update_idletasks()

def clear_logs():
    log_textbox.configure(state="normal")
    log_textbox.delete("1.0", "end")
    log_textbox.insert("end", "Logs cleared\n")
    log_textbox.configure(state="disabled")

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
    if os.path.exists("icon.ico"):
        app.iconbitmap("icon.ico")
except Exception as e:
    print(f"Could not set window icon: {e}")

colors = {
    "bg": "#1a1a1a",
    "surface": "#2d2d2d", 
    "primary": "#4A90E2",
    "text": "#ffffff",
    "text_secondary": "#b0b0b0",
    "success": "#10b981",
    "warning": "#f59e0b"
}

app.configure(fg_color=colors["bg"])

main_frame = ctk.CTkFrame(app, corner_radius=25)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

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

tabview = ctk.CTkTabview(main_frame, corner_radius=25, width=900, height=420,
                        segmented_button_fg_color=("#E5E5E7", "#2A2D2E"), 
                        segmented_button_selected_color=("#007AFF", "#0A84FF"),
                        segmented_button_unselected_color=("#F2F2F7", "#3A3A3C"),
                        border_width=0)
tabview.pack(fill="both", expand=True, padx=20, pady=(0, 20))

# Create tabs
main_tab = tabview.add("Main")
about_tab = tabview.add("About")
help_tab = tabview.add("Help")

main_content_frame = ctk.CTkScrollableFrame(main_tab, corner_radius=20)
main_content_frame.pack(fill="both", expand=True, padx=15, pady=15)

# Input section
input_frame = ctk.CTkFrame(main_content_frame, corner_radius=20)
input_frame.pack(fill="x", padx=5, pady=(5, 15))

url_label = ctk.CTkLabel(input_frame, text="YouTube URL:", font=ctk.CTkFont(size=14, weight="bold"))
url_label.pack(anchor="w", padx=25, pady=(25, 8))

url_entry = ctk.CTkEntry(input_frame, placeholder_text="https://youtube.com/watch?v=...", 
                        height=44, corner_radius=22, font=ctk.CTkFont(size=14))
url_entry.pack(fill="x", padx=25, pady=(0, 20))
url_entry.bind('<KeyRelease>', on_url_change)

file_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
file_frame.pack(fill="x", padx=25, pady=(0, 20))

ctk.CTkButton(file_frame, text="Select Local File", command=select_file, 
             height=44, width=160, corner_radius=22, font=ctk.CTkFont(size=14)).pack(side="left")

file_label = ctk.CTkLabel(file_frame, text="No file selected", font=ctk.CTkFont(size=14))
file_label.pack(side="left", padx=(20, 0))

output_label = ctk.CTkLabel(input_frame, text="Output filename:", font=ctk.CTkFont(size=14, weight="bold"))
output_label.pack(anchor="w", padx=25, pady=(20, 8))

title_entry = ctk.CTkEntry(input_frame, placeholder_text="my_vocals", 
                          height=44, corner_radius=22, font=ctk.CTkFont(size=14))
title_entry.pack(fill="x", padx=25, pady=(0, 20))

# Action selection
action_var = ctk.StringVar(value="merge")
action_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
action_frame.pack(fill="x", padx=25, pady=(0, 25))

ctk.CTkRadioButton(action_frame, text="Extract Vocals Only (WAV)", 
                  variable=action_var, value="extract", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)
ctk.CTkRadioButton(action_frame, text="Merge with Video (MP4)", 
                  variable=action_var, value="merge", font=ctk.CTkFont(size=14)).pack(anchor="w", pady=5)

# Control buttons
button_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent")
button_frame.pack(fill="x", padx=5, pady=(0, 20))

start_btn = ctk.CTkButton(button_frame, text="Start Processing", command=start_processing, 
                         height=50, corner_radius=25, fg_color=colors["success"], 
                         font=ctk.CTkFont(size=16, weight="bold"))
start_btn.pack(side="left", padx=(0, 15))

clear_btn = ctk.CTkButton(button_frame, text="Clear Logs", command=clear_logs, 
                         height=50, corner_radius=25, fg_color=colors["warning"],
                         font=ctk.CTkFont(size=16, weight="bold"))
clear_btn.pack(side="left")



# Log section
log_frame = ctk.CTkFrame(main_content_frame, corner_radius=20)
log_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

log_label = ctk.CTkLabel(log_frame, text="Processing Log:", font=ctk.CTkFont(size=14, weight="bold"))
log_label.pack(anchor="w", padx=25, pady=(20, 8))

progress_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
progress_frame.pack(fill="x", padx=25, pady=(0, 15))

progress_label = ctk.CTkLabel(progress_frame, text="Ready to start", font=ctk.CTkFont(size=13))
progress_label.pack(anchor="w", pady=(0, 8))

progress_bar = ctk.CTkProgressBar(progress_frame, height=24, corner_radius=12)
progress_bar.pack(fill="x", pady=(0, 15))
progress_bar.set(0)

log_textbox = ctk.CTkTextbox(log_frame, height=120, font=ctk.CTkFont(family="Courier", size=12),
                            corner_radius=15, state="disabled")
log_textbox.pack(fill="both", expand=True, padx=25, pady=(0, 25))

# About tab content
about_content_frame = ctk.CTkScrollableFrame(about_tab, corner_radius=20)
about_content_frame.pack(fill="both", expand=True, padx=15, pady=15)

try:
    logo_image_large = ctk.CTkImage(Image.open("icon.png"), size=(80, 80))
    about_logo_label = ctk.CTkLabel(about_content_frame, image=logo_image_large, text="")
    about_logo_label.pack(pady=(20, 20))
except:
    about_logo_label = ctk.CTkLabel(about_content_frame, text="🎵", font=ctk.CTkFont(size=64))
    about_logo_label.pack(pady=(20, 20))

ctk.CTkLabel(about_content_frame, text="Ohne - Only Vocals", 
            font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(0, 15))

ctk.CTkLabel(about_content_frame, text="Professional vocal extraction tool", 
            font=ctk.CTkFont(size=16), justify="center").pack(pady=(0, 20))

ctk.CTkLabel(about_content_frame, text="Created by: Marouane Elhizabri\nLinkedIn: linkedin.com/in/marouaneelhizabri", 
            font=ctk.CTkFont(size=14), justify="center").pack(pady=(0, 20))

ctk.CTkLabel(about_content_frame, text="Version 1.0\n© 2025 All rights reserved", 
            font=ctk.CTkFont(size=12), justify="center").pack(pady=(0, 20))

ctk.CTkLabel(about_content_frame, text="Features:", 
            font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(30, 10))

features_text = """• AI-powered vocal separation 
• Support for YouTube URLs and local video files
• Multiple output formats (WAV audio, MP4 video)
• Real-time processing progress tracking
• Automatic file organization in videos folder
• Cross-platform compatibility (Windows, macOS, Linux)
• Professional-grade audio quality
• Batch processing capabilities"""

ctk.CTkLabel(about_content_frame, text=features_text, 
            font=ctk.CTkFont(size=14), justify="left").pack(pady=(0, 20))

ctk.CTkLabel(about_content_frame, text="Technical Specifications:", 
            font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

tech_text = """• Demucs AI Model: htdemucs (state-of-the-art separation)
• Audio Processing: 44.1kHz, 16-bit PCM
• Video Codecs: H.264, VP9, AV1 support
• Container Formats: MP4, MOV, MKV, WEBM
• Dependencies: Automatically managed (FFmpeg, yt-dlp, PyTorch)
• Memory Usage: Optimized for efficiency
• Processing Speed: Real-time on modern hardware"""

ctk.CTkLabel(about_content_frame, text=tech_text, 
            font=ctk.CTkFont(size=14), justify="left").pack(pady=(0, 30))

# Help tab content
help_content_frame = ctk.CTkScrollableFrame(help_tab, corner_radius=20)
help_content_frame.pack(fill="both", expand=True, padx=15, pady=15)

ctk.CTkLabel(help_content_frame, text="How to Use", 
            font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 20))

help_sections = [
    ("Getting Started", """1. Choose your video source:
   • Enter a YouTube URL in the text field
   • OR click 'Select Local File' to browse for a video

2. Enter a descriptive name for your output file
   • This will be the filename of your processed video/audio
   • Don't include file extensions (.mp4, .wav)

3. Select processing mode:
   • Extract Vocals Only: Creates a WAV audio file with isolated vocals
   • Merge with Video: Creates an MP4 video with vocals-only audio track"""),
    
    ("Processing", """4. Click 'Start Processing' to begin
   • The progress bar shows real-time processing status
   • Processing stages: Download → Extract Audio → Separate Vocals → Merge
   • Processing time depends on video length (typically 2-5x real-time)

5. Monitor the log for detailed progress information
   • Only essential progress information is shown
   • Errors and warnings will be displayed if they occur"""),
    
    ("Output Files", """• All output files are automatically saved to the 'videos' folder
• Files are automatically opened when processing completes
• Full file paths are displayed in the processing log
• Supported input formats: MP4, MOV, MKV, WEBM
• Output formats: WAV (audio), MP4 (video)"""),
    
    ("Tips & Troubleshooting", """• Ensure stable internet connection for YouTube downloads
• Close other audio/video applications during processing
• For best results, use videos with clear vocal tracks
• Processing requires significant CPU/GPU resources
• If processing fails, check the log for error details
• Temporary files are automatically cleaned up after processing"""),
    
    ("System Requirements", """• Operating System: Windows 10+, macOS 10.14+, or Linux
• RAM: 8GB minimum, 16GB recommended
• Storage: 2GB free space per hour of video
• Internet: Required for YouTube downloads and model downloads
• Dependencies: Automatically managed (FFmpeg, yt-dlp, PyTorch)""")
]

for section_title, section_content in help_sections:
    ctk.CTkLabel(help_content_frame, text=section_title, 
                font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10), anchor="w")
    
    ctk.CTkLabel(help_content_frame, text=section_content, 
                font=ctk.CTkFont(size=14), justify="left", wraplength=650).pack(pady=(0, 10), anchor="w")

if __name__ == "__main__":
    app.mainloop()
