"""アートワーク画像のアップロード処理"""
import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Optional

import config

CATBOX_WRAPPER_BASE = "https://nowplayimg.alicey.dev/catbox_ximg"
LITTERBOX_WRAPPER_BASE = "https://nowplayimg.alicey.dev/litter_ximg"


def upload_image(data: bytes, service: Optional[str] = None) -> Optional[str]:
    """指定サービスに画像をアップロードし URL を返す。無効時は None。

    service を省略した場合は config.IMAGE_UPLOAD_SERVICE を使う。
    """
    if service is None:
        service = config.IMAGE_UPLOAD_SERVICE
    if not service:
        return None
    if service == "imgur":
        return _imgur(data)
    if service == "catbox":
        return _catbox(data)
    if service == "litterbox":
        return _litterbox(data)
    raise ValueError(f"未対応のサービス: {service}")


def _imgur(data: bytes) -> str:
    client_id = config.IMGUR_CLIENT_ID
    if not client_id:
        raise ValueError("config.py の IMGUR_CLIENT_ID を設定してください")

    payload = urllib.parse.urlencode({
        "image": base64.b64encode(data).decode(),
        "type": "base64",
    }).encode()
    req = urllib.request.Request(
        "https://api.imgur.com/3/image",
        data=payload,
        headers={"Authorization": f"Client-ID {client_id}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    return result["data"]["link"]


def _multipart_body(fields: dict, file_bytes: bytes, boundary: str) -> bytes:
    """テキストフィールド + 画像ファイルの multipart/form-data ボディを組み立てる。"""
    parts = b""
    for name, value in fields.items():
        parts += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()
    parts += (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="fileToUpload"; filename="artwork.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
    return parts


def _post_upload(endpoint: str, fields: dict, data: bytes, wrapper_base: str) -> str:
    """catbox 系エンドポイントへ 1 回アップロードし、wrapper URL を返す。失敗時は例外。"""
    boundary = "------------------------catboxboundary"
    body = _multipart_body(fields, data, boundary)
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            url = resp.read().decode().strip()
    except urllib.error.HTTPError as e:
        # catbox は理由を本文で返す（例: 412 "Uploads paused until I can resolve storage issues."）
        detail = ""
        try:
            detail = e.read().decode(errors="replace").strip()
        except Exception:
            pass
        raise ValueError(f"アップロード失敗（{e.code}）: {detail or e.reason}")

    # 断続的に空応答（HTTP 200 だが本文なし）を返すことがある → 失敗として扱う
    if not url:
        raise ValueError("空の応答が返りました")
    if not url.startswith("https://"):
        raise ValueError(f"アップロード失敗: {url}")

    # 実体 URL (https://files.catbox.moe/xxx.jpg 等) → wrapper URL に変換
    filename = url.rsplit("/", 1)[-1]
    return f"{wrapper_base}/{filename}"


def _with_retry(once: Callable[[], str], attempts: int = 3) -> str:
    """断続的な失敗を吸収するため、最大 attempts 回リトライする。"""
    last: Optional[Exception] = None
    for i in range(attempts):
        try:
            return once()
        except Exception as e:  # timeout / 空応答 / 一時エラーは再試行
            last = e
            if i < attempts - 1:
                time.sleep(0.6)
    raise ValueError(f"アップロードに失敗しました（{attempts}回試行）: {last}")


def _catbox(data: bytes) -> str:
    return _with_retry(lambda: _post_upload(
        "https://catbox.moe/user/api.php",
        {"reqtype": "fileupload"},
        data,
        CATBOX_WRAPPER_BASE,
    ))


def _litterbox(data: bytes) -> str:
    return _with_retry(lambda: _post_upload(
        "https://litterbox.catbox.moe/resources/internals/api.php",
        {"reqtype": "fileupload", "time": config.LITTERBOX_TIME},
        data,
        LITTERBOX_WRAPPER_BASE,
    ))
