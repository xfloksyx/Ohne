# Ohne - Only Vocals
## Professional Audio Extraction Software

**Version 1.0**  
**Developer:** Marouane El Hizabri  
**Website:** [ohne.space](https://ohne.space)  
**LinkedIn:** [linkedin.com/in/marouaneelhizabri](https://linkedin.com/in/marouaneelhizabri)

---

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation Guide](#installation-guide)
4. [Quick Start Guide](#quick-start-guide)
5. [Detailed User Manual](#detailed-user-manual)
6. [Troubleshooting](#troubleshooting)
7. [Technical Specifications](#technical-specifications)
8. [Support & Contact](#support--contact)
9. [License & Credits](#license--credits)

---

## Overview

**Ohne - Only Vocals** is a professional-grade desktop application designed for high-quality vocal extraction and audio processing. Powered by advanced AI technology using the Demucs neural network, this software provides studio-quality vocal isolation from any audio or video source.

### Key Features

- **AI-Powered Vocal Extraction**: Utilizes state-of-the-art Demucs neural network for superior audio separation
- **YouTube Integration**: Direct processing from YouTube URLs with automatic download
- **Local File Support**: Process local video files (MP4, MOV, MKV, WEBM formats)
- **Dual Output Modes**: Extract vocals only (WAV) or merge vocals with original video (MP4)
- **Real-Time Progress Tracking**: Live progress monitoring during processing
- **Professional Interface**: Modern, intuitive design with dark theme
- **Batch Processing Ready**: Efficient workflow for multiple files
- **High-Quality Output**: Maintains original audio fidelity during processing

---

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux Ubuntu 18.04+
- **RAM**: 8 GB (16 GB recommended for large files)
- **Storage**: 5 GB free space (additional space needed for processing)
- **Internet**: Required for YouTube downloads and initial setup

### Recommended Specifications
- **RAM**: 16 GB or higher
- **Storage**: SSD with 20+ GB free space
- **CPU**: Multi-core processor (Intel i5/AMD Ryzen 5 or better)
- **GPU**: CUDA-compatible GPU (optional, for faster processing)

### Dependencies
The following components are automatically installed:
- Python 3.8+
- FFmpeg
- yt-dlp
- Demucs AI model
- CustomTkinter GUI framework

---

## Installation Guide

### Windows Installation

1. **Download the Installer**
   - Download `Ohne-Setup.exe` from the official website
   - Ensure you have administrator privileges

2. **Run the Installer**
   - Double-click the installer file
   - Follow the installation wizard prompts
   - Choose installation directory (default recommended)
   - Allow firewall permissions if prompted

3. **First Launch**
   - Launch from Desktop shortcut or Start Menu
   - Initial setup will download required AI models (may take 5-10 minutes)
   - Application is ready to use once setup completes

### macOS Installation

1. **Download the Package**
   - Download `Ohne.dmg` from the official website
   - Open the DMG file

2. **Install the Application**
   - Drag "Ohne" to Applications folder
   - Right-click and select "Open" for first launch (security requirement)
   - Allow necessary permissions in System Preferences

3. **Initial Setup**
   - First launch will install dependencies
   - Grant microphone access if prompted
   - Wait for AI model download to complete

### Linux Installation

1. **Download the Package**
   - Download `ohne-linux.tar.gz`
   - Extract to desired location

2. **Install Dependencies**
   \`\`\`bash
   sudo apt update
   sudo apt install python3 python3-pip ffmpeg
   \`\`\`

3. **Run the Application**
   \`\`\`bash
   cd ohne-linux
   chmod +x ohne
   ./ohne
   \`\`\`

---

## Quick Start Guide

### Processing a YouTube Video

1. **Launch Ohne - Only Vocals**
2. **Navigate to Main Tab** (default view)
3. **Enter YouTube URL**
   - Paste the YouTube video URL in the "YouTube URL" field
   - Example: `https://youtube.com/watch?v=example`
4. **Set Output Name**
   - Enter desired filename in "Output filename" field
   - Do not include file extension
5. **Choose Processing Mode**
   - **Extract Vocals Only**: Creates WAV audio file with isolated vocals
   - **Merge with Video**: Creates MP4 video with vocals over original video
6. **Start Processing**
   - Click "Start Processing" button
   - Monitor progress in the console log
   - Processing time varies based on video length (typically 2-5 minutes per minute of audio)

### Processing a Local File

1. **Select Local File**
   - Click "Select Local File" button
   - Choose video file (MP4, MOV, MKV, WEBM)
   - Selected filename will appear next to button
2. **Follow steps 4-6 from YouTube processing**

---

## Detailed User Manual

### Interface Overview

The application features a modern tabbed interface with three main sections:

#### Main Tab
- **YouTube URL Input**: Text field for YouTube video links
- **Local File Selection**: Button to browse and select local video files
- **Output Filename**: Custom name for processed files
- **Processing Options**: Radio buttons for output format selection
- **Control Buttons**: Start processing and clear logs
- **Progress Console**: Real-time processing status and progress bars

#### About Tab
- Application information and version details
- Feature overview and technical specifications
- Developer contact information

#### Help Tab
- Comprehensive usage instructions
- Supported formats and troubleshooting tips
- Step-by-step processing guides

### Processing Modes Explained

#### Extract Vocals Only (WAV)
- **Output**: High-quality WAV audio file containing isolated vocals
- **Use Case**: Perfect for karaoke tracks, vocal analysis, or remixing
- **Quality**: 44.1kHz/16-bit or higher, depending on source
- **File Size**: Typically 10-50 MB for a 3-4 minute song

#### Merge with Video (MP4)
- **Output**: MP4 video file with extracted vocals over original video
- **Use Case**: Creating vocal-only versions of music videos
- **Quality**: Maintains original video resolution and framerate
- **File Size**: Similar to original video file

### Advanced Features

#### Progress Monitoring
- Real-time progress bars show processing status
- Detailed logging of each processing stage
- Estimated time remaining for long processes

#### File Management
- Automatic output folder organization
- Temporary file cleanup after processing
- Conflict resolution for existing files

#### Error Handling
- Comprehensive error reporting
- Automatic retry for network issues
- Graceful handling of unsupported formats

---

## Troubleshooting

### Common Issues and Solutions

#### "Failed to download video"
- **Cause**: Network connectivity or invalid URL
- **Solution**: 
  - Check internet connection
  - Verify YouTube URL is correct and video is publicly available
  - Try again after a few minutes

#### "Processing failed during vocal extraction"
- **Cause**: Insufficient memory or corrupted audio
- **Solution**:
  - Close other applications to free memory
  - Try processing a shorter video segment
  - Restart the application

#### "Output file not found"
- **Cause**: Processing interrupted or insufficient disk space
- **Solution**:
  - Ensure adequate free disk space (at least 2GB)
  - Check if antivirus software is blocking file creation
  - Run application as administrator (Windows)

#### Slow Processing Speed
- **Optimization Tips**:
  - Close unnecessary applications
  - Process shorter video segments
  - Ensure adequate RAM availability
  - Use SSD storage for better performance

### Performance Optimization

#### For Best Results
- **RAM**: 16GB+ recommended for videos longer than 10 minutes
- **Storage**: Use SSD for temporary files and output
- **CPU**: Multi-core processors significantly improve processing speed
- **Network**: Stable internet connection for YouTube downloads

#### Processing Time Estimates
- **Short videos (3-5 minutes)**: 2-4 minutes processing time
- **Medium videos (10-15 minutes)**: 8-15 minutes processing time
- **Long videos (30+ minutes)**: 25-45 minutes processing time

---

## Technical Specifications

### Audio Processing
- **AI Model**: Demucs v4 (state-of-the-art source separation)
- **Sample Rate**: Up to 48kHz
- **Bit Depth**: 16-bit and 24-bit support
- **Channels**: Stereo processing with mono compatibility

### Video Processing
- **Input Formats**: MP4, MOV, MKV, WEBM, AVI
- **Output Formats**: MP4 (H.264), WAV (PCM)
- **Resolution Support**: Up to 4K (3840x2160)
- **Frame Rates**: 24fps, 30fps, 60fps

### Network Features
- **YouTube Support**: Full compatibility with YouTube URLs
- **Download Quality**: Automatic best quality selection
- **Bandwidth Optimization**: Efficient streaming and caching

---

## Support & Contact

### Developer Information
**Marouane El Hizabri**  
 Software Developer

### Contact Methods
- **Website**: [ohne.space](https://ohne.space)
- **LinkedIn**: [linkedin.com/in/marouaneelhizabri](https://linkedin.com/in/marouaneelhizabri)
- **Email**: Available through website contact form

### Support Resources
- **Documentation**: Complete user guides and tutorials
- **Updates**: Regular software updates and improvements
- **Community**: User forums and discussion groups

### Business Inquiries
For licensing, custom development, or enterprise solutions, please contact through the official website.

---

## License & Credits

### Software License
Ohne - Only Vocals is proprietary software developed by Marouane El Hizabri. All rights reserved.

### Third-Party Components
- **Demucs**: META Research (MIT License)
- **FFmpeg**: FFmpeg team (LGPL/GPL)
- **yt-dlp**: Community-driven project (Unlicense)
- **CustomTkinter**: Tom Schimansky (MIT License)

### Acknowledgments
Special thanks to the open-source community for providing the foundational technologies that make this software possible.

### Copyright Notice
© 2025 Marouane El Hizabri. All rights reserved. Ohne - Only Vocals and all related marks are trademarks of Marouane El Hizabri.

---

**End of Documentation**

*For the latest updates and additional resources, visit [ohne.space](https://ohne.space)*

