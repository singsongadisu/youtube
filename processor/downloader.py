import yt_dlp
import os
from pathlib import Path

class VideoDownloader:
    def __init__(self, download_path: str = "assets/downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)

    def get_video_info(self, url: str):
        """Fetches metadata and available formats for a video."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                formats = []
                for f in info.get('formats', []):
                    # Filter for useful formats (video+audio or best standalone)
                    if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                        formats.append({
                            'format_id': f.get('format_id'),
                            'extension': f.get('ext'),
                            'resolution': f.get('resolution') or f.get('format_note'),
                            'filesize': f.get('filesize') or f.get('filesize_approx'),
                            'vcodec': f.get('vcodec'),
                            'acodec': f.get('acodec'),
                            'fps': f.get('fps'),
                        })
                
                return {
                    'title': info.get('title'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'formats': formats,
                    'original_url': url
                }
            except Exception as e:
                print(f"Error fetching info: {e}")
                return {"error": str(e)}

    def download_video(self, url: str, format_id: str = None):
        """Downloads a video from a URL. Optionally specify a format_id."""
        ydl_opts = {
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
        }
        
        if format_id:
            ydl_opts['format'] = format_id
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # If merged, the extension might change
            if not os.path.exists(filename):
                # Try with common extensions
                for ext in ['mp4', 'mkv', 'webm']:
                    alt_name = os.path.splitext(filename)[0] + '.' + ext
                    if os.path.exists(alt_name):
                        filename = alt_name
                        break
            return filename

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
