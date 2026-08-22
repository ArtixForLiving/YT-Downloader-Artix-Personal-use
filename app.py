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

# --- KONFIGURASI VERSI & GITHUB ---
APP_VERSION = "v1.0"

GITHUB_REPO = "ArtixForLiving/YT-Downloader-Artix-Personal-Use"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Konfigurasi Tema UI
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GlassDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"YT Downloader for Artix {APP_VERSION}")
        self.geometry("680x500")

        self.configure(fg_color=("#F4F4F4", "#181818"))
        self.attributes("-alpha", 0.95)

        self.title_label = ctk.CTkLabel(self, text=f"YT Downloader for Artix {APP_VERSION}", font=("Segoe UI", 24, "bold"))
        self.title_label.pack(pady=(30, 10))

        # --- Input Link URL ---
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Tempelkan Link YouTube di sini...", width=500, height=40)
        self.url_entry.pack(pady=10)
        self.url_entry.bind("<KeyRelease>", self.reset_download_state)

        # --- Frame Opsi ---
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.pack(pady=15)

        self.type_var = ctk.StringVar(value="Video")
        self.type_menu = ctk.CTkOptionMenu(self.options_frame, values=["Video", "Audio (MP3)"], variable=self.type_var, command=self.toggle_options)
        self.type_menu.grid(row=0, column=0, padx=10)

        self.res_var = ctk.StringVar(value="1080p")
        self.res_menu = ctk.CTkOptionMenu(self.options_frame, values=["2160p", "1440p", "1080p", "720p", "480p"], variable=self.res_var)
        self.res_menu.grid(row=0, column=1, padx=10)

        self.fps_var = ctk.StringVar(value="60 FPS")
        self.fps_menu = ctk.CTkOptionMenu(self.options_frame, values=["60 FPS", "30 FPS"], variable=self.fps_var)
        self.fps_menu.grid(row=0, column=2, padx=10)

        self.audio_var = ctk.StringVar(value="192 kbps")
        self.audio_menu = ctk.CTkOptionMenu(self.options_frame, values=["320 kbps", "256 kbps", "192 kbps", "128 kbps"], variable=self.audio_var)

        # --- Progress bar & Status ---
        self.progress_bar = ctk.CTkProgressBar(self, width=500, height=10)
        self.progress_bar.pack(pady=(20, 10))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="Wajib: Klik 'Cek Link' sebelum mengunduh!", text_color="gray")
        self.status_label.pack(pady=5)

        # --- FRAME TOMBOL AKSI ---
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(pady=15)

        self.check_btn = ctk.CTkButton(self.action_frame, text="Cek Link", font=("Segoe UI", 14, "bold"), height=40, command=self.start_check_link)
        self.check_btn.grid(row=0, column=0, padx=10)

        self.download_btn = ctk.CTkButton(self.action_frame, text="Download Sekarang", font=("Segoe UI", 14, "bold"), height=40, state="disabled", command=self.ask_location_and_download)
        self.download_btn.grid(row=0, column=1, padx=10)

        # --- TOMBOL CEK UPDATE (Kiri Bawah) ---
        self.update_btn = ctk.CTkButton(
            self, 
            text="Cek Update", 
            width=100, 
            height=28, 
            fg_color="transparent", 
            border_width=1, 
            text_color=("black", "white"),
            command=self.start_check_update
        )
        self.update_btn.place(relx=0.05, rely=0.95, anchor="sw")

        # --- Switch Dark/Light Mode (Kanan Bawah) ---
        self.switch_var = ctk.StringVar(value="on")
        self.theme_switch = ctk.CTkSwitch(self, text="Dark Mode", variable=self.switch_var, onvalue="on", offvalue="off", command=self.toggle_theme)
        self.theme_switch.place(relx=0.95, rely=0.95, anchor="se")

    def toggle_theme(self):
        if self.switch_var.get() == "on":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def toggle_options(self, choice):
        if choice == "Audio (MP3)":
            self.res_menu.grid_forget()
            self.fps_menu.grid_forget()
            self.audio_menu.grid(row=0, column=1, padx=10)
        else:
            self.audio_menu.grid_forget()
            self.res_menu.grid(row=0, column=1, padx=10)
            self.fps_menu.grid(row=0, column=2, padx=10)

    def reset_download_state(self, event):
        self.download_btn.configure(state="disabled")
        self.status_label.configure(text="Link diubah. Silakan klik 'Cek Link' lagi.")

    # ==========================================
    # FITUR AUTO-UPDATER
    # ==========================================
    def start_check_update(self):
        self.status_label.configure(text="Mengecek pembaruan ke server...")
        self.update_btn.configure(state="disabled")
        threading.Thread(target=self.process_update, daemon=True).start()

    def process_update(self):
        try:
            # Meminta data rilis terbaru dari API GitHub
            req = urllib.request.Request(GITHUB_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
            latest_version = data.get('tag_name', '')
            
            # Jika versi di GitHub BEDA dari versi di aplikasi ini
            if latest_version and latest_version != APP_VERSION:
                self.status_label.configure(text=f"Versi {latest_version} tersedia! Mengunduh installer...")
                
                # Cari link file .exe di daftar lampiran (assets) GitHub
                download_url = ""
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.exe'):
                        download_url = asset['browser_download_url']
                        break
                        
                if download_url:
                    # Simpan installer ke folder Downloads PC pengguna
                    downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
                    installer_path = os.path.join(downloads_folder, f"Update_YTDownloader_{latest_version}.exe")
                    
                    # Mengunduh file
                    urllib.request.urlretrieve(download_url, installer_path)
                    
                    self.status_label.configure(text="Unduhan selesai! Membuka installer...")
                    
                    # Eksekusi installer dan tutup aplikasi agar bisa ditimpa
                    if os.name == 'nt':  # Khusus Windows
                        os.startfile(installer_path)
                    else:  # Khusus Linux
                        subprocess.call(['xdg-open', installer_path])
                        
                    self.destroy()
                    sys.exit()
                else:
                    self.status_label.configure(text="Gagal! File installer (.exe) tidak ditemukan di server.")
            else:
                self.status_label.configure(text="Aplikasi kamu sudah versi yang paling baru!")
        except Exception as e:
            self.status_label.configure(text="Gagal terhubung ke server update. Coba lagi nanti.")
        finally:
            self.update_btn.configure(state="normal")
            
    # ==========================================

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
                self.download_btn.configure(state="normal")
        except Exception as e:
            self.status_label.configure(text="Gagal membaca link. Pastikan link YouTube valid.")
        finally:
            self.check_btn.configure(state="normal")

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
            except Exception as e:
                self.status_label.configure(text="Mengunduh... Harap tunggu.")
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
            
        except Exception as e:
            self.status_label.configure(text="Error saat mengunduh. Coba klik 'Cek Update'.")
        finally:
            self.download_btn.configure(text="Download Sekarang", state="normal")
            self.check_btn.configure(state="normal")

if __name__ == "__main__":
    app = GlassDownloader()
    app.mainloop()