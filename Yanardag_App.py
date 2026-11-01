import os
import sys
import re
import uuid
import shutil
import subprocess
import urllib.request
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import zipfile
import webbrowser


def _num(value):
    """'1080p' / '128kbps' gibi metinlerden sayıyı çıkarır."""
    m = re.search(r"\d+", str(value or ""))
    return int(m.group()) if m else 0


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
        self.ffmpeg_dir = os.path.join(self.working_dir, "ffmpeg")
        self.ffmpeg_bin = os.path.join(self.ffmpeg_dir, "bin")
        self.ffmpeg_exe = os.path.join(self.ffmpeg_bin, "ffmpeg.exe")

        self.YouTube = None          # pytubefix kurulumdan sonra yüklenir
        self._dl_label = ""

        self.v_formats = ["mp4", "mov", "avi", "mkv", "webm", "wmv", "flv"]
        self.a_formats = ["mp3", "aac", "ogg", "flac", "wav", "alac", "aiff", "m4a", "wma"]

        self.texts = {
            "TR": {
                "title": "YANARDAĞ OTONOM SİSTEM",
                "label": "Video/Ses Linkini Girin:",
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

        # Video çıktıları için ffmpeg kodlayıcı ayarları (kopyalama mümkün değilse)
        self.video_enc = {
            "mp4":  ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                     "-c:a", "aac", "-b:a", "192k"],
            "mov":  ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                     "-c:a", "aac", "-b:a", "192k"],
            "avi":  ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                     "-c:a", "libmp3lame", "-q:a", "2"],
            "wmv":  ["-c:v", "wmv2", "-b:v", "5M", "-c:a", "wmav2", "-b:a", "192k"],
            "flv":  ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
                     "-c:a", "aac", "-b:a", "160k"],
            "webm": ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-row-mt", "1",
                     "-c:a", "libopus", "-b:a", "160k"],
            "mkv":  ["-c", "copy"],
        }

        # Ses çıktıları için ffmpeg ayarları
        self.audio_enc = {
            "mp3":  ["-c:a", "libmp3lame", "-q:a", "0"],
            "aac":  ["-c:a", "aac", "-b:a", "256k"],
            "ogg":  ["-c:a", "libvorbis", "-q:a", "6"],
            "flac": ["-c:a", "flac"],
            "wav":  ["-c:a", "pcm_s16le"],
            "alac": ["-c:a", "alac"],
            "aiff": ["-c:a", "pcm_s16be"],
            "m4a":  ["-c:a", "aac", "-b:a", "256k"],
            "wma":  ["-c:a", "wmav2", "-b:a", "192k"],
        }

        self.setup_ui()
        threading.Thread(target=self.initial_setup, daemon=True).start()

    # ------------------------------------------------------------------ KURULUM
    def initial_setup(self):
        """Sistemi kurar ve gerekli araçları indirir."""
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        for d in ["My Videos", "My Music"]:
            p = os.path.join(desktop, d)
            if not os.path.exists(p):
                os.makedirs(p)

        # pytubefix: YouTube sık değiştiği için güncel tutulur
        self.update_status("pytubefix Kontrol Ediliyor...", "#f1c40f")
        if not getattr(sys, "frozen", False):
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-U", "pytubefix"],
                    creationflags=0x08000000, capture_output=True, timeout=120
                )
            except Exception:
                pass
        try:
            from pytubefix import YouTube
            self.YouTube = YouTube
        except Exception as e:
            self.update_status(f"pytubefix hatası: {e}", "#ff0000")
            return

        if not os.path.exists(self.ffmpeg_exe):
            self.update_status(self.texts[self.lang]["ffmpeg_install"], "#f1c40f")
            try:
                ffmpeg_url = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
                zip_p = os.path.join(self.working_dir, "ffmpeg.zip")
                urllib.request.urlretrieve(ffmpeg_url, zip_p)
                with zipfile.ZipFile(zip_p, 'r') as z:
                    z.extractall(self.working_dir)
                extracted = [d for d in os.listdir(self.working_dir)
                             if "ffmpeg-" in d and os.path.isdir(os.path.join(self.working_dir, d))]
                if extracted:
                    os.rename(os.path.join(self.working_dir, extracted[0]), self.ffmpeg_dir)
                os.remove(zip_p)
            except Exception as e:
                self.update_status(f"FFmpeg hatası: {e}", "#ff0000")
                return

        self.update_status(self.texts[self.lang]["status_ready"], "#2ecc71")

    def update_status(self, text, color="#00ff00"):
        """Thread-safe status güncellemesi."""
        self.root.after(0, lambda: self.status_label.config(text=text, fg=color))

    # ---------------------------------------------------------------------- ARAYÜZ
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
        self.quality_lbl.config(text=self.texts[self.lang]["quality_label"])
        self.quality_combo.config(values=self.texts[self.lang]["qualities"])
        self.quality_combo.current(0)
        self.update_status(self.texts[self.lang]["status_ready"], "#2ecc71")

    def get_quality_value(self):
        selected = self.quality_var.get()
        return self.quality_map.get(selected, "best")

    # ------------------------------------------------------------------ İNDİRME
    def start_process(self, fmt, mode):
        url = self.link_entry.get().strip()
        if not url:
            return
        if self.YouTube is None:
            self.update_status(self.texts[self.lang]["status_setup"], "#f1c40f")
            return
        video_id = self.clean_url(url)
        if not video_id:
            self.update_status("Geçersiz URL!", "#ff0000")
            return
        self.update_status(self.texts[self.lang]["status_analyzing"], "#f1c40f")
        threading.Thread(target=self.execute_download, args=(video_id, fmt, mode), daemon=True).start()

    def clean_url(self, url):
        """Linkten 11 karakterlik YouTube video ID'sini çıkarır (liste/ek parametreler atılır)."""
        url = url.strip()
        m = re.search(
            r"(?:youtube\.com/(?:watch\?(?:[^#\s]*&)?v=|shorts/|embed/|live/|v/)|youtu\.be/)"
            r"([0-9A-Za-z_-]{11})", url)
        return m.group(1) if m else None

    @staticmethod
    def safe_name(title):
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title or "video").strip(" .")
        return (name or "video")[:150]

    @staticmethod
    def unique_path(folder, name, ext):
        path = os.path.join(folder, f"{name}.{ext}")
        n = 1
        while os.path.exists(path):
            path = os.path.join(folder, f"{name} ({n}).{ext}")
            n += 1
        return path

    def on_progress(self, stream, chunk, bytes_remaining):
        total = getattr(stream, "filesize", 0) or 0
        if total:
            pct = (total - bytes_remaining) * 100 / total
            self.update_status(f"{self.texts[self.lang]['status_dl']} {self._dl_label} %{pct:.0f}", "#f1c40f")

    def run_ffmpeg(self, inputs, args, out_path):
        cmd = [self.ffmpeg_exe, "-y", "-loglevel", "error"]
        for i in inputs:
            cmd += ["-i", i]
        cmd += args + [out_path]
        proc = subprocess.run(cmd, creationflags=0x08000000, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=3600)
        if proc.returncode != 0:
            raise RuntimeError("ffmpeg: " + (proc.stderr or proc.stdout or "")[-300:])

    def download_to_disk(self, stream, tmp_dir, filename, label):
        """pytubefix akışı parça parça doğrudan diske yazar (RAM'de tutmaz)."""
        self._dl_label = label
        return stream.download(output_path=tmp_dir, filename=filename)

    def pick_audio(self, yt, fmt, worst):
        auds = list(yt.streams.filter(only_audio=True).fmt_streams)
        if not auds:
            return None
        pref = "audio/webm" if fmt == "webm" else "audio/mp4"
        if worst:
            return min(auds, key=lambda s: _num(s.abr))
        return max(auds, key=lambda s: (s.mime_type == pref, _num(s.abr)))

    def pick_video(self, yt, fmt, quality):
        vids = list(yt.streams.filter(only_video=True).fmt_streams)
        if not vids:
            return None
        pref = "video/webm" if fmt == "webm" else "video/mp4"
        if quality == "worst":
            return min(vids, key=lambda s: (_num(s.resolution), _num(s.fps), _num(s.bitrate)))
        if quality != "best":
            limit = int(quality)
            capped = [s for s in vids if 0 < _num(s.resolution) <= limit]
            if capped:
                vids = capped
            else:  # istenen kalite yoksa mevcut en düşüğü al
                lowest = min(_num(s.resolution) for s in vids)
                vids = [s for s in vids if _num(s.resolution) == lowest]
        return max(vids, key=lambda s: (_num(s.resolution), _num(s.fps),
                                        s.mime_type == pref, _num(s.bitrate)))

    def download_media(self, yt, fmt, mode, quality, tmp_dir, out_dir):
        name = self.safe_name(yt.title)

        # ----- SES -----
        if mode == "a":
            a = self.pick_audio(yt, "mp4", False)
            if a is None:
                raise RuntimeError("Ses akışı bulunamadı")
            src = self.download_to_disk(a, tmp_dir, "audio_src." + a.subtype, "(ses)")
            ext = "m4a" if fmt == "alac" else fmt
            if fmt == "m4a" and a.mime_type == "audio/mp4":
                args = ["-vn", "-c:a", "copy"]
            else:
                args = ["-vn"] + self.audio_enc[fmt]
            tmp_out = os.path.join(tmp_dir, "out." + ext)
            self.run_ffmpeg([src], args, tmp_out)
            final = self.unique_path(out_dir, name, ext)
            shutil.move(tmp_out, final)
            return final

        # ----- VİDEO -----
        v = self.pick_video(yt, fmt, quality)
        if v is not None:
            a = self.pick_audio(yt, fmt, quality == "worst")
            if a is None:
                raise RuntimeError("Ses akışı bulunamadı")
            v_src = self.download_to_disk(v, tmp_dir, "video_src." + v.subtype,
                                          f"(video {v.resolution})")
            a_src = self.download_to_disk(a, tmp_dir, "audio_src." + a.subtype, "(ses)")

            vc = (v.video_codec or "").lower()
            ac = (a.audio_codec or "").lower()
            can_copy = (
                (fmt == "mkv") or
                (fmt == "mp4" and v.mime_type == "video/mp4" and a.mime_type == "audio/mp4") or
                (fmt == "mov" and vc.startswith("avc1") and ac.startswith("mp4a")) or
                (fmt == "webm" and v.mime_type == "video/webm" and a.mime_type == "audio/webm")
            )
            args = (["-c", "copy"] if can_copy else self.video_enc[fmt])
            args = ["-map", "0:v:0", "-map", "1:a:0"] + args
            tmp_out = os.path.join(tmp_dir, "out." + fmt)
            self.update_status(f"{self.texts[self.lang]['status_dl']} (birleştiriliyor)", "#f1c40f")
            self.run_ffmpeg([v_src, a_src], args, tmp_out)
        else:
            # Adaptif akış yoksa (nadir) ses+video birleşik akışa düş
            progs = list(yt.streams.filter(progressive=True).fmt_streams)
            if not progs:
                raise RuntimeError("Video akışı bulunamadı")
            if quality == "worst":
                p = min(progs, key=lambda s: _num(s.resolution))
            else:
                limit = 99999 if quality == "best" else int(quality)
                ok = [s for s in progs if _num(s.resolution) <= limit] or progs
                p = max(ok, key=lambda s: _num(s.resolution))
            src = self.download_to_disk(p, tmp_dir, "prog_src." + p.subtype,
                                        f"(video {p.resolution})")
            tmp_out = os.path.join(tmp_dir, "out." + fmt)
            if fmt == "mp4" and p.mime_type == "video/mp4":
                shutil.move(src, tmp_out)
            else:
                self.run_ffmpeg([src], self.video_enc[fmt], tmp_out)

        final = self.unique_path(out_dir, name, fmt)
        shutil.move(tmp_out, final)
        return final

    def execute_download(self, video_id, fmt, mode):
        folder = "My Videos" if mode == "v" else "My Music"
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        out_dir = os.path.join(desktop, folder)
        os.makedirs(out_dir, exist_ok=True)
        quality = self.get_quality_value()
        url = "https://www.youtube.com/watch?v=" + video_id

        # YouTube istemci türleri sırayla denenir
        strategies = [
            ("VisionOS", "VISION_OS"),
            ("Web",      "WEB"),
            ("Android",  "ANDROID_VR"),
            ("TV",       "TV"),
        ]

        success = False
        last_error = ""

        for i, (name, client) in enumerate(strategies):
            self.update_status(f"Strateji {i+1}/4 ({name}) deneniyor...", "#f1c40f")
            tmp_dir = os.path.join(self.working_dir, "tmp_" + uuid.uuid4().hex[:8])
            try:
                os.makedirs(tmp_dir, exist_ok=True)
                yt = self.YouTube(url, client=client, on_progress_callback=self.on_progress)
                self.download_media(yt, fmt, mode, quality, tmp_dir, out_dir)
                success = True
                break
            except Exception as exc:
                last_error = str(exc)[-400:]
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

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
