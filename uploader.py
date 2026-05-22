"""アートワーク画像のアップロード処理"""
import base64
import json
import urllib.parse
import urllib.request
from typing import Optional

import config

CATBOX_WRAPPER_BASE = "https://hogehoge.alicey.dev/catbox_ximg"


def upload_image(data: bytes) -> Optional[str]:
    """設定されたサービスに画像をアップロードし URL を返す。無効時は None。"""
    service = config.IMAGE_UPLOAD_SERVICE
    if not service:
        return None
    if service == "imgur":
        return _imgur(data)
    if service == "catbox":
        return _catbox(data)
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


def _catbox(data: bytes) -> str:
    boundary = "------------------------catboxboundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="reqtype"\r\n\r\n'
        f"fileupload\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="fileToUpload"; filename="artwork.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        "https://catbox.moe/user/api.php",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        url = resp.read().decode().strip()
    if not url.startswith("https://"):
        raise ValueError(f"アップロード失敗: {url}")

    # catbox URL (https://files.catbox.moe/xxx.jpg) → wrapper URL に変換
    filename = url.rsplit("/", 1)[-1]
    return f"{CATBOX_WRAPPER_BASE}/{filename}"
