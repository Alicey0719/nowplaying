"""設定の読み書きテスト"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def tmp_settings(tmp_path, monkeypatch):
    """settings モジュールの _FILE を一時ファイルに差し替える"""
    import settings
    fake = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "_FILE", fake)
    return fake


class TestSettings:
    def test_load_returns_defaults_when_no_file(self, tmp_settings):
        import settings
        data = settings.load()
        assert "tweet_template" in data
        assert "tweet_template_no_artist" in data
        assert "browser_path" in data
        assert data["browser_path"] == ""

    def test_save_and_load_roundtrip(self, tmp_settings):
        import settings
        payload = {
            "tweet_template": "♪ {title} by {artist}",
            "tweet_template_no_artist": "♪ {title}",
            "browser_path": r"C:\Program Files\Chrome\chrome.exe",
        }
        settings.save(payload)
        loaded = settings.load()
        assert loaded["tweet_template"] == payload["tweet_template"]
        assert loaded["tweet_template_no_artist"] == payload["tweet_template_no_artist"]
        assert loaded["browser_path"] == payload["browser_path"]

    def test_load_merges_with_defaults(self, tmp_settings):
        """ファイルに一部のキーしかなくてもデフォルト値で補完されること"""
        import settings
        tmp_settings.write_text(
            json.dumps({"tweet_template": "custom {title}"}), encoding="utf-8"
        )
        data = settings.load()
        assert data["tweet_template"] == "custom {title}"
        assert data["tweet_template_no_artist"] == settings.DEFAULTS["tweet_template_no_artist"]
        assert data["browser_path"] == ""

    def test_load_falls_back_on_corrupt_json(self, tmp_settings):
        """壊れた JSON はデフォルトにフォールバックすること"""
        import settings
        tmp_settings.write_text("{ invalid json }", encoding="utf-8")
        data = settings.load()
        assert data == settings.DEFAULTS

    def test_save_is_valid_json(self, tmp_settings):
        import settings
        settings.save({"tweet_template": "test", "tweet_template_no_artist": "t", "browser_path": ""})
        parsed = json.loads(tmp_settings.read_text(encoding="utf-8"))
        assert parsed["tweet_template"] == "test"

    def test_save_preserves_unicode(self, tmp_settings):
        import settings
        settings.save({"tweet_template": "🎵 {title} 🎶", "tweet_template_no_artist": "", "browser_path": ""})
        raw = tmp_settings.read_text(encoding="utf-8")
        assert "🎵" in raw  # ensure_ascii=False が効いていること
