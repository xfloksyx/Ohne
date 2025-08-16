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
# Enhanced Modern UI Setup
# -----------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Ohne - Only Vocals")
app.geometry("900x750")
app.minsize(800, 700)

try:
    if os.path.exists("icon.ico"):
        app.iconbitmap("icon.ico")
except Exception as e:
    print(f"Could not set window icon: {e}")

# Enhanced color palette with gradients and modern colors
colors = {
    "bg": "#0a0a0b",
    "surface": "#161618", 
    "surface_light": "#1f1f23",
    "surface_elevated": "#2a2a2f",
    "primary": "#007AFF",
    "primary_hover": "#0056D6",
    "primary_light": "#4A9EFF",
    "accent": "#FF6B35",
    "accent_hover": "#FF5722",
    "success": "#34C759",
    "success_hover": "#28A745",
    "warning": "#FF9500",
    "warning_hover": "#E6840E",
    "error": "#FF3B30",
    "text_primary": "#FFFFFF",
    "text_secondary": "#98989F",
    "text_tertiary": "#636366",
    "border": "#2C2C2E",
    "border_light": "#3A3A3C"
}

app.configure(fg_color=colors["bg"])

# Main container with subtle gradient effect
main_frame = ctk.CTkFrame(
    app, 
    corner_radius=30,
    fg_color=colors["surface"],
    border_width=1,
    border_color=colors["border"]
)
main_frame.pack(fill="both", expand=True, padx=25, pady=25)

# Enhanced header with better typography
header_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=80)
header_frame.pack(fill="x", padx=30, pady=(30, 20))
header_frame.pack_propagate(False)

header_left = ctk.CTkFrame(header_frame, fg_color="transparent")
header_left.pack(side="left", fill="both", expand=True)

# Logo with improved styling
try:
    logo_image = ctk.CTkImage(Image.open("icon.png"), size=(48, 48))
    logo_label = ctk.CTkLabel(header_left, image=logo_image, text="")
    logo_label.pack(side="left", padx=(0, 15), pady=16)
except:
    logo_frame = ctk.CTkFrame(
        header_left, 
        width=48, 
        height=48, 
        corner_radius=24,
        fg_color=colors["primary"]
    )
    logo_frame.pack(side="left", padx=(0, 15), pady=16)
    logo_frame.pack_propagate(False)
    
    logo_emoji = ctk.CTkLabel(
        logo_frame, 
        text="🎵", 
        font=ctk.CTkFont(size=28),
        text_color=colors["text_primary"]
    )
    logo_emoji.pack(expand=True)

# Enhanced title with gradient-like effect
title_container = ctk.CTkFrame(header_left, fg_color="transparent")
title_container.pack(side="left", fill="both", expand=True, pady=16)

title_label = ctk.CTkLabel(
    title_container, 
    text="Ohne - Only Vocals", 
    font=ctk.CTkFont(size=32, weight="bold"),
    text_color=colors["text_primary"]
)
title_label.pack(anchor="w")

subtitle_label = ctk.CTkLabel(
    title_container,
    text="Professional AI-powered vocal separation",
    font=ctk.CTkFont(size=14, weight="normal"),
    text_color=colors["text_secondary"]
)
subtitle_label.pack(anchor="w", pady=(2, 0))

# Enhanced tabview with modern styling
tabview = ctk.CTkTabview(
    main_frame, 
    corner_radius=25, 
    width=900, 
    height=500,
    segmented_button_fg_color=colors["surface_light"], 
    segmented_button_selected_color=colors["primary"],
    segmented_button_unselected_color=colors["surface_elevated"],
    segmented_button_selected_hover_color=colors["primary_hover"],
    segmented_button_unselected_hover_color=colors["surface_elevated"],
    border_width=1,
    border_color=colors["border"],
    text_color=colors["text_primary"],
    text_color_disabled=colors["text_tertiary"]
)
tabview.pack(fill="both", expand=True, padx=30, pady=(0, 30))

# Create tabs
main_tab = tabview.add("Main")
about_tab = tabview.add("About") 
help_tab = tabview.add("Help")

# Enhanced scrollable content
main_content_frame = ctk.CTkScrollableFrame(
    main_tab, 
    corner_radius=20,
    fg_color=colors["surface_light"],
    scrollbar_button_color=colors["surface_elevated"],
    scrollbar_button_hover_color=colors["border_light"]
)
main_content_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Enhanced input section with modern cards
input_frame = ctk.CTkFrame(
    main_content_frame, 
    corner_radius=20,
    fg_color=colors["surface_elevated"],
    border_width=1,
    border_color=colors["border_light"]
)
input_frame.pack(fill="x", padx=8, pady=(8, 20))

# URL input with enhanced styling
url_section = ctk.CTkFrame(input_frame, fg_color="transparent")
url_section.pack(fill="x", padx=25, pady=(25, 15))

url_label = ctk.CTkLabel(
    url_section, 
    text="YouTube URL", 
    font=ctk.CTkFont(size=16, weight="bold"),
    text_color=colors["text_primary"]
)
url_label.pack(anchor="w", pady=(0, 8))

url_entry = ctk.CTkEntry(
    url_section, 
    placeholder_text="https://youtube.com/watch?v=...", 
    height=50, 
    corner_radius=25, 
    font=ctk.CTkFont(size=15),
    border_width=2,
    border_color=colors["border"],
    fg_color=colors["surface_light"],
    placeholder_text_color=colors["text_tertiary"],
    text_color=colors["text_primary"]
)
url_entry.pack(fill="x", pady=(0, 5))
url_entry.bind('<KeyRelease>', on_url_change)

# File selection with enhanced button
file_section = ctk.CTkFrame(input_frame, fg_color="transparent")
file_section.pack(fill="x", padx=25, pady=15)

file_row = ctk.CTkFrame(file_section, fg_color="transparent")
file_row.pack(fill="x")

file_select_btn = ctk.CTkButton(
    file_row, 
    text="📁 Select Local File", 
    command=select_file, 
    height=50, 
    width=180, 
    corner_radius=25, 
    font=ctk.CTkFont(size=15, weight="bold"),
    fg_color=colors["surface_light"],
    hover_color=colors["border_light"],
    text_color=colors["text_primary"],
    border_width=2,
    border_color=colors["border"]
)
file_select_btn.pack(side="left")

file_label = ctk.CTkLabel(
    file_row, 
    text="No file selected", 
    font=ctk.CTkFont(size=15),
    text_color=colors["text_secondary"]
)
file_label.pack(side="left", padx=(20, 0), pady=12)

# Output filename input
output_section = ctk.CTkFrame(input_frame, fg_color="transparent")
output_section.pack(fill="x", padx=25, pady=15)

output_label = ctk.CTkLabel(
    output_section, 
    text="Output Filename", 
    font=ctk.CTkFont(size=16, weight="bold"),
    text_color=colors["text_primary"]
)
output_label.pack(anchor="w", pady=(0, 8))

title_entry = ctk.CTkEntry(
    output_section, 
    placeholder_text="my_vocals", 
    height=50, 
    corner_radius=25, 
    font=ctk.CTkFont(size=15),
    border_width=2,
    border_color=colors["border"],
    fg_color=colors["surface_light"],
    placeholder_text_color=colors["text_tertiary"],
    text_color=colors["text_primary"]
)
title_entry.pack(fill="x")

# Enhanced action selection with modern radio buttons
action_var = ctk.StringVar(value="merge")
action_section = ctk.CTkFrame(input_frame, fg_color="transparent")
action_section.pack(fill="x", padx=25, pady=(20, 25))

action_label = ctk.CTkLabel(
    action_section,
    text="Processing Mode",
    font=ctk.CTkFont(size=16, weight="bold"),
    text_color=colors["text_primary"]
)
action_label.pack(anchor="w", pady=(0, 15))

radio_frame = ctk.CTkFrame(action_section, fg_color="transparent")
radio_frame.pack(fill="x")

extract_radio = ctk.CTkRadioButton(
    radio_frame, 
    text="🎵 Extract Vocals Only (WAV)", 
    variable=action_var, 
    value="extract", 
    font=ctk.CTkFont(size=15),
    text_color=colors["text_primary"],
    radiobutton_width=24,
    radiobutton_height=24
)
extract_radio.pack(anchor="w", pady=(0, 12))

merge_radio = ctk.CTkRadioButton(
    radio_frame, 
    text="🎬 Merge with Video (MP4)", 
    variable=action_var, 
    value="merge", 
    font=ctk.CTkFont(size=15),
    text_color=colors["text_primary"],
    radiobutton_width=24,
    radiobutton_height=24
)
merge_radio.pack(anchor="w")

# Enhanced control buttons with better styling
button_section = ctk.CTkFrame(main_content_frame, fg_color="transparent")
button_section.pack(fill="x", padx=8, pady=(0, 20))

button_row = ctk.CTkFrame(button_section, fg_color="transparent")
button_row.pack()

start_btn = ctk.CTkButton(
    button_row, 
    text="▶️ Start Processing", 
    command=start_processing, 
    height=56, 
    width=200,
    corner_radius=28, 
    fg_color=colors["success"], 
    hover_color=colors["success_hover"],
    font=ctk.CTkFont(size=17, weight="bold"),
    text_color=colors["text_primary"]
)
start_btn.pack(side="left", padx=(0, 15))

clear_btn = ctk.CTkButton(
    button_row, 
    text="🗑️ Clear Logs", 
    command=clear_logs, 
    height=56, 
    width=160,
    corner_radius=28, 
    fg_color=colors["warning"],
    hover_color=colors["warning_hover"],
    font=ctk.CTkFont(size=17, weight="bold"),
    text_color=colors["text_primary"]
)
clear_btn.pack(side="left")

# Enhanced log section with modern design
log_frame = ctk.CTkFrame(
    main_content_frame, 
    corner_radius=20,
    fg_color=colors["surface_elevated"],
    border_width=1,
    border_color=colors["border_light"]
)
log_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

log_header = ctk.CTkFrame(log_frame, fg_color="transparent", height=60)
log_header.pack(fill="x", padx=25, pady=(25, 0))
log_header.pack_propagate(False)

log_title = ctk.CTkLabel(
    log_header, 
    text="Processing Log", 
    font=ctk.CTkFont(size=18, weight="bold"),
    text_color=colors["text_primary"]
)
log_title.pack(anchor="w", pady=16)

# Enhanced progress section
progress_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
progress_frame.pack(fill="x", padx=25, pady=(0, 15))

progress_label = ctk.CTkLabel(
    progress_frame, 
    text="Ready to start", 
    font=ctk.CTkFont(size=14, weight="normal"),
    text_color=colors["text_secondary"]
)
progress_label.pack(anchor="w", pady=(0, 10))

progress_bar = ctk.CTkProgressBar(
    progress_frame, 
    height=28, 
    corner_radius=14,
    progress_color=colors["primary"],
    fg_color=colors["surface_light"],
    border_width=1,
    border_color=colors["border"]
)
progress_bar.pack(fill="x", pady=(0, 15))
progress_bar.set(0)

# Enhanced log textbox
log_textbox = ctk.CTkTextbox(
    log_frame, 
    height=140, 
    font=ctk.CTkFont(family="JetBrains Mono", size=13),
    corner_radius=15, 
    state="disabled",
    fg_color=colors["surface_light"],
    border_width=1,
    border_color=colors["border"],
    text_color=colors["text_primary"],
    scrollbar_button_color=colors["surface_elevated"],
    scrollbar_button_hover_color=colors["border_light"]
)
log_textbox.pack(fill="both", expand=True, padx=25, pady=(0, 25))

# Enhanced About tab
about_content_frame = ctk.CTkScrollableFrame(
    about_tab, 
    corner_radius=20,
    fg_color=colors["surface_light"]
)
about_content_frame.pack(fill="both", expand=True, padx=20, pady=20)

about_header = ctk.CTkFrame(about_content_frame, fg_color="transparent")
about_header.pack(fill="x", pady=(30, 40))

# Enhanced logo for about page
try:
    logo_image_large = ctk.CTkImage(Image.open("icon.png"), size=(100, 100))
    about_logo_label = ctk.CTkLabel(about_header, image=logo_image_large, text="")
    about_logo_label.pack(pady=(0, 20))
except:
    about_logo_frame = ctk.CTkFrame(
        about_header,
        width=100,
        height=100,
        corner_radius=50,
        fg_color=colors["primary"]
    )
    about_logo_frame.pack(pady=(0, 20))
    about_logo_frame.pack_propagate(False)
    
    about_logo_emoji = ctk.CTkLabel(
        about_logo_frame,
        text="🎵",
        font=ctk.CTkFont(size=64)
    )
    about_logo_emoji.pack(expand=True)

about_title = ctk.CTkLabel(
    about_header, 
    text="Ohne - Only Vocals", 
    font=ctk.CTkFont(size=36, weight="bold"),
    text_color=colors["text_primary"]
)
about_title.pack(pady=(0, 10))

about_subtitle = ctk.CTkLabel(
    about_header, 
    text="Professional vocal extraction tool", 
    font=ctk.CTkFont(size=18, weight="normal"),
    text_color=colors["text_secondary"]
)
about_subtitle.pack(pady=(0, 30))

# Info cards with enhanced styling
info_card = ctk.CTkFrame(
    about_content_frame,
    corner_radius=20,
    fg_color=colors["surface_elevated"],
    border_width=1,
    border_color=colors["border_light"]
)
info_card.pack(fill="x", pady=(0, 25), padx=20)

info_text = """Created by: Marouane Elhizabri
LinkedIn: linkedin.com/in/marouaneelhizabri
Version: 1.0
© 2025 All rights reserved"""

info_label = ctk.CTkLabel(
    info_card, 
    text=info_text, 
    font=ctk.CTkFont(size=16),
    text_color=colors["text_primary"],
    justify="center"
)
info_label.pack(pady=30)

# Features section with enhanced styling
features_card = ctk.CTkFrame(
    about_content_frame,
    corner_radius=20,
    fg_color=colors["surface_elevated"],
    border_width=1,
    border_color=colors["border_light"]
)
features_card.pack(fill="x", pady=(0, 25), padx=20)

features_title = ctk.CTkLabel(
    features_card, 
    text="✨ Features", 
    font=ctk.CTkFont(size=20, weight="bold"),
    text_color=colors["text_primary"]
)
features_title.pack(pady=(25, 15))

features_text = """• AI-powered vocal separation using state-of-the-art Demucs model
• Support for YouTube URLs and local video files
• Multiple output formats (WAV audio, MP4 video)
• Real-time processing progress tracking with detailed logs
• Automatic file organization in videos folder
• Cross-platform compatibility (Windows, macOS, Linux)
• Professional-grade audio quality (44.1kHz, 16-bit PCM)
• Batch processing capabilities with intelligent cleanup"""

features_label = ctk.CTkLabel(
    features_card, 
    text=features_text, 
    font=ctk.CTkFont(size=15),
    text_color=colors["text_secondary"],
    justify="left"
)
features_label.pack(pady=(0, 25), padx=25)

# Technical specifications
tech_card = ctk.CTkFrame(
    about_content_frame,
    corner_radius=20,
    fg_color=colors["surface_elevated"],
    border_width=1,
    border_color=colors["border_light"]
)
tech_card.pack(fill="x", pady=(0, 30), padx=20)

tech_title = ctk.CTkLabel(
    tech_card, 
    text="⚙️ Technical Specifications", 
    font=ctk.CTkFont(size=20, weight="bold"),
    text_color=colors["text_primary"]
)
tech_title.pack(pady=(25, 15))

tech_text = """• Demucs AI Model: htdemucs (state-of-the-art separation)
• Audio Processing: 44.1kHz, 16-bit PCM
• Video Codecs: H.264, VP9, AV1 support
• Container Formats: MP4, MOV, MKV, WEBM
• Dependencies: Automatically managed (FFmpeg, yt-dlp, PyTorch)
• Memory Usage: Optimized for efficiency
• Processing Speed: Real-time on modern hardware"""

tech_label = ctk.CTkLabel(
    tech_card, 
    text=tech_text, 
    font=ctk.CTkFont(size=15),
    text_color=colors["text_secondary"],
    justify="left"
)
tech_label.pack(pady=(0, 25), padx=25)

# Enhanced Help tab
help_content_frame = ctk.CTkScrollableFrame(
    help_tab, 
    corner_radius=20,
    fg_color=colors["surface_light"]
)
help_content_frame.pack(fill="both", expand=True, padx=20, pady=20)

help_title = ctk.CTkLabel(
    help_content_frame, 
    text="📖 How to Use", 
    font=ctk.CTkFont(size=32, weight="bold"),
    text_color=colors["text_primary"]
)
help_title.pack(pady=(30, 40))

# Help sections with modern card design
help_sections = [
    ("🚀 Getting Started", """1. Choose your video source:
   • Enter a YouTube URL in the text field
   • OR click 'Select Local File' to browse for a video

2. Enter a descriptive name for your output file
   • This will be the filename of your processed video/audio
   • Don't include file extensions (.mp4, .wav)

3. Select processing mode:
   • Extract Vocals Only: Creates a WAV audio file with isolated vocals
   • Merge with Video: Creates an MP4 video with vocals-only audio track"""),
    
    ("⚡ Processing", """4. Click 'Start Processing' to begin
   • The progress bar shows real-time processing status
   • Processing stages: Download → Extract Audio → Separate Vocals → Merge
   • Processing time depends on video length (typically 2-5x real-time)

5. Monitor the log for detailed progress information
   • Only essential progress information is shown
   • Errors and warnings will be displayed if they occur"""),
    
    ("📁 Output Files", """• All output files are automatically saved to the 'videos' folder
• Files are automatically opened when processing completes
• Full file paths are displayed in the processing log
• Supported input formats: MP4, MOV, MKV, WEBM
• Output formats: WAV (audio), MP4 (video)"""),
    
    ("💡 Tips & Troubleshooting", """• Ensure stable internet connection for YouTube downloads
• Close other audio/video applications during processing
• For best results, use videos with clear vocal tracks
• Processing requires significant CPU/GPU resources
• If processing fails, check the log for error details
• Temporary files are automatically cleaned up after processing"""),
    
    ("💻 System Requirements", """• Operating System: Windows 10+, macOS 10.14+, or Linux
• RAM: 8GB minimum, 16GB recommended
• Storage: 2GB free space per hour of video
• Internet: Required for YouTube downloads and model downloads
• Dependencies: Automatically managed (FFmpeg, yt-dlp, PyTorch)""")
]

for i, (section_title, section_content) in enumerate(help_sections):
    help_card = ctk.CTkFrame(
        help_content_frame,
        corner_radius=20,
        fg_color=colors["surface_elevated"],
        border_width=1,
        border_color=colors["border_light"]
    )
    help_card.pack(fill="x", pady=(0, 20), padx=20)
    
    card_title = ctk.CTkLabel(
        help_card, 
        text=section_title, 
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=colors["text_primary"]
    )
    card_title.pack(anchor="w", pady=(25, 15), padx=25)
    
    card_content = ctk.CTkLabel(
        help_card, 
        text=section_content, 
        font=ctk.CTkFont(size=15),
        text_color=colors["text_secondary"],
        justify="left",
        wraplength=750
    )
    card_content.pack(anchor="w", pady=(0, 25), padx=25)

if __name__ == "__main__":
    app.mainloop()