import asyncio
import json
import os
import re
import urllib.request
import threading
import sys
import subprocess
import time
import webview
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

APP_VERSION = "v1.2"
GITHUB_REPO = "ArtixForLiving/YT-Downloader-Artix-Personal-use"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def parse_version(v_str: str) -> tuple:
    try:
        return tuple(map(int, re.findall(r'\d+', v_str)))
    except Exception:
        return (0,)

@app.get("/api/info")
async def get_video_info(url: str = Query(...)):
    try:
        ydl_opts = {'quiet': True, 'nocheckcertificate': True}
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False))
        
        formats = info.get('formats', [])
        duration = info.get('duration', 0)
        
        a_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
        base_a_size = 0
        if a_formats:
            best_a = a_formats[-1]
            base_a_size = best_a.get('filesize') or best_a.get('filesize_approx') or 0
            if base_a_size == 0 and best_a.get('abr') and duration:
                base_a_size = (best_a.get('abr') * 1000 * duration) / 8

        available_res = []
        video_sizes = {}
        for r in [2160, 1440, 1080, 720, 480]:
            v_formats = [f for f in formats if f.get('height') == r and f.get('vcodec') != 'none']
            if v_formats:
                res_label = f"{r}p"
                available_res.append(res_label)
                best_v = v_formats[-1]
                v_size = best_v.get('filesize') or best_v.get('filesize_approx') or 0
                if v_size == 0 and best_v.get('vbr') and duration:
                    v_size = (best_v.get('vbr') * 1000 * duration) / 8
                total_bytes = v_size + base_a_size
                video_sizes[res_label] = f"{(total_bytes / (1024 * 1024)):.1f} MB" if total_bytes > 0 else "Tidak diketahui"

        audio_sizes = {}
        for bitrate in [320, 256, 192, 128]:
            audio_bytes = (bitrate * 1000 * duration) / 8 if duration > 0 else 0
            audio_sizes[f"{bitrate} kbps"] = f"{(audio_bytes / (1024 * 1024)):.1f} MB" if audio_bytes > 0 else "Tidak diketahui"

        mins, secs = divmod(duration, 60)
        return {
            "status": "success", "title": info.get('title', 'Unknown'), "channel": info.get('uploader', 'Unknown'),
            "duration": f"{mins}:{secs:02d}", "available_resolutions": available_res or ["1080p"],
            "estimations": {"video": video_sizes, "audio": audio_sizes}
        }
    except Exception as e:
        return {"status": "error", "message": "Gagal membaca link."}

@app.get("/api/check-update")
async def check_update():
    try:
        req = urllib.request.Request(GITHUB_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: json.loads(urllib.request.urlopen(req).read().decode()))
        latest_version = data.get('tag_name', '')

        if latest_version and parse_version(latest_version) > parse_version(APP_VERSION):
            download_url = next((asset['browser_download_url'] for asset in data.get('assets', []) if asset['name'].endswith('.exe')), "")
            return {"update_available": True, "current_version": APP_VERSION, "latest_version": latest_version, "download_url": download_url}
        return {"update_available": False, "current_version": APP_VERSION, "latest_version": latest_version}
    except Exception:
        return {"status": "error", "message": "Gagal terhubung ke GitHub."}

@app.get("/api/do-update")
async def do_update(url: str = Query(...), version: str = Query(...)):
    try:
        downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
        installer_path = os.path.join(downloads_folder, f"Update_YTDownloader_{version}.exe")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: urllib.request.urlretrieve(url, installer_path))
        
        if os.name == 'nt':
            os.startfile(installer_path)
        else:
            subprocess.call(['xdg-open', installer_path])
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.websocket("/ws/download")
async def websocket_download(websocket: WebSocket):
    await websocket.accept()
    try:
        data = json.loads(await websocket.receive_text())
        url, dl_type = data.get("url"), data.get("type")
        res = data.get("resolution", "1080").replace("p", "").replace(" kbps", "")
        
        save_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        out_template = os.path.join(save_path, '%(title)s.%(ext)s')
        loop = asyncio.get_event_loop()

        def progress_hook(d):
            if d['status'] == 'downloading':
                p = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0%')).strip()
                s = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_speed_str', '0KiB/s')).strip()
                asyncio.run_coroutine_threadsafe(websocket.send_json({"status": "downloading", "progress": p, "speed": s}), loop)
            elif d['status'] == 'finished':
                asyncio.run_coroutine_threadsafe(websocket.send_json({"status": "merging", "message": "Menggabungkan file (FFmpeg)..."}), loop)

        ydl_opts = {'outtmpl': out_template, 'progress_hooks': [progress_hook], 'quiet': True, 'nocheckcertificate': True}
        if dl_type == "Video":
            ydl_opts.update({'format': f'bestvideo[height<={res}]+bestaudio/best', 'merge_output_format': 'mp4'})
        else:
            ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': res}]})

        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        await websocket.send_json({"status": "completed"})
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})
    finally:
        await websocket.close()

def start_api():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == '__main__':
    threading.Thread(target=start_api, daemon=True).start()
    
    time.sleep(1.5)
    
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    html_path = os.path.join(base_dir, "frontend_dist", "index.html")
    webview.create_window('YT Downloader for Me', html_path, width=720, height=580, resizable=False)
    webview.start()