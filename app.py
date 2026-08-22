import customtkinter as ctk
from customtkinter import filedialog
import yt_dlp
import threading
import os
import re
import urllib.request
import json
import sys
import subprocess

APP_VERSION = "v1.1"
GITHUB_REPO = "ArtixForLiving/YT-Downloader-Artix-Personal-use"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GlassDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        #
        self.title(f"YT Downloader for Me {APP_VERSION}")
        self.geometry("720x550")
        self.minsize(680, 500) 

        self.configure(fg_color=("#F4F4F4", "#181818"))
        
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=40, pady=20)

        #
        self.title_label = ctk.CTkLabel(self.main_frame, text=f"YT Downloader for Me", font=("Segoe UI", 28, "bold"), text_color=("black", "white"))
        self.title_label.pack(pady=(10, 20))

        # Input Link URL 
        self.url_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Tempelkan Link YouTube di sini...", height=45, corner_radius=10, font=("Segoe UI", 13, "bold"))
        self.url_entry.pack(fill="x", pady=10) 
        self.url_entry.bind("<KeyRelease>", self.reset_download_state)

        #  Frame Opsi 
        self.options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.options_frame.pack(pady=15)

        self.type_var = ctk.StringVar(value="Video")
        self.type_menu = ctk.CTkOptionMenu(self.options_frame, values=["Video", "Audio (MP3)"], variable=self.type_var, command=self.toggle_options, corner_radius=8, font=("Segoe UI", 13, "bold"))
        self.type_menu.grid(row=0, column=0, padx=10)

        self.res_var = ctk.StringVar(value="1080p")
        self.res_menu = ctk.CTkOptionMenu(self.options_frame, values=["2160p", "1440p", "1080p", "720p", "480p"], variable=self.res_var, command=self.update_estimation, corner_radius=8, font=("Segoe UI", 13, "bold"))
        self.res_menu.grid(row=0, column=1, padx=10)

        self.fps_var = ctk.StringVar(value="60 FPS")
        self.fps_menu = ctk.CTkOptionMenu(self.options_frame, values=["60 FPS", "30 FPS"], variable=self.fps_var, corner_radius=8, font=("Segoe UI", 13, "bold"))
        self.fps_menu.grid(row=0, column=2, padx=10)

        self.audio_var = ctk.StringVar(value="192 kbps")
        self.audio_menu = ctk.CTkOptionMenu(self.options_frame, values=["320 kbps", "256 kbps", "192 kbps", "128 kbps"], variable=self.audio_var, corner_radius=8, font=("Segoe UI", 13, "bold"))

        #  LABEL ESTIMASI UKURAN FILE (Font Bold & Adaptif) 
        self.size_label = ctk.CTkLabel(self.main_frame, text="Estimasi Ukuran: -", font=("Segoe UI", 13, "bold"), text_color=("#444444", "#DDDDDD"))
        self.size_label.pack(pady=5)

        #  Progress bar & Status 
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, height=12, corner_radius=10)
        self.progress_bar.pack(fill="x", pady=(15, 10))
        self.progress_bar.set(0)

        # Font Bold & Teks lebih kontras (Hitam pekat di Light, Putih cerah di Dark)
        self.status_label = ctk.CTkLabel(self.main_frame, text="Wajib: Klik 'Cek Link' sebelum mengunduh!", font=("Segoe UI", 14, "bold"), text_color=("#222222", "#EEEEEE"))
        self.status_label.pack(pady=5)

        # FRAME TOMBOL AKSI (Modern) 
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.action_frame.pack(pady=20)

        # Menghapus warna hijau, kembali ke biru default CustomTkinter
        self.check_btn = ctk.CTkButton(self.action_frame, text="Cek Link", font=("Segoe UI", 14, "bold"), height=45, width=140, corner_radius=10, command=self.start_check_link)
        self.check_btn.grid(row=0, column=0, padx=15)

        self.download_btn = ctk.CTkButton(self.action_frame, text="Download Sekarang", font=("Segoe UI", 14, "bold"), height=45, width=180, corner_radius=10, state="disabled", command=self.ask_location_and_download)
        self.download_btn.grid(row=0, column=1, padx=15)

        # TOMBOL BAWAH 
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(fill="x", side="bottom", padx=20, pady=15)

        self.update_btn = ctk.CTkButton(self.bottom_frame, text="Cek Update", width=100, height=30, fg_color="transparent", border_width=1, corner_radius=8, font=("Segoe UI", 12, "bold"), text_color=("black", "white"), command=self.start_check_update)
        self.update_btn.pack(side="left")

        self.switch_var = ctk.StringVar(value="on")
        self.theme_switch = ctk.CTkSwitch(self.bottom_frame, text="Dark Mode", font=("Segoe UI", 12, "bold"), variable=self.switch_var, onvalue="on", offvalue="off", command=self.toggle_theme)
        self.theme_switch.pack(side="right")
        
        self.current_video_info = None 

    def toggle_theme(self):
        ctk.set_appearance_mode("Dark" if self.switch_var.get() == "on" else "Light")

    def toggle_options(self, choice):
        if choice == "Audio (MP3)":
            self.res_menu.grid_forget()
            self.fps_menu.grid_forget()
            self.audio_menu.grid(row=0, column=1, padx=10)
        else:
            self.audio_menu.grid_forget()
            self.res_menu.grid(row=0, column=1, padx=10)
            self.fps_menu.grid(row=0, column=2, padx=10)
        self.update_estimation()

    def reset_download_state(self, event):
        self.download_btn.configure(state="disabled")
        self.status_label.configure(text="Link diubah. Silakan klik 'Cek Link' lagi.")
        self.size_label.configure(text="Estimasi Ukuran: -")
        self.current_video_info = None

    def start_check_update(self):
        self.status_label.configure(text="Mengecek pembaruan ke server...")
        self.update_btn.configure(state="disabled")
        threading.Thread(target=self.process_update, daemon=True).start()

    def process_update(self):
        try:
            req = urllib.request.Request(GITHUB_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
            latest_version = data.get('tag_name', '')
            if latest_version and latest_version != APP_VERSION:
                self.status_label.configure(text=f"Versi {latest_version} tersedia! Mengunduh installer...")
                download_url = ""
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.exe'):
                        download_url = asset['browser_download_url']
                        break
                        
                if download_url:
                    downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
                    installer_path = os.path.join(downloads_folder, f"Update_YTDownloader_{latest_version}.exe")
                    urllib.request.urlretrieve(download_url, installer_path)
                    self.status_label.configure(text="Unduhan selesai! Membuka installer...")
                    if os.name == 'nt':
                        os.startfile(installer_path)
                    else:
                        subprocess.call(['xdg-open', installer_path])
                    self.destroy()
                    sys.exit()
                else:
                    self.status_label.configure(text="Gagal! File installer tidak ditemukan.")
            else:
                self.status_label.configure(text="Aplikasi kamu sudah versi yang paling baru!")
        except Exception:
            self.status_label.configure(text="Gagal terhubung ke server update.")
        finally:
            self.update_btn.configure(state="normal")

    def start_check_link(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_label.configure(text="Link tidak boleh kosong!")
            return
        
        self.status_label.configure(text="Mengecek info ke YouTube...")
        self.check_btn.configure(state="disabled")
        self.download_btn.configure(state="disabled")
        threading.Thread(target=self.fetch_video_info, args=(url,), daemon=True).start()

    def fetch_video_info(self, url):
        try:
            ydl_opts = {'quiet': True, 'nocheckcertificate': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.current_video_info = info
                
                formats = info.get('formats', [])
                resolutions = [f.get('height') for f in formats if f.get('height') is not None]
                max_res = max(resolutions) if resolutions else 1080
                
                available_res = []
                for r in [2160, 1440, 1080, 720, 480]:
                    if r <= max_res:
                        available_res.append(f"{r}p")
                
                if available_res:
                    self.res_menu.configure(values=available_res)
                    self.res_var.set(available_res[0]) 

                self.status_label.configure(text=f"Media siap: {info.get('title', 'Ditemukan')}")
                self.update_estimation()
                self.download_btn.configure(state="normal")
        except Exception:
            self.status_label.configure(text="Gagal membaca link. Pastikan link valid.")
        finally:
            self.check_btn.configure(state="normal")

    def update_estimation(self, *args):
        if not self.current_video_info:
            return
            
        try:
            formats = self.current_video_info.get('formats', [])
            total_bytes = 0
            
            if self.type_var.get() == "Video":
                target_res = int(self.res_var.get().replace('p', ''))
                v_formats = [f for f in formats if f.get('height') == target_res and f.get('vcodec') != 'none']
                a_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                
                if v_formats:
                    v_size = v_formats[-1].get('filesize') or v_formats[-1].get('filesize_approx') or 0
                    total_bytes += v_size
                if a_formats:
                    a_size = a_formats[-1].get('filesize') or a_formats[-1].get('filesize_approx') or 0
                    total_bytes += a_size
            else:
                a_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                if a_formats:
                    total_bytes = a_formats[-1].get('filesize') or a_formats[-1].get('filesize_approx') or 0

            if total_bytes > 0:
                mb = total_bytes / (1024 * 1024)
                self.size_label.configure(text=f"Estimasi Ukuran: ~{mb:.1f} MB")
            else:
                self.size_label.configure(text="Estimasi Ukuran: Tidak dapat diprediksi")
        except:
            self.size_label.configure(text="Estimasi Ukuran: Tidak diketahui")

    def ask_location_and_download(self):
        save_path = filedialog.askdirectory(title="Pilih Lokasi Penyimpanan")
        if not save_path:
            return  

        self.download_btn.configure(text="Mengunduh...", state="disabled")
        self.check_btn.configure(state="disabled")
        self.progress_bar.set(0)
        
        threading.Thread(target=self.download_process, args=(save_path,), daemon=True).start()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0%')
                speed_str = d.get('_speed_str', '0KiB/s')
                clean_percent = re.sub(r'\x1b\[[0-9;]*m', '', percent_str).strip()
                clean_speed = re.sub(r'\x1b\[[0-9;]*m', '', speed_str).strip()
                p_val = float(clean_percent.replace('%', '').strip())
                self.progress_bar.set(p_val / 100.0)
                self.status_label.configure(text=f"Proses: {clean_percent}  |  Kecepatan: {clean_speed}")
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.status_label.configure(text="Proses penggabungan (FFmpeg)... Harap tunggu.")
            self.progress_bar.set(1.0)

    def download_process(self, save_path):
        url = self.url_entry.get().strip()
        download_type = self.type_var.get()
        out_template = os.path.join(save_path, '%(title)s.%(ext)s')

        ydl_opts = {
            'outtmpl': out_template,
            'progress_hooks': [self.progress_hook],
            'quiet': True,
            'nocheckcertificate': True,
            'color': 'no_color',
        }

        if download_type == "Video":
            res = self.res_var.get().replace('p', '')
            fps = self.fps_var.get().replace(' FPS', '')
            ydl_opts['format'] = f'bestvideo[height<={res}][fps<={fps}][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<={res}][fps<={fps}]+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'
        else:
            bitrate = self.audio_var.get().replace(' kbps', '')
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': bitrate,
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            media_type = "Audio" if download_type == "Audio (MP3)" else "Video"
            self.status_label.configure(text=f"Selesai! {media_type} berhasil disimpan.")
        except Exception:
            self.status_label.configure(text="Error saat mengunduh. Coba klik 'Cek Update'.")
        finally:
            self.download_btn.configure(text="Download Sekarang", state="normal")
            self.check_btn.configure(state="normal")

if __name__ == "__main__":
    app = GlassDownloader()
    app.mainloop()
