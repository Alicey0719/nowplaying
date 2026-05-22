"""設定の読み書き（settings.json に永続化）"""
import json
from pathlib import Path

import config

_FILE = Path(__file__).parent / "settings.json"

DEFAULTS: dict = {
    "tweet_template": config.TWEET_TEMPLATE,
    "tweet_template_no_artist": config.TWEET_TEMPLATE_NO_ARTIST,
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
