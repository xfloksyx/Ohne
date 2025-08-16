"""
Dependency Manager for Ohne - Only Vocals
Handles finding and managing external tools (demucs, ffmpeg, yt-dlp)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import urllib.request
import zipfile
import platform

class DependencyManager:
    def __init__(self):
        self.app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        self.tools_dir = self.app_dir / "tools"
        self.tools_dir.mkdir(exist_ok=True)
        
        # Tool configurations
        self.tools = {
            'yt-dlp': {
                'executable': 'yt-dlp.exe' if platform.system() == 'Windows' else 'yt-dlp',
                'download_url': 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe',
                'version_check': ['--version']
            },
            'ffmpeg': {
                'executable': 'ffmpeg.exe' if platform.system() == 'Windows' else 'ffmpeg',
                'download_url': 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
                'version_check': ['-version']
            }
        }
    
    def find_tool(self, tool_name):
        """Find tool in multiple locations"""
        tool_config = self.tools.get(tool_name, {})
        executable = tool_config.get('executable', tool_name)
        
        # Search locations in order of preference
        search_paths = [
            # 1. Bundled with app
            self.tools_dir / executable,
            # 2. Same directory as app
            self.app_dir / executable,
            # 3. System PATH
            shutil.which(executable),
            # 4. Common installation paths
            Path("C:/Program Files/ffmpeg/bin") / executable if platform.system() == 'Windows' else None,
            Path("C:/ffmpeg/bin") / executable if platform.system() == 'Windows' else None,
            Path("/usr/local/bin") / executable if platform.system() != 'Windows' else None,
            Path("/usr/bin") / executable if platform.system() != 'Windows' else None,
        ]
        
        for path in search_paths:
            if path and Path(path).exists() and Path(path).is_file():
                return str(path)
        
        return None
    
    def check_tool(self, tool_name):
        """Check if tool is available and working"""
        tool_path = self.find_tool(tool_name)
        if not tool_path:
            return False, f"{tool_name} not found"
        
        try:
            tool_config = self.tools.get(tool_name, {})
            version_check = tool_config.get('version_check', ['--version'])
            
            result = subprocess.run(
                [tool_path] + version_check,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, f"{tool_name} found at {tool_path}"
            else:
                return False, f"{tool_name} found but not working properly"
                
        except Exception as e:
            return False, f"Error checking {tool_name}: {str(e)}"
    
    def download_tool(self, tool_name, progress_callback=None):
        """Download and install a tool"""
        if tool_name not in self.tools:
            return False, f"Unknown tool: {tool_name}"
        
        tool_config = self.tools[tool_name]
        download_url = tool_config['download_url']
        executable = tool_config['executable']
        
        try:
            if progress_callback:
                progress_callback(f"Downloading {tool_name}...")
            
            # Download to temporary file
            temp_file = self.tools_dir / f"temp_{executable}"
            urllib.request.urlretrieve(download_url, temp_file)
            
            if tool_name == 'ffmpeg' and download_url.endswith('.zip'):
                # Extract FFmpeg from zip
                with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                    # Find ffmpeg.exe in the zip
                    for file_info in zip_ref.filelist:
                        if file_info.filename.endswith('ffmpeg.exe'):
                            # Extract just the ffmpeg.exe file
                            with zip_ref.open(file_info) as source:
                                with open(self.tools_dir / executable, 'wb') as target:
                                    target.write(source.read())
                            break
                temp_file.unlink()  # Remove zip file
            else:
                # Move downloaded file to final location
                final_path = self.tools_dir / executable
                temp_file.rename(final_path)
                
                # Make executable on Unix systems
                if platform.system() != 'Windows':
                    os.chmod(final_path, 0o755)
            
            if progress_callback:
                progress_callback(f"{tool_name} downloaded successfully!")
            
            return True, f"{tool_name} installed successfully"
            
        except Exception as e:
            return False, f"Failed to download {tool_name}: {str(e)}"
    
    def get_tool_command(self, tool_name):
        """Get the full command path for a tool"""
        tool_path = self.find_tool(tool_name)
        if tool_path:
            return [tool_path]
        else:
            # Return the tool name as fallback (might work if in PATH)
            return [tool_name]
    
    def check_all_dependencies(self):
        """Check all required dependencies"""
        results = {}
        missing_tools = []
        
        # Check Python packages
        python_packages = ['customtkinter', 'Pillow', 'pathlib']
        for package in python_packages:
            try:
                __import__(package)
                results[package] = (True, f"{package} available")
            except ImportError:
                results[package] = (False, f"{package} not installed")
        
        # Check external tools
        for tool_name in ['yt-dlp', 'ffmpeg']:
            is_available, message = self.check_tool(tool_name)
            results[tool_name] = (is_available, message)
            if not is_available:
                missing_tools.append(tool_name)
        
        # Check for demucs (Python package)
        try:
            import demucs
            results['demucs'] = (True, "demucs Python package available")
        except ImportError:
            results['demucs'] = (False, "demucs not installed - will be installed automatically on first use")
        
        return results, missing_tools
    
    def install_missing_dependencies(self, missing_tools, progress_callback=None):
        """Install missing dependencies"""
        success_count = 0
        
        for tool in missing_tools:
            if tool in self.tools:
                success, message = self.download_tool(tool, progress_callback)
                if success:
                    success_count += 1
                if progress_callback:
                    progress_callback(message)
        
        # Install demucs if missing
        try:
            import demucs
        except ImportError:
            if progress_callback:
                progress_callback("Installing demucs Python package...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'demucs'])
                if progress_callback:
                    progress_callback("demucs installed successfully!")
                success_count += 1
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Failed to install demucs: {str(e)}")
        
        return success_count

# Global instance
dependency_manager = DependencyManager()
