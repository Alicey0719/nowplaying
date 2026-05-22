"""Now Playing → X 投稿補助 GUI"""
import threading
import tkinter as tk
from io import BytesIO
from pathlib import Path
from typing import Optional
import webbrowser
from urllib.parse import quote

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

import config
from media import get_media_info, MediaInfo
from uploader import upload_image

FONT = "LINE Seed JP"

# Catppuccin Mocha
BG      = "#1e1e2e"
SURFACE = "#313244"
OVERLAY = "#45475a"
TEXT    = "#cdd6f4"
SUBTEXT = "#a6adc8"
MUTED   = "#585b70"
ACCENT  = "#cba6f7"   # lavender
PINK    = "#f38ba8"
GREEN   = "#a6e3a1"
YELLOW  = "#f9e2af"


def _format_tweet(info: MediaInfo) -> str:
    if info.artist:
        return config.TWEET_TEMPLATE.format(
            title=info.title, artist=info.artist, album=info.album,
        )
    return config.TWEET_TEMPLATE_NO_ARTIST.format(
        title=info.title, album=info.album,
    )


def _copy_text(text: str) -> None:
    import win32clipboard
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()


def _copy_image(artwork: bytes) -> None:
    import win32clipboard
    img = Image.open(BytesIO(artwork))
    img.thumbnail((300, 300), Image.LANCZOS)
    buf = BytesIO()
    img.convert("RGB").save(buf, "BMP")
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, buf.getvalue()[14:])
    finally:
        win32clipboard.CloseClipboard()


def _make_icon(size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, size - 1, size - 1], fill=ACCENT)
    s = size // 8
    # 音符の縦棒
    x = size * 17 // 32
    d.rectangle([x, s * 2, x + s, s * 5], fill=BG)
    # 旗
    d.polygon([(x + s, s * 2), (x + s * 4, s * 3), (x + s, s * 4)], fill=BG)
    # 音符の頭
    cx, cy, r = size * 13 // 32, s * 5, s + 1
    d.ellipse([cx - r, cy - r + 2, cx + r, cy + r + 2], fill=BG)
    return img


def _rounded_art(data: bytes, size: int = 148) -> ctk.CTkImage:
    img = Image.open(BytesIO(data)).convert("RGBA")
    img.thumbnail((size, size), Image.LANCZOS)
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=10, fill=255)
    img.putalpha(mask)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))


class NowPlayingApp:
    _REFRESH_MS = config.WATCH_INTERVAL_SECONDS * 1000

    def __init__(self) -> None:
        self._info: Optional[MediaInfo] = None
        self._tweet_text = ""
        self._uploaded_url: Optional[str] = None
        self._fetching = False
        self._after_id: Optional[str] = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._root = ctk.CTk()
        self._root.title("Now Playing")
        self._root.resizable(True, True)
        self._root.configure(fg_color=BG)

        # アイコン
        try:
            icon_path = Path(__file__).parent / "_icon.png"
            if not icon_path.exists():
                _make_icon(64).save(icon_path)
            self._root.iconphoto(True, ImageTk.PhotoImage(Image.open(icon_path)))
        except Exception:
            pass

        self._auto_var = tk.BooleanVar(value=True)
        self._auto_var.trace_add("write", self._on_auto_changed)

        self._build_ui()
        # 高さはコンテンツ実寸、幅はテキスト列を確保できる最低幅を保証
        self._root.update_idletasks()
        w = max(self._root.winfo_reqwidth(), 440)
        h = self._root.winfo_reqheight()
        self._root.geometry(f"{w}x{h}")
        self._root.minsize(w, h)
        self._do_refresh()
        self._root.mainloop()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        # ヘッダー: タイトル左 / アイコンボタン群 + スイッチ + ↺ 右
        hdr = ctk.CTkFrame(self._root, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 8))

        ctk.CTkLabel(
            hdr, text="♪  Now Playing",
            font=ctk.CTkFont(FONT, 14, "bold"),
            text_color=ACCENT,
        ).pack(side="left")

        # 右端から pack: ↺ → switch → 🖼 → 📋 → 𝕏
        self._btn_refresh = ctk.CTkButton(
            hdr, text="↺", width=24, height=24,
            fg_color="transparent", hover_color=OVERLAY,
            text_color=MUTED, font=ctk.CTkFont(size=14),
            corner_radius=6, command=self._do_refresh,
        )
        self._btn_refresh.pack(side="right", padx=(3, 0))

        self._switch = ctk.CTkSwitch(
            hdr, text="", variable=self._auto_var,
            progress_color=ACCENT, button_color=TEXT,
            width=34, height=17,
        )
        self._switch.pack(side="right", padx=(6, 0))

        self._btn_image = ctk.CTkButton(
            hdr, text="🖼", width=24, height=24,
            fg_color="transparent", hover_color=OVERLAY,
            text_color=SUBTEXT, font=ctk.CTkFont(size=14),
            corner_radius=6, command=self._do_copy_image,
        )
        self._btn_image.pack(side="right", padx=(3, 0))

        self._btn_text = ctk.CTkButton(
            hdr, text="📋", width=24, height=24,
            fg_color="transparent", hover_color=OVERLAY,
            text_color=SUBTEXT, font=ctk.CTkFont(size=14),
            corner_radius=6, command=self._do_copy_text,
        )
        self._btn_text.pack(side="right", padx=(3, 0))

        self._btn_browser = ctk.CTkButton(
            hdr, text="𝕏", width=24, height=24,
            fg_color="transparent", hover_color=OVERLAY,
            text_color=ACCENT, font=ctk.CTkFont(FONT, 13, "bold"),
            corner_radius=6, command=self._open_browser,
        )
        self._btn_browser.pack(side="right", padx=(6, 0))

        # カード（アート + 曲情報）
        card = ctk.CTkFrame(self._root, fg_color=SURFACE, corner_radius=14)
        card.pack(fill="x", padx=14)
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(0, weight=1)

        self._art_label = ctk.CTkLabel(card, text="♪", width=148, height=148,
                                        text_color=MUTED,
                                        font=ctk.CTkFont(size=52),
                                        fg_color=OVERLAY, corner_radius=14)
        self._art_label.grid(row=0, column=0, padx=(12, 10), pady=12, sticky="ns")

        meta = ctk.CTkFrame(card, fg_color="transparent")
        meta.grid(row=0, column=1, sticky="nsew", pady=14, padx=(0, 12))
        meta.bind("<Configure>", self._on_meta_configure)

        self._lbl_title = ctk.CTkLabel(
            meta, text="—", anchor="w", justify="left", wraplength=1,
            font=ctk.CTkFont(FONT, 14, "bold"), text_color=TEXT,
        )
        self._lbl_title.pack(fill="x")

        self._lbl_artist = ctk.CTkLabel(
            meta, text="", anchor="w", justify="left", wraplength=1,
            font=ctk.CTkFont(FONT, 12), text_color=SUBTEXT,
        )
        self._lbl_artist.pack(fill="x", pady=(3, 0))

        self._lbl_album = ctk.CTkLabel(
            meta, text="", anchor="w", justify="left", wraplength=1,
            font=ctk.CTkFont(FONT, 11), text_color=MUTED,
        )
        self._lbl_album.pack(fill="x", pady=(1, 0))

        # ステータス
        self._status_var = tk.StringVar()
        self._lbl_status = ctk.CTkLabel(
            self._root, textvariable=self._status_var,
            font=ctk.CTkFont(FONT, 10), text_color=GREEN,
        )
        self._lbl_status.pack(pady=(4, 6))

        self._root.bind("<Return>", lambda _: self._open_browser())

    def _on_meta_configure(self, event) -> None:
        # DPI変更・ウィンドウリサイズ両方に対応して wraplength を実幅に合わせる
        w = max(event.width - 4, 50)
        for lbl in (self._lbl_title, self._lbl_artist, self._lbl_album):
            lbl.configure(wraplength=w)

    # ------------------------------------------------------------------ ボタン

    def _open_browser(self) -> None:
        if not self._tweet_text:
            return
        if config.IMAGE_UPLOAD_SERVICE and self._info and self._info.artwork and self._uploaded_url is None:
            self._set_status("アップロード中...", YELLOW)
            self._set_content_buttons(False)
            artwork = self._info.artwork
            def do_upload() -> None:
                try:
                    url = upload_image(artwork)
                except Exception as e:
                    self._root.after(0, lambda: self._on_upload_done(None, str(e)))
                    return
                self._root.after(0, lambda: self._on_upload_done(url, None))
            threading.Thread(target=do_upload, daemon=True).start()
        else:
            self._launch_browser()

    def _on_upload_done(self, url: Optional[str], error: Optional[str]) -> None:
        if error:
            self._set_status(f"アップロード失敗: {error}", PINK)
        else:
            self._uploaded_url = url
        self._set_content_buttons(True)
        self._launch_browser()

    def _launch_browser(self) -> None:
        text = self._tweet_text
        if self._uploaded_url:
            text = f"{text} {self._uploaded_url}"
        webbrowser.open(f"https://x.com/intent/tweet?text={quote(text)}")
        self._set_status("ブラウザを開きました ✓", GREEN)

    def _do_copy_text(self) -> None:
        if not self._tweet_text:
            return
        try:
            _copy_text(self._tweet_text)
            self._set_status("✓ テキストをコピーしました", GREEN)
        except Exception as e:
            self._set_status(f"コピー失敗: {e}", PINK)

    def _do_copy_image(self) -> None:
        if not self._info or not self._info.artwork:
            return
        try:
            _copy_image(self._info.artwork)
            self._set_status("✓ 画像をコピーしました", GREEN)
        except Exception as e:
            self._set_status(f"コピー失敗: {e}", PINK)

    # ------------------------------------------------------------------ 更新

    def _on_auto_changed(self, *_) -> None:
        if self._auto_var.get():
            if self._after_id:
                self._root.after_cancel(self._after_id)
                self._after_id = None
            self._do_refresh()

    def _do_refresh(self) -> None:
        if self._fetching:
            return
        self._fetching = True
        self._btn_refresh.configure(state="disabled")
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self) -> None:
        try:
            info = get_media_info()
        except Exception:
            info = None
        self._root.after(0, lambda: self._apply(info))

    def _apply(self, info: Optional[MediaInfo]) -> None:
        self._fetching = False
        self._btn_refresh.configure(state="normal")
        if info != self._info:
            self._info = info
            self._uploaded_url = None
            self._render(info)
            # テキスト量に応じてウィンドウ高さを自動調整
            self._root.update_idletasks()
            needed_h = self._root.winfo_reqheight()
            if needed_h > self._root.winfo_height():
                self._root.geometry(f"{self._root.winfo_width()}x{needed_h}")
        if self._auto_var.get():
            self._after_id = self._root.after(self._REFRESH_MS, self._do_refresh)

    def _render(self, info: Optional[MediaInfo]) -> None:
        if info is None:
            self._tweet_text = ""
            self._lbl_title.configure(text="再生中の曲が見つかりません", text_color=MUTED)
            self._lbl_artist.configure(text="")
            self._lbl_album.configure(text="")
            self._art_label.configure(image=None, text="♪", fg_color=OVERLAY)
            self._set_content_buttons(False)
            return

        self._tweet_text = _format_tweet(info)
        self._lbl_title.configure(text=info.title, text_color=TEXT)
        self._lbl_artist.configure(text=info.artist)
        self._lbl_album.configure(text=info.album)

        if info.artwork:
            try:
                photo = _rounded_art(info.artwork)
                self._art_label.configure(image=photo, text="", fg_color="transparent")
                self._art_label._ctk_image = photo  # GC 防止
            except Exception:
                self._art_label.configure(image=None, text="♪", fg_color=OVERLAY)
        else:
            self._art_label.configure(image=None, text="♪", fg_color=OVERLAY)

        self._set_content_buttons(True)
        self._btn_image.configure(state="normal" if info.artwork else "disabled")

    def _set_content_buttons(self, enabled: bool) -> None:
        s = "normal" if enabled else "disabled"
        self._btn_browser.configure(state=s)
        self._btn_text.configure(state=s)
        self._btn_image.configure(state=s)

    def _set_status(self, msg: str, color: str = GREEN) -> None:
        self._status_var.set(msg)
        self._lbl_status.configure(text_color=color)


def run_gui() -> None:
    NowPlayingApp()
