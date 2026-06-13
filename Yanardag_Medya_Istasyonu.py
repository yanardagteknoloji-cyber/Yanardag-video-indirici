import os
import subprocess
import urllib.request
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import zipfile
import re
import webbrowser

class Yanardag_download_tool:
    def __init__(self, root):
        self.root = root
        self.root.title("Yanardağ Medya İstasyonu")
        self.root.geometry("680x860")
        self.root.configure(bg="#050505")
        self.lang = "TR"
        self.quality_var = tk.StringVar(value="best")

        self.working_dir = r"C:\Yanardag_Sistem"
        self.support_url = "http://yanardag.free.nf"
        self.ytdlp_path = os.path.join(self.working_dir, "yt-dlp.exe")
        self.ffmpeg_dir = os.path.join(self.working_dir, "ffmpeg")
        self.ffmpeg_bin = os.path.join(self.ffmpeg_dir, "bin")

        self.v_formats = ["mp4", "mov", "avi", "mkv", "webm", "wmv", "flv"]
        self.a_formats = ["mp3", "aac", "ogg", "flac", "wav", "alac", "aiff", "m4a", "wma"]

        self.texts = {
            "TR": {
                "title": "YANARDAĞ OTONOM SİSTEM",
                "label": "Video/Ses Linkini Girin:",
                "ai_badge": "Bu uygulama Bypass AI ile güçlendirilmiştir",
                "quality_label": "Kalite:",
                "v_sec": "VİDEO (Masaüstü/My Videos)",
                "a_sec": "SES (Masaüstü/My Music)",
                "lang_btn": "Dil: TR",
                "support_btn": "Destek & Hata Bildir",
                "status_setup": "Sistem Hazırlanıyor... (Bileşenler Kuruluyor)",
                "status_ready": "Sistem Hazır / Link Bekleniyor",
                "status_analyzing": "Bağlantı Analiz Ediliyor...",
                "status_dl": "İndiriliyor...",
                "success": "Başarıyla İndirildi!",
                "error": "Hata Oluştu! Lütfen Destek Sayfasına Gidin.",
                "ffmpeg_install": "FFmpeg Kuruluyor...",
                "qualities": ["En İyi Kalite", "1080p", "720p", "480p", "360p", "En Düşük Kalite"],
            },
            "EN": {
                "title": "YANARDAG AUTONOMOUS SYSTEM",
                "label": "Paste Video/Audio Link:",
                "ai_badge": "This application is powered by Bypass AI",
                "quality_label": "Quality:",
                "v_sec": "VIDEO (Desktop/My Videos)",
                "a_sec": "AUDIO (Desktop/My Music)",
                "lang_btn": "Language: EN",
                "support_btn": "Support & Report",
                "status_setup": "Setting Up... (Installing Components)",
                "status_ready": "System Ready / Waiting for Link",
                "status_analyzing": "Analyzing Connection...",
                "status_dl": "Downloading...",
                "success": "Downloaded Successfully!",
                "error": "An Error Occurred! Please Visit Support Page.",
                "ffmpeg_install": "Installing FFmpeg...",
                "qualities": ["Best Quality", "1080p", "720p", "480p", "360p", "Lowest Quality"],
            }
        }

        self.quality_map = {
            "En İyi Kalite": "best", "Best Quality": "best",
            "1080p": "1080",
            "720p": "720",
            "480p": "480",
            "360p": "360",
            "En Düşük Kalite": "worst", "Lowest Quality": "worst",
        }

        self.setup_ui()
        threading.Thread(target=self.initial_setup, daemon=True).start()

    def initial_setup(self):
        """Sistemi kurar ve gerekli araçları indirir."""
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        for d in ["My Videos", "My Music"]:
            p = os.path.join(desktop, d)
            if not os.path.exists(p):
                os.makedirs(p)

        if not os.path.exists(self.ytdlp_path):
            self.update_status("yt-dlp İndiriliyor...", "#f1c40f")
            url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
            urllib.request.urlretrieve(url, self.ytdlp_path)

        
        ffmpeg_exe = os.path.join(self.ffmpeg_bin, "ffmpeg.exe")
        if not os.path.exists(ffmpeg_exe):
            self.update_status(self.texts[self.lang]["ffmpeg_install"], "#f1c40f")
            try:
                ffmpeg_url = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
                zip_p = os.path.join(self.working_dir, "ffmpeg.zip")
                urllib.request.urlretrieve(ffmpeg_url, zip_p)
                with zipfile.ZipFile(zip_p, 'r') as z:
                    z.extractall(self.working_dir)
                extracted = [d for d in os.listdir(self.working_dir) if "ffmpeg-" in d and os.path.isdir(os.path.join(self.working_dir, d))]
                if extracted:
                    os.rename(os.path.join(self.working_dir, extracted[0]), self.ffmpeg_dir)
                os.remove(zip_p)
            except Exception as e:
                self.update_status(f"FFmpeg hatası: {e}", "#ff0000")
                return

        
        try:
            subprocess.run([self.ytdlp_path, "-U"], creationflags=0x08000000, timeout=30)
        except:
            pass

        self.update_status(self.texts[self.lang]["status_ready"], "#2ecc71")

    def update_status(self, text, color="#00ff00"):
        """Thread-safe status güncellemesi."""
        self.root.after(0, lambda: self.status_label.config(text=text, fg=color))

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#111", height=60)
        header.pack(fill="x")
        self.lang_btn = tk.Button(header, text=self.texts[self.lang]["lang_btn"],
                                  command=self.toggle_lang, bg="#333", fg="white", bd=0, padx=10)
        self.lang_btn.pack(side="right", padx=10, pady=15)
        self.support_btn = tk.Button(header, text=self.texts[self.lang]["support_btn"],
                                     command=lambda: webbrowser.open(self.support_url),
                                     bg="#c0392b", fg="white", bd=0, padx=10, font=("Arial", 8, "bold"))
        self.support_btn.pack(side="left", padx=10, pady=15)

        tk.Label(self.root, text=self.texts[self.lang]["title"],
                 font=("Impact", 28), bg="#050505", fg="#ff0000").pack(pady=15)

        ai_band = tk.Frame(self.root, bg="#0d0d0d", pady=5)
        ai_band.pack(fill="x")
        self.ai_badge_lbl = tk.Label(
            ai_band,
            text=self.texts[self.lang]["ai_badge"],
            bg="#0d0d0d", fg="#00e5ff",
            font=("Consolas", 9, "bold")
        )
        self.ai_badge_lbl.pack()

        self.link_label = tk.Label(self.root, text=self.texts[self.lang]["label"],
                                   bg="#050505", fg="#777")
        self.link_label.pack(pady=(10, 2))
        self.link_entry = tk.Entry(self.root, width=55, font=("Consolas", 11),
                                   bg="#111", fg="#00ff00", insertbackground="white",
                                   bd=0, highlightthickness=1, highlightbackground="#333")
        self.link_entry.pack(pady=5, ipady=8)

        q_frame = tk.Frame(self.root, bg="#050505")
        q_frame.pack(pady=4)
        self.quality_lbl = tk.Label(q_frame, text=self.texts[self.lang]["quality_label"],
                                    bg="#050505", fg="#888", font=("Arial", 9))
        self.quality_lbl.pack(side="left", padx=5)
        self.quality_combo = ttk.Combobox(q_frame, textvariable=self.quality_var,
                                          values=self.texts[self.lang]["qualities"],
                                          width=18, state="readonly", font=("Consolas", 9))
        self.quality_combo.current(0)
        self.quality_combo.pack(side="left")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#111", background="#333",
                        foreground="#2ecc71", selectbackground="#333")

        self.v_lbl = tk.Label(self.root, text=self.texts[self.lang]["v_sec"],
                              bg="#050505", fg="#f1c40f", font=("Arial", 9, "bold"))
        self.v_lbl.pack(pady=(12, 3))
        v_f = tk.Frame(self.root, bg="#050505")
        v_f.pack()
        row = None
        for i, f in enumerate(self.v_formats):
            if i % 4 == 0:
                row = tk.Frame(v_f, bg="#050505")
                row.pack()
            tk.Button(row, text=f.upper(), width=10,
                      command=lambda x=f: self.start_process(x, "v"),
                      bg="#1a1a1a", fg="#ff0000", font=("Arial", 9, "bold"),
                      bd=1, relief="flat", pady=5, cursor="hand2").pack(side="left", padx=5, pady=4)

        self.a_lbl = tk.Label(self.root, text=self.texts[self.lang]["a_sec"],
                              bg="#050505", fg="#f1c40f", font=("Arial", 9, "bold"))
        self.a_lbl.pack(pady=(12, 3))
        a_f = tk.Frame(self.root, bg="#050505")
        a_f.pack()
        row = None
        for i, f in enumerate(self.a_formats):
            if i % 3 == 0:
                row = tk.Frame(a_f, bg="#050505")
                row.pack()
            tk.Button(row, text=f.upper(), width=14,
                      command=lambda x=f: self.start_process(x, "a"),
                      bg="#1a1a1a", fg="#9b59b6", font=("Arial", 9, "bold"),
                      bd=1, relief="flat", pady=5, cursor="hand2").pack(side="left", padx=5, pady=4)

        self.status_label = tk.Label(self.root, text=self.texts[self.lang]["status_setup"],
                                     bg="#000", fg="#00ff00", font=("Consolas", 10), height=3)
        self.status_label.pack(side="bottom", fill="x")

    def toggle_lang(self):
        self.lang = "EN" if self.lang == "TR" else "TR"
        self.lang_btn.config(text=self.texts[self.lang]["lang_btn"])
        self.support_btn.config(text=self.texts[self.lang]["support_btn"])
        self.v_lbl.config(text=self.texts[self.lang]["v_sec"])
        self.a_lbl.config(text=self.texts[self.lang]["a_sec"])
        self.link_label.config(text=self.texts[self.lang]["label"])
        self.ai_badge_lbl.config(text=self.texts[self.lang]["ai_badge"])
        self.quality_lbl.config(text=self.texts[self.lang]["quality_label"])
        self.quality_combo.config(values=self.texts[self.lang]["qualities"])
        self.quality_combo.current(0)
        self.update_status(self.texts[self.lang]["status_ready"], "#2ecc71")

    def get_quality_value(self):
        selected = self.quality_var.get()
        return self.quality_map.get(selected, "best")

    def start_process(self, fmt, mode):
        url = self.link_entry.get().strip()
        if not url:
            return
        clean = self.clean_url(url)
        if not clean:
            self.update_status("Geçersiz URL!", "#ff0000")
            return
        self.update_status(self.texts[self.lang]["status_analyzing"], "#f1c40f")
        threading.Thread(target=self.execute_download, args=(clean, fmt, mode), daemon=True).start()

    def clean_url(self, url):
        url = url.strip()
        if "youtube" in url or "youtu.be" in url:
            m = re.search(r"[?&]v=([0-9A-Za-z_-]{11})", url)
            if m:
                return "https://www.youtube.com/watch?v=" + m.group(1)
            m2 = re.search(r"youtu\.be/([0-9A-Za-z_-]{11})", url)
            if m2:
                return "https://www.youtube.com/watch?v=" + m2.group(1)
        return url

    def execute_download(self, url, fmt, mode):
        folder = "My Videos" if mode == "v" else "My Music"
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        out_dir = os.path.join(desktop, folder)
        out_tpl  = os.path.join(out_dir, "%(title)s.%(ext)s")
        quality  = self.get_quality_value()

        if mode == "a":
            out_tpl = os.path.join(out_dir, "%(title)s." + fmt)
            audio_q = {"mp3": ["--audio-quality", "0"],
                       "aac": ["--audio-quality", "0"],
                       "ogg": ["--audio-quality", "0"],
                       "m4a": ["--audio-quality", "0"],
                       "wma": ["--audio-quality", "0"]}
            fmt_args = (
                ["-f", "bestaudio",          
                 "--extract-audio",          
                 "--audio-format", fmt,      
                 "--audio-quality", "0"]     
                + audio_q.get(fmt, [])
            )
        else:
            if quality == "best":
                fsel = "bestvideo+bestaudio/best"
            elif quality == "worst":
                fsel = "worstvideo+worstaudio/worst"
            else:
                fsel = ("bestvideo[height<=" + quality + "]+bestaudio[ext=m4a]/"
                        "bestvideo[height<=" + quality + "]+bestaudio/"
                        "bestvideo+bestaudio/best")

            if fmt == "mp4":
                fmt_args = ["-f", fsel, "--merge-output-format", "mp4"]
            elif fmt == "webm":
                fmt_args = ["-f", fsel, "--merge-output-format", "webm"]
            else:
                fmt_args = ["-f", fsel, "--merge-output-format", "mkv",
                            "--recode-video", fmt]

        strategies = [
            ("Web+Android",  ["--extractor-args","youtube:player-client=web,android"]),
            ("iOS İstemci",  ["--extractor-args","youtube:player-client=ios,web"]),
            ("User-Agent",   ["--user-agent",
                              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/124.0.0.0 Safari/537.36"]),
            ("Chrome Çerez", ["--cookies-from-browser","chrome"]),
        ]

        success    = False
        last_error = ""

        for i, (name, extra) in enumerate(strategies):
            self.update_status(f"Strateji {i+1}/4 ({name}) deneniyor...", "#f1c40f")

            cmd = (
                [self.ytdlp_path,
                 "--ffmpeg-location", self.ffmpeg_bin,
                 "--no-playlist",
                 "--no-check-certificate",
                 "--socket-timeout", "30",
                 "-o", out_tpl]
                + extra
                + fmt_args
                + [url]          
            )

            try:
                proc = subprocess.run(
                    cmd,
                    creationflags=0x08000000,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=300
                )
                if proc.returncode == 0:
                    success = True
                    break
                last_error = (proc.stderr or proc.stdout or "")[-400:]
            except subprocess.TimeoutExpired:
                last_error = "Zaman aşımı (300s)"
            except Exception as exc:
                last_error = str(exc)

        if success:
            self.update_status(self.texts[self.lang]["success"], "#2ecc71")
            self.root.after(0, lambda: messagebox.showinfo("Yanardağ", self.texts[self.lang]["success"]))
            try:
                os.startfile(out_dir)
            except Exception:
                pass
        else:
            self.update_status(self.texts[self.lang]["error"], "#ff0000")
            msg = self.texts[self.lang]["error"] + "\n\nSon hata:\n" + last_error
            self.root.after(0, lambda m=msg: messagebox.showerror("Hata", m))

        self.root.after(0, lambda: self.link_entry.delete(0, tk.END))


if __name__ == "__main__":
    root = tk.Tk()
    app = Yanardag_download_tool(root)
    root.mainloop()