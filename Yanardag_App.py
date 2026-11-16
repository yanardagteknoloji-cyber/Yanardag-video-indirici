import ctypes
import hashlib
import glob
from importlib.metadata import PackageNotFoundError, version
import logging
import logging.handlers
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.request
import uuid
import webbrowser
import zipfile
from tkinter import messagebox, ttk
from urllib.parse import parse_qs, urlparse

IS_WINDOWS = sys.platform == "win32"
NO_WINDOW = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
APP_DIR_NAME = "Yanardag_Sistem"

FFMPEG_URL = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
FFMPEG_SHA256 = "fa7d4d7e795db0e2503f49f105f46ed5852386f0cfdd819899be3b65ebde24fc"

YT_HOSTS = {
    "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com",
    "youtube-nocookie.com", "www.youtube-nocookie.com",
}
ID_RE = re.compile(r"^[0-9A-Za-z_-]{11}$")

CLIENTS = [
    ("VisionOS", "VISION_OS"),
    ("Web", "WEB"),
    ("Android", "ANDROID_VR"),
    ("TV", "TV"),
]

YELLOW, GREEN, RED = "#f1c40f", "#2ecc71", "#ff0000"

VIDEO_FORMATS = ["mp4", "mov", "avi", "mkv", "webm", "wmv", "flv"]
AUDIO_FORMATS = ["mp3", "aac", "ogg", "flac", "wav", "alac", "aiff", "m4a", "wma"]

VIDEO_ENC = {
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

AUDIO_ENC = {
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

TEXTS = {
    "TR": {
        "title": "YANARDAĞ OTONOM SİSTEM",
        "label": "Video/Ses Linkini Girin:",
        "quality_label": "Kalite:",
        "v_sec": "VİDEO (Masaüstü/My Videos)",
        "a_sec": "SES (Masaüstü/My Music)",
        "lang_btn": "Dil: TR",
        "support_btn": "Destek & Hata Bildir",
        "status_setup": "Sistem Hazırlanıyor... (Bileşenler Kuruluyor)",
        "status_analyzing": "Bağlantı Analiz Ediliyor...",
        "status_dl": "İndiriliyor...",
        "success": "Başarıyla İndirildi!",
        "error": "Hata Oluştu! Lütfen Destek Sayfasına Gidin.",
        "ffmpeg_install": "FFmpeg Kuruluyor...",
        "qualities": ["En İyi Kalite", "1080p", "720p", "480p", "360p", "En Düşük Kalite"],
        "invalid_url": "Geçersiz URL!",
        "playlist_only": "Bu bir oynatma listesi linki. Lütfen tek bir videonun linkini girin.",
        "playlist_note": "Not: Link bir oynatma listesi içeriyor; yalnızca tek video indirilecek.",
        "busy": "Bir indirme zaten sürüyor, bitmesini bekleyin.",
        "merging": "birleştiriliyor",
        "strategy": "Strateji {i}/{n} ({name}) deneniyor...",
        "errors_header": "Denenen yöntemlerin hataları:",
        "err_title": "Hata",
        "no_audio": "Ses akışı bulunamadı",
        "no_video": "Video akışı bulunamadı",
        "pytubefix_check": "pytubefix Kontrol Ediliyor...",
        "pytubefix_missing": "pytubefix bulunamadı. Uygulamayı yeniden indirin ya da 'pip install pytubefix' çalıştırın.",
        "pytubefix_err": "pytubefix hatası: {err}",
        "ffmpeg_err": "FFmpeg hatası: {err}",
        "ffmpeg_missing": "FFmpeg bulunamadı. Lütfen kurup PATH'e ekleyin.",
        "ffmpeg_no_exe": "Zip içinde ffmpeg.exe bulunamadı.",
        "checksum_err": "FFmpeg dosyası doğrulanamadı (SHA-256 uyuşmuyor).",
        "unsafe_zip": "Zip içinde güvenli olmayan yol var.",
        "tag_audio": "(ses)",
        "tag_video": "(video {res})",
        "ffmpeg_no_hash": "FFmpeg kurulamadı: doğrulama özeti tanımlı değil. FFmpeg'i elle kurup PATH'e ekleyin ya da uygulamanın yeni sürümünü kullanın.",
        "ffmpeg_verify": "FFmpeg doğrulanıyor...",
        "ffmpeg_extract": "FFmpeg açılıyor...",
        "status_ready_ver": "Sistem Hazır / Link Bekleniyor\npytubefix {ver}",
        "frozen_hint": "İndirme sürekli başarısız oluyorsa YouTube değişmiş olabilir; uygulamanın yeni sürümünü indirin.",
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
        "status_analyzing": "Analyzing Connection...",
        "status_dl": "Downloading...",
        "success": "Downloaded Successfully!",
        "error": "An Error Occurred! Please Visit Support Page.",
        "ffmpeg_install": "Installing FFmpeg...",
        "qualities": ["Best Quality", "1080p", "720p", "480p", "360p", "Lowest Quality"],
        "invalid_url": "Invalid URL!",
        "playlist_only": "This is a playlist link. Please enter the link of a single video.",
        "playlist_note": "Note: the link contains a playlist; only the single video will be downloaded.",
        "busy": "A download is already running, please wait for it to finish.",
        "merging": "merging",
        "strategy": "Strategy {i}/{n} ({name}) in progress...",
        "errors_header": "Errors from each attempt:",
        "err_title": "Error",
        "no_audio": "No audio stream found",
        "no_video": "No video stream found",
        "pytubefix_check": "Checking pytubefix...",
        "pytubefix_missing": "pytubefix not found. Download the app again or run 'pip install pytubefix'.",
        "pytubefix_err": "pytubefix error: {err}",
        "ffmpeg_err": "FFmpeg error: {err}",
        "ffmpeg_missing": "FFmpeg not found. Please install it and add it to PATH.",
        "ffmpeg_no_exe": "ffmpeg.exe not found inside the zip.",
        "checksum_err": "FFmpeg download could not be verified (SHA-256 mismatch).",
        "unsafe_zip": "Zip contains an unsafe path.",
        "tag_audio": "(audio)",
        "tag_video": "(video {res})",
        "ffmpeg_no_hash": "FFmpeg could not be installed: checksum is not set. Install FFmpeg manually and add it to PATH, or use a newer version of the app.",
        "ffmpeg_verify": "Verifying FFmpeg...",
        "ffmpeg_extract": "Extracting FFmpeg...",
        "status_ready_ver": "System Ready / Waiting for Link\npytubefix {ver}",
        "frozen_hint": "If downloads keep failing, YouTube may have changed; get a newer version of the app.",
    },
}

QUALITY_MAP = {
    "En İyi Kalite": "best", "Best Quality": "best",
    "1080p": "1080", "720p": "720", "480p": "480", "360p": "360",
    "En Düşük Kalite": "worst", "Lowest Quality": "worst",
}

log = logging.getLogger("yanardag")


class FFmpegError(RuntimeError):
    """ffmpeg işlemi başarısız. İstemci (client) değiştirmek sorunu çözmez."""


class DownloadError(RuntimeError):
    """Tüm indirme stratejileri başarısız oldu."""

    def __init__(self, errors):
        super().__init__("\n".join(errors))
        self.errors = errors


def _num(value):
    """'1080p' / '128kbps' gibi metinlerden sayıyı çıkarır."""
    m = re.search(r"\d+", str(value or ""))
    return int(m.group()) if m else 0


def app_data_dir():
    """Kullanıcıya özel, yazma izni olan uygulama klasörü (C:\\ köküne yazmaz)."""
    home = os.path.expanduser("~")
    if IS_WINDOWS:
        base = os.environ.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
    elif sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    return os.path.join(base, APP_DIR_NAME)


def desktop_dir():
    """Gerçek masaüstü klasörü (OneDrive'a taşınmış olsa bile)."""
    if IS_WINDOWS:
        try:
            class GUID(ctypes.Structure):
                _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort),
                            ("Data3", ctypes.c_ushort), ("Data4", ctypes.c_ubyte * 8)]

            fid = GUID(0xB4BFCC3A, 0xDB2C, 0x424C,
                       (ctypes.c_ubyte * 8)(0xB0, 0x29, 0x7F, 0xE9, 0x9A, 0x87, 0xC6, 0x41))
            ptr = ctypes.c_wchar_p()
            res = ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(fid), 0, None, ctypes.byref(ptr))
            if res == 0 and ptr.value:
                value = ptr.value
                ctypes.windll.ole32.CoTaskMemFree(ptr)
                return value
        except Exception:
            log.warning("Masaüstü yolu Windows API'sinden alınamadı", exc_info=True)
    return os.path.join(os.path.expanduser("~"), "Desktop")


def setup_logging(work_dir):
    os.makedirs(work_dir, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        os.path.join(work_dir, "yanardag.log"), maxBytes=512_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.setLevel(logging.INFO)
    log.addHandler(handler)


def parse_video_url(url):
    """(video_id | None, playlist_var_mi) döndürür. Yalnızca gerçek YouTube host'larını kabul eder."""
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    try:
        p = urlparse(url)
    except ValueError:
        return None, False
    if p.scheme not in ("http", "https"):
        return None, False
    host = (p.hostname or "").lower()
    q = parse_qs(p.query)
    has_list = "list" in q
    vid = None
    if host == "youtu.be":
        vid = p.path.lstrip("/").split("/")[0]
    elif host in YT_HOSTS:
        if p.path == "/watch":
            vid = (q.get("v") or [""])[0]
        else:
            m = re.match(r"^/(?:shorts|embed|live|v)/([^/?#]+)", p.path)
            if m:
                vid = m.group(1)
    if vid and ID_RE.match(vid):
        return vid, has_list
    return None, has_list


_RESERVED = ({"CON", "PRN", "AUX", "NUL"}
             | {f"COM{c}" for c in "123456789¹²³"}
             | {f"LPT{c}" for c in "123456789¹²³"})


def safe_name(title):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title or "video").strip(" .")
    name = name[:150].strip(" .")
    if name.split(".")[0].strip().upper() in _RESERVED:
        name = "_" + name
    return name or "video"


def unique_path(folder, name, ext):
    path = os.path.join(folder, f"{name}.{ext}")
    n = 1
    while os.path.exists(path):
        path = os.path.join(folder, f"{name} ({n}).{ext}")
        n += 1
    return path


def open_folder(path):
    try:
        if IS_WINDOWS:
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        log.warning("Klasör açılamadı: %s", path, exc_info=True)


def print_ffmpeg_hash():
    """Geliştirici yardımcısı: zip'i indirir, SHA-256 değerini yazdırır (FFMPEG_SHA256 için)."""
    h = hashlib.sha256()
    with urllib.request.urlopen(FFMPEG_URL, timeout=60) as r:
        for chunk in iter(lambda: r.read(1 << 20), b""):
            h.update(chunk)
    print(h.hexdigest())


class Progress:
    """pytubefix ilerleme geri çağrısı; yalnızca yüzde değişince / en fazla 5 Hz güncellenir."""

    def __init__(self, emit):
        self.emit = emit
        self.label = lambda: ""
        self._last_pct = -1
        self._last_t = 0.0

    def set_label(self, label):
        self.label = label
        self._last_pct = -1
        self._last_t = 0.0

    def __call__(self, stream, chunk, bytes_remaining):
        total = getattr(stream, "filesize", 0) or 0
        if not total:
            return
        pct = int((total - bytes_remaining) * 100 / total)
        now = time.monotonic()
        if pct == self._last_pct or (pct < 100 and now - self._last_t < 0.2):
            return
        self._last_pct, self._last_t = pct, now
        self.emit(self.label, pct)


def load_pytubefix(t):
    try:
        from pytubefix import YouTube
    except ImportError as exc:
        raise RuntimeError(t("pytubefix_missing")) from exc
    try:
        ver = version("pytubefix")
    except PackageNotFoundError:
        ver = getattr(sys.modules["pytubefix"], "__version__", "?")
    log.info("pytubefix %s", ver)
    return YouTube, ver


class FFmpegManager:
    def __init__(self, work_dir, t):
        self.work_dir = work_dir
        self.t = t
        self.dir = os.path.join(work_dir, "ffmpeg")
        if IS_WINDOWS:
            self.exe = os.path.join(self.dir, "bin", "ffmpeg.exe")
        else:
            self.exe = shutil.which("ffmpeg")

    def available(self):
        return bool(self.exe) and os.path.exists(self.exe)

    def ensure(self, status):
        if self.available():
            return
        found = shutil.which("ffmpeg")
        if found:
            self.exe = found
            return
        if not IS_WINDOWS:
            raise RuntimeError(self.t("ffmpeg_missing"))
        self._install(status)

    def _download(self, url, dest, status):
        try:
            with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                done, last = 0, -1
                while True:
                    chunk = r.read(1 << 18)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        pct = done * 100 // total
                        if pct != last:
                            last = pct
                            status(lambda pct=pct: f"{self.t('ffmpeg_install')} %{pct}", YELLOW)
            if total and done != total:
                raise RuntimeError(f"eksik indirme ({done}/{total})")
        except Exception as exc:
            raise RuntimeError(f"{exc} [{url}]") from exc

    def _verify(self, zip_path, expected):
        h = hashlib.sha256()
        with open(zip_path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != expected:
            raise RuntimeError(self.t("checksum_err"))

    def _safe_extract(self, zip_path, dest):
        base = os.path.realpath(dest)
        with zipfile.ZipFile(zip_path) as z:
            for m in z.infolist():
                target = os.path.realpath(os.path.join(dest, m.filename))
                if target != base and not target.startswith(base + os.sep):
                    raise RuntimeError(self.t("unsafe_zip"))
            z.extractall(dest)

    def _swap_in(self, new_dir):
        """Eski sürüm, yenisi yerleşmeden silinmez; taşıma başarısız olursa geri yüklenir.
        Kilitli kalmış eski .old klasörleri yeni işlemi engellemesin diye benzersiz ad kullanılır."""
        for leftover in glob.glob(self.dir + ".old*"):
            shutil.rmtree(leftover, ignore_errors=True)
        old = f"{self.dir}.old.{uuid.uuid4().hex[:6]}"
        had_old = os.path.exists(self.dir)
        if had_old:
            os.replace(self.dir, old)
        try:
            os.replace(new_dir, self.dir)
        except Exception:
            if had_old and not os.path.exists(self.dir):
                os.replace(old, self.dir)
            raise
        shutil.rmtree(old, ignore_errors=True)

    def _install(self, status):
        expected = FFMPEG_SHA256.strip().lower()
        if not expected:
            raise RuntimeError(self.t("ffmpeg_no_hash"))
        status(lambda: self.t("ffmpeg_install"), YELLOW)
        stage = os.path.join(self.work_dir, "ffmpeg_setup_" + uuid.uuid4().hex[:8])
        os.makedirs(stage)
        try:
            zip_path = os.path.join(stage, "ffmpeg.zip")
            self._download(FFMPEG_URL, zip_path, status)
            status(lambda: self.t("ffmpeg_verify"), YELLOW)
            self._verify(zip_path, expected)
            status(lambda: self.t("ffmpeg_extract"), YELLOW)
            extract_dir = os.path.join(stage, "x")
            self._safe_extract(zip_path, extract_dir)
            roots = [d for d in os.listdir(extract_dir)
                     if os.path.isfile(os.path.join(extract_dir, d, "bin", "ffmpeg.exe"))]
            if not roots:
                raise RuntimeError(self.t("ffmpeg_no_exe"))
            self._swap_in(os.path.join(extract_dir, roots[0]))
        finally:
            shutil.rmtree(stage, ignore_errors=True)

    def run(self, inputs, args, out_path):
        cmd = [self.exe, "-y", "-loglevel", "error"]
        for i in inputs:
            cmd += ["-i", i]
        cmd += args + [out_path]
        try:
            proc = subprocess.run(cmd, creationflags=NO_WINDOW, capture_output=True, stdin=subprocess.DEVNULL,
                                  text=True, encoding="utf-8", errors="replace", timeout=3600)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise FFmpegError(f"ffmpeg: {exc}") from exc
        if proc.returncode != 0:
            raise FFmpegError("ffmpeg: " + (proc.stderr or proc.stdout or "")[-300:])


class MediaDownloader:
    """Ağ + akış seçimi + ffmpeg birleştirme. Tk'ya bağımlı değildir."""

    def __init__(self, YouTube, ffmpeg, tmp_root, t):
        self.YouTube = YouTube
        self.ffmpeg = ffmpeg
        self.tmp_root = tmp_root
        self.t = t

    @staticmethod
    def pick_audio(yt, fmt, worst):
        auds = list(yt.streams.filter(only_audio=True).fmt_streams)
        if not auds:
            return None
        pref = "audio/webm" if fmt == "webm" else "audio/mp4"
        if worst:
            return min(auds, key=lambda s: _num(s.abr))
        return max(auds, key=lambda s: (s.mime_type == pref, _num(s.abr)))

    @staticmethod
    def pick_video(yt, fmt, quality):
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
            else:
                lowest = min(_num(s.resolution) for s in vids)
                vids = [s for s in vids if _num(s.resolution) == lowest]
        return max(vids, key=lambda s: (_num(s.resolution), _num(s.fps),
                                        s.mime_type == pref, _num(s.bitrate)))

    def download(self, video_id, fmt, mode, quality, out_dir, status, progress):
        """İstemci stratejilerini dener. ffmpeg hatasında diğer istemcilere GEÇMEZ
        (aynı büyük dosyayı tekrar indirmek sorunu çözmez). Tüm hataları toplar."""
        url = "https://www.youtube.com/watch?v=" + video_id
        errors = []
        for i, (name, client) in enumerate(CLIENTS, 1):
            status(lambda i=i, name=name: self.t("strategy", i=i, n=len(CLIENTS), name=name), YELLOW)
            tmp_dir = os.path.join(self.tmp_root, uuid.uuid4().hex[:8])
            try:
                os.makedirs(tmp_dir)
                yt = self.YouTube(url, client=client, on_progress_callback=progress)
                return self._fetch(yt, fmt, mode, quality, tmp_dir, out_dir, status, progress)
            except FFmpegError:
                raise
            except Exception as exc:
                log.warning("Strateji %s başarısız", name, exc_info=True)
                errors.append(f"{name}: {str(exc)[-200:]}")
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)
        raise DownloadError(errors)

    @staticmethod
    def _to_disk(stream, tmp_dir, filename, label, progress):
        progress.set_label(label)
        return stream.download(output_path=tmp_dir, filename=filename)

    def _fetch(self, yt, fmt, mode, quality, tmp_dir, out_dir, status, progress):
        t = self.t
        name = safe_name(yt.title)

        if mode == "a":
            a = self.pick_audio(yt, "m4a", quality == "worst")
            if a is None:
                raise RuntimeError(t("no_audio"))
            src = self._to_disk(a, tmp_dir, "audio_src." + a.subtype, lambda: t("tag_audio"), progress)
            ext = "m4a" if fmt == "alac" else fmt
            if fmt == "m4a" and a.mime_type == "audio/mp4":
                args = ["-vn", "-c:a", "copy"]
            else:
                args = ["-vn"] + AUDIO_ENC[fmt]
            tmp_out = os.path.join(tmp_dir, "out." + ext)
            self.ffmpeg.run([src], args, tmp_out)
            final = unique_path(out_dir, name, ext)
            shutil.move(tmp_out, final)
            return final

        tmp_out = os.path.join(tmp_dir, "out." + fmt)
        v = self.pick_video(yt, fmt, quality)
        if v is not None:
            a = self.pick_audio(yt, fmt, quality == "worst")
            if a is None:
                raise RuntimeError(t("no_audio"))
            v_src = self._to_disk(v, tmp_dir, "video_src." + v.subtype,
                                  lambda: t("tag_video", res=v.resolution), progress)
            a_src = self._to_disk(a, tmp_dir, "audio_src." + a.subtype, lambda: t("tag_audio"), progress)

            vc = (v.video_codec or "").lower()
            ac = (a.audio_codec or "").lower()
            can_copy = (
                fmt == "mkv"
                or (fmt == "mp4" and v.mime_type == "video/mp4" and a.mime_type == "audio/mp4")
                or (fmt == "mov" and vc.startswith("avc1") and ac.startswith("mp4a"))
                or (fmt == "webm" and v.mime_type == "video/webm" and a.mime_type == "audio/webm")
            )
            maps = ["-map", "0:v:0", "-map", "1:a:0"]
            status(lambda: f"{t('status_dl')} ({t('merging')})", YELLOW)
            try:
                self.ffmpeg.run([v_src, a_src], maps + (["-c", "copy"] if can_copy else VIDEO_ENC[fmt]), tmp_out)
            except FFmpegError:
                if not can_copy or fmt == "mkv":
                    raise
                log.warning("Kopyalama başarısız, yeniden kodlanıyor", exc_info=True)
                self.ffmpeg.run([v_src, a_src], maps + VIDEO_ENC[fmt], tmp_out)
        else:
            progs = list(yt.streams.filter(progressive=True).fmt_streams)
            if not progs:
                raise RuntimeError(t("no_video"))
            if quality == "worst":
                p = min(progs, key=lambda s: _num(s.resolution))
            else:
                limit = 99999 if quality == "best" else int(quality)
                ok = [s for s in progs if _num(s.resolution) <= limit] or progs
                p = max(ok, key=lambda s: _num(s.resolution))
            src = self._to_disk(p, tmp_dir, "prog_src." + p.subtype,
                                lambda: t("tag_video", res=p.resolution), progress)
            if fmt == "mp4" and p.mime_type == "video/mp4":
                shutil.move(src, tmp_out)
            else:
                self.ffmpeg.run([src], VIDEO_ENC[fmt], tmp_out)

        final = unique_path(out_dir, name, fmt)
        shutil.move(tmp_out, final)
        return final


class Yanardag_download_tool:
    def __init__(self, root):
        self.root = root
        self.root.title("Yanardağ Medya İstasyonu")
        self.root.geometry("680x860")
        self.root.configure(bg="#050505")
        self.lang = "TR"
        self.quality_var = tk.StringVar(value="best")

        self.working_dir = app_data_dir()
        self.tmp_root = os.path.join(self.working_dir, "tmp")
        self.support_url = "https://yanardag.free.nf"
        setup_logging(self.working_dir)

        self.ffmpeg = FFmpegManager(self.working_dir, self.t)
        self.downloader = None
        self._busy = threading.Lock()
        self._buttons = []
        self.pytubefix_version = "?"
        self.setup_failed = False
        self._status_spec = (lambda: self.t("status_setup"), "#00ff00")

        self.setup_ui()
        threading.Thread(target=self.initial_setup, daemon=True).start()

    def t(self, key, **kw):
        s = TEXTS[self.lang].get(key) or TEXTS["EN"][key]
        return s.format(**kw) if kw else s

    def cleanup_stale_tmp(self, max_age=3600):
        """Süreç yarıda ölürse geride kalan geçici klasörleri temizler."""
        now = time.time()
        candidates = glob.glob(os.path.join(self.working_dir, "ffmpeg_setup_*"))
        if os.path.isdir(self.tmp_root):
            candidates += [os.path.join(self.tmp_root, e) for e in os.listdir(self.tmp_root)]
        for path in candidates:
            try:
                if now - os.path.getmtime(path) > max_age:
                    shutil.rmtree(path, ignore_errors=True)
            except OSError:
                log.warning("Geçici klasör temizlenemedi: %s", path, exc_info=True)

    def initial_setup(self):
        try:
            os.makedirs(self.tmp_root, exist_ok=True)
            self.cleanup_stale_tmp()
            desktop = desktop_dir()
            for d in ("My Videos", "My Music"):
                os.makedirs(os.path.join(desktop, d), exist_ok=True)
        except Exception:
            log.warning("Klasörler hazırlanamadı", exc_info=True)

        self.update_status(lambda: self.t("pytubefix_check"), YELLOW)
        try:
            YouTube, self.pytubefix_version = load_pytubefix(self.t)
        except Exception as e:
            log.exception("pytubefix yüklenemedi")
            self.setup_failed = True
            self.update_status(lambda err=str(e): self.t("pytubefix_err", err=err), RED)
            return

        try:
            self.ffmpeg.ensure(self.update_status)
        except Exception as e:
            log.exception("FFmpeg kurulamadı")
            self.setup_failed = True
            self.update_status(lambda err=str(e): self.t("ffmpeg_err", err=err), RED)
            return

        self.downloader = MediaDownloader(YouTube, self.ffmpeg, self.tmp_root, self.t)
        ver = self.pytubefix_version
        key = "status_ready_ver"
        self.update_status(lambda: self.t(key, ver=ver), GREEN)

    def update_status(self, text, color="#00ff00"):
        """Thread-safe durum güncellemesi. `text` metin ya da (dil değişince yeniden
        üretilebilsin diye) argümansız bir fonksiyon olabilir."""
        try:
            self.root.after(0, self._render_status, text, color)
        except (tk.TclError, RuntimeError):
            pass

    def _render_status(self, spec, color):
        self._status_spec = (spec, color)
        self._draw_status()

    def _draw_status(self):
        spec, color = self._status_spec
        self.status_label.config(text=spec() if callable(spec) else spec, fg=color)

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#111", height=60)
        header.pack(fill="x")
        self.lang_btn = tk.Button(header, text=self.t("lang_btn"),
                                  command=self.toggle_lang, bg="#333", fg="white", bd=0, padx=10)
        self.lang_btn.pack(side="right", padx=10, pady=15)
        self.support_btn = tk.Button(header, text=self.t("support_btn"),
                                     command=lambda: webbrowser.open(self.support_url),
                                     bg="#c0392b", fg="white", bd=0, padx=10, font=("Arial", 8, "bold"))
        self.support_btn.pack(side="left", padx=10, pady=15)

        self.title_lbl = tk.Label(self.root, text=self.t("title"),
                                  font=("Impact", 28), bg="#050505", fg="#ff0000")
        self.title_lbl.pack(pady=15)

        self.link_label = tk.Label(self.root, text=self.t("label"), bg="#050505", fg="#777")
        self.link_label.pack(pady=(10, 2))
        self.link_entry = tk.Entry(self.root, width=55, font=("Consolas", 11),
                                   bg="#111", fg="#00ff00", insertbackground="white",
                                   bd=0, highlightthickness=1, highlightbackground="#333")
        self.link_entry.pack(pady=5, ipady=8)

        q_frame = tk.Frame(self.root, bg="#050505")
        q_frame.pack(pady=4)
        self.quality_lbl = tk.Label(q_frame, text=self.t("quality_label"),
                                    bg="#050505", fg="#888", font=("Arial", 9))
        self.quality_lbl.pack(side="left", padx=5)
        self.quality_combo = ttk.Combobox(q_frame, textvariable=self.quality_var,
                                          values=TEXTS[self.lang]["qualities"],
                                          width=18, state="readonly", font=("Consolas", 9))
        self.quality_combo.current(0)
        self.quality_combo.pack(side="left")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#111", background="#333",
                        foreground="#2ecc71", selectbackground="#333")

        self.v_lbl = tk.Label(self.root, text=self.t("v_sec"),
                              bg="#050505", fg="#f1c40f", font=("Arial", 9, "bold"))
        self.v_lbl.pack(pady=(12, 3))
        self._build_buttons(VIDEO_FORMATS, "v", per_row=4, width=10, fg="#ff0000")

        self.a_lbl = tk.Label(self.root, text=self.t("a_sec"),
                              bg="#050505", fg="#f1c40f", font=("Arial", 9, "bold"))
        self.a_lbl.pack(pady=(12, 3))
        self._build_buttons(AUDIO_FORMATS, "a", per_row=3, width=14, fg="#9b59b6")

        self.status_label = tk.Label(self.root, text=self.t("status_setup"),
                                     bg="#000", fg="#00ff00", font=("Consolas", 10),
                                     height=3, wraplength=640, justify="center")
        self.status_label.pack(side="bottom", fill="x")

    def _build_buttons(self, formats, mode, per_row, width, fg):
        frame = tk.Frame(self.root, bg="#050505")
        frame.pack()
        row = None
        for i, f in enumerate(formats):
            if i % per_row == 0:
                row = tk.Frame(frame, bg="#050505")
                row.pack()
            b = tk.Button(row, text=f.upper(), width=width,
                          command=lambda x=f: self.start_process(x, mode),
                          bg="#1a1a1a", fg=fg, font=("Arial", 9, "bold"),
                          bd=1, relief="flat", pady=5, cursor="hand2")
            b.pack(side="left", padx=5, pady=4)
            self._buttons.append(b)

    def _set_buttons(self, state):
        for b in self._buttons:
            b.config(state=state)

    def toggle_lang(self):
        self.lang = "EN" if self.lang == "TR" else "TR"
        idx = self.quality_combo.current()
        self.lang_btn.config(text=self.t("lang_btn"))
        self.support_btn.config(text=self.t("support_btn"))
        self.title_lbl.config(text=self.t("title"))
        self.v_lbl.config(text=self.t("v_sec"))
        self.a_lbl.config(text=self.t("a_sec"))
        self.link_label.config(text=self.t("label"))
        self.quality_lbl.config(text=self.t("quality_label"))
        self.quality_combo.config(values=TEXTS[self.lang]["qualities"])
        self.quality_combo.current(idx if idx >= 0 else 0)
        self._draw_status()

    def get_quality_value(self):
        return QUALITY_MAP.get(self.quality_var.get(), "best")

    def start_process(self, fmt, mode):
        url = self.link_entry.get().strip()
        if not url:
            return
        if self.downloader is None:
            if not self.setup_failed:
                self.update_status(lambda: self.t("status_setup"), YELLOW)
            return

        video_id, has_list = parse_video_url(url)
        if not video_id:
            key = "playlist_only" if has_list else "invalid_url"
            self.update_status(lambda: self.t(key), RED)
            return

        quality = self.get_quality_value()

        if not self._busy.acquire(blocking=False):
            self.update_status(lambda: self.t("busy"), YELLOW)
            return
        self._set_buttons("disabled")

        def analyzing():
            text = self.t("status_analyzing")
            return text + "\n" + self.t("playlist_note") if has_list else text
        self.update_status(analyzing, YELLOW)
        threading.Thread(target=self.execute_download,
                         args=(video_id, fmt, mode, quality), daemon=True).start()

    def execute_download(self, video_id, fmt, mode, quality):
        success, error_text, out_dir = False, "", None
        try:
            out_dir = os.path.join(desktop_dir(), "My Videos" if mode == "v" else "My Music")
            os.makedirs(out_dir, exist_ok=True)
            progress = Progress(lambda label, pct: self.update_status(
                lambda: f"{self.t('status_dl')} {label()} %{pct}", YELLOW))
            self.downloader.download(video_id, fmt, mode, quality, out_dir,
                                     self.update_status, progress)
            success = True
        except FFmpegError as exc:
            log.exception("ffmpeg hatası")
            error_text = str(exc)
        except DownloadError as exc:
            error_text = self.t("errors_header") + "\n" + "\n".join(exc.errors)
        except Exception as exc:
            log.exception("Beklenmeyen indirme hatası")
            error_text = str(exc)[-400:]
        finally:
            self.root.after(0, self._finish, success, error_text, out_dir if success else None)
            self._busy.release()

    def _finish(self, success, error_text, out_dir):
        """Ana thread'de çalışır: arayüzü geri açar, sonucu gösterir."""
        self._set_buttons("normal")
        if success:
            self._render_status(lambda: self.t("success"), GREEN)
            self.link_entry.delete(0, tk.END)
            messagebox.showinfo("Yanardağ", self.t("success"))
            open_folder(out_dir)
        else:
            self._render_status(lambda: self.t("error"), RED)
            hint = "\n\n" + self.t("frozen_hint") if getattr(sys, "frozen", False) else ""
            messagebox.showerror(self.t("err_title"), self.t("error") + "\n\n" + error_text + hint)


if __name__ == "__main__":
    if "--ffmpeg-hash" in sys.argv:
        print_ffmpeg_hash()
        sys.exit(0)
    root = tk.Tk()
    app = Yanardag_download_tool(root)
    root.mainloop()
