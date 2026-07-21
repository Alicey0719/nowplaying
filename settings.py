"""設定の読み書き（settings.json に永続化）"""
import json
import os
import sys
from pathlib import Path

import config


def _settings_file() -> Path:
    if getattr(sys, "frozen", False):
        # パッケージ版: %APPDATA%\NowPlaying\settings.json
        d = Path(os.environ.get("APPDATA", Path.home())) / "NowPlaying"
        d.mkdir(exist_ok=True)
        return d / "settings.json"
    return Path(__file__).parent / "settings.json"


_FILE = _settings_file()

DEFAULTS: dict = {
    "tweet_template": config.TWEET_TEMPLATE,
    "tweet_template_no_artist": config.TWEET_TEMPLATE_NO_ARTIST,
    "browser_path": "",
    # 画像アップロード先: "catbox" / "litterbox" / None（config.py の既定値を初期値に）
    "upload_service": config.IMAGE_UPLOAD_SERVICE,
}


def load() -> dict:
    if _FILE.exists():
        try:
            data = json.loads(_FILE.read_text(encoding="utf-8"))
            return {**DEFAULTS, **data}
        except Exception:
            pass
    return dict(DEFAULTS)


def save(data: dict) -> None:
    _FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
