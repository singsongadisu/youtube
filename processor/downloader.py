import yt_dlp
import os
from pathlib import Path

class VideoDownloader:
    def __init__(self, download_path: str = "assets/downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)

    def download_video(self, url: str):
        """Downloads the best quality video from a URL."""
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    def download_audio(self, url: str):
        """Downloads only the audio from a URL as mp3."""
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # yt-dlp might change the extension to mp3 after post-processing
            filename = ydl.prepare_filename(info)
            return str(Path(filename).with_suffix('.mp3'))

if __name__ == "__main__":
    downloader = VideoDownloader()
    # Example usage (commented out to avoid accidental runs)
    # downloader.download_audio("YOUR_URL_HERE")
