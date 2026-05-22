"""Now Playing → X 投稿補助 GUI"""
import threading
import tkinter as tk
from tkinter import ttk
from io import BytesIO
from typing import Optional
import webbrowser
from urllib.parse import quote

import config
from media import get_media_info, MediaInfo
from uploader import upload_image


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
    from PIL import Image
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


class NowPlayingApp:
    _REFRESH_MS = config.WATCH_INTERVAL_SECONDS * 1000

    def __init__(self) -> None:
        self._info: Optional[MediaInfo] = None
        self._tweet_text = ""
        self._uploaded_url: Optional[str] = None  # 曲ごとにキャッシュ

        self._root = tk.Tk()
        self._root.title("Now Playing")
        self._root.resizable(False, False)
        self._build_ui()
        self._schedule_refresh()
        self._root.mainloop()

    def _build_ui(self) -> None:
        self._art_label = tk.Label(self._root)
        self._art_label.pack(pady=(16, 0))

        self._txt = tk.Text(
            self._root, width=42, height=4, wrap="word",
            font=("Segoe UI", 10), relief="flat", bg="#f5f5f5", padx=8, pady=8,
        )
        self._txt.pack(padx=16, pady=12)

        self._status = tk.StringVar(value="読み込み中...")
        tk.Label(self._root, textvariable=self._status,
                 font=("Segoe UI", 9), fg="#2e7d32").pack()

        btn_frame = tk.Frame(self._root)
        btn_frame.pack(pady=(8, 16))

        self._btn_browser = ttk.Button(btn_frame, text="ブラウザで開く",
                                       command=self._open_browser, width=18)
        self._btn_browser.pack(side="left", padx=4)

        self._btn_text = ttk.Button(btn_frame, text="テキストをコピー",
                                    command=self._do_copy_text, width=18)
        self._btn_text.pack(side="left", padx=4)

        self._btn_image = ttk.Button(btn_frame, text="画像をコピー",
                                     command=self._do_copy_image, width=14)
        self._btn_image.pack(side="left", padx=4)

        self._root.bind("<Return>", lambda _: self._open_browser())

    # --- ボタンアクション ---

    def _open_browser(self) -> None:
        if not self._tweet_text:
            return
        # アップロード設定あり・未アップロードの場合はバックグラウンドでアップロード
        if config.IMAGE_UPLOAD_SERVICE and self._info and self._info.artwork and self._uploaded_url is None:
            self._status.set("画像をアップロード中...")
            self._set_buttons("disabled", "disabled", "disabled")
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
            self._status.set(f"アップロード失敗: {error}")
        else:
            self._uploaded_url = url
        self._set_buttons("normal", "normal", "normal" if self._info and self._info.artwork else "disabled")
        self._launch_browser()

    def _launch_browser(self) -> None:
        text = self._tweet_text
        if self._uploaded_url:
            text = f"{text} {self._uploaded_url}"
        webbrowser.open(f"https://x.com/intent/tweet?text={quote(text)}")
        self._status.set("ブラウザを開きました")

    def _do_copy_text(self) -> None:
        if not self._tweet_text:
            return
        try:
            _copy_text(self._tweet_text)
            self._status.set("✓ テキストをコピーしました")
        except Exception as e:
            self._status.set(f"コピー失敗: {e}")

    def _do_copy_image(self) -> None:
        if not self._info or not self._info.artwork:
            return
        try:
            _copy_image(self._info.artwork)
            self._status.set("✓ 画像をコピーしました")
        except Exception as e:
            self._status.set(f"コピー失敗: {e}")

    # --- 自動更新 ---

    def _schedule_refresh(self) -> None:
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self) -> None:
        try:
            info = get_media_info()
        except Exception:
            info = None
        self._root.after(0, lambda: self._apply(info))

    def _apply(self, info: Optional[MediaInfo]) -> None:
        if info != self._info:
            self._info = info
            self._uploaded_url = None  # 曲が変わったらキャッシュをリセット
            self._render(info)
        self._root.after(self._REFRESH_MS, self._schedule_refresh)

    def _render(self, info: Optional[MediaInfo]) -> None:
        if info is None:
            self._tweet_text = ""
            self._set_text("再生中の曲が見つかりません")
            self._art_label.config(image="")
            self._art_label.image = None
            self._set_buttons("disabled", "disabled", "disabled")
            self._status.set("")
            return

        self._tweet_text = _format_tweet(info)
        self._set_text(self._tweet_text)

        if info.artwork:
            try:
                from PIL import Image, ImageTk
                img = Image.open(BytesIO(info.artwork))
                img.thumbnail((120, 120), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._art_label.config(image=photo)
                self._art_label.image = photo
            except Exception:
                self._art_label.config(image="")
        else:
            self._art_label.config(image="")

        img_state = "normal" if info.artwork else "disabled"
        self._set_buttons("normal", "normal", img_state)
        self._status.set("")

    def _set_text(self, text: str) -> None:
        self._txt.config(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.insert("1.0", text)
        self._txt.config(state="disabled")

    def _set_buttons(self, browser: str, text: str, image: str) -> None:
        self._btn_browser.config(state=browser)
        self._btn_text.config(state=text)
        self._btn_image.config(state=image)


def run_gui() -> None:
    NowPlayingApp()
