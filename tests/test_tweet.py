"""ツイートフォーマットのテスト"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from media import MediaInfo

# twitter モジュールは GUI 依存があるので関数だけ直接テスト
def _format_tweet(info, tmpl, tmpl_no_artist):
    try:
        if info.artist:
            return tmpl.format(title=info.title, artist=info.artist, album=info.album)
        return tmpl_no_artist.format(title=info.title, album=info.album)
    except (KeyError, ValueError):
        return f"{info.title} - {info.artist}"


TMPL       = "Now Playing: {title} - {artist} #nowplaying"
TMPL_NOART = "Now Playing: {title} #nowplaying"


class TestFormatTweet:
    def test_with_artist(self):
        info = MediaInfo("Song", "Artist", "Album")
        assert _format_tweet(info, TMPL, TMPL_NOART) == "Now Playing: Song - Artist #nowplaying"

    def test_without_artist(self):
        info = MediaInfo("Song", "", "Album")
        assert _format_tweet(info, TMPL, TMPL_NOART) == "Now Playing: Song #nowplaying"

    def test_album_placeholder(self):
        info = MediaInfo("Song", "Artist", "My Album")
        tmpl = "{title} ({album}) - {artist}"
        assert _format_tweet(info, tmpl, TMPL_NOART) == "Song (My Album) - Artist"

    def test_invalid_template_fallback(self):
        """不正なテンプレートはフォールバックすること"""
        info = MediaInfo("Song", "Artist", "Album")
        bad_tmpl = "{title} - {unknown_key}"
        result = _format_tweet(info, bad_tmpl, TMPL_NOART)
        assert "Song" in result
        assert "Artist" in result

    def test_special_chars(self):
        """特殊文字がそのまま含まれること"""
        info = MediaInfo("曲 & 'テスト'", "アーティスト", "アルバム")
        result = _format_tweet(info, TMPL, TMPL_NOART)
        assert "曲 & 'テスト'" in result
        assert "アーティスト" in result

    def test_empty_album(self):
        info = MediaInfo("Song", "Artist", "")
        result = _format_tweet(info, "{title} {album} {artist}", TMPL_NOART)
        assert result == "Song  Artist"
