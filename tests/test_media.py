"""MediaInfo の等値比較ロジックのテスト"""
import pytest
from media import MediaInfo

ART_A = b"\xff\xd8\xff" + b"\x00" * 100  # ダミーJPEGヘッダ
ART_B = b"\xff\xd8\xff" + b"\x01" * 100  # 別の画像


class TestMediaInfoEquality:
    def test_same_title_artist_no_artwork(self):
        a = MediaInfo("Title", "Artist", "Album")
        b = MediaInfo("Title", "Artist", "Album 2")  # albumは比較に含まれない
        assert a == b

    def test_different_title(self):
        a = MediaInfo("Song A", "Artist", "Album", artwork=ART_A)
        b = MediaInfo("Song B", "Artist", "Album", artwork=ART_A)
        assert a != b

    def test_different_artist(self):
        a = MediaInfo("Title", "Artist A", "Album")
        b = MediaInfo("Title", "Artist B", "Album")
        assert a != b

    def test_artwork_present_to_none(self):
        """アートワークあり→なし は別物と判定されること（アートワーク残留バグの再発防止）"""
        a = MediaInfo("Title", "Artist", "Album", artwork=ART_A)
        b = MediaInfo("Title", "Artist", "Album", artwork=None)
        assert a != b

    def test_artwork_none_to_present(self):
        """アートワークなし→あり も別物と判定されること"""
        a = MediaInfo("Title", "Artist", "Album", artwork=None)
        b = MediaInfo("Title", "Artist", "Album", artwork=ART_A)
        assert a != b

    def test_artwork_both_present(self):
        """アートワークの中身が違っても両方ありなら同じ曲と判定（同アルバム別トラック）"""
        a = MediaInfo("Title", "Artist", "Album", artwork=ART_A)
        b = MediaInfo("Title", "Artist", "Album", artwork=ART_B)
        assert a == b

    def test_artwork_both_none(self):
        a = MediaInfo("Title", "Artist", "Album", artwork=None)
        b = MediaInfo("Title", "Artist", "Album", artwork=None)
        assert a == b

    def test_not_equal_to_none(self):
        a = MediaInfo("Title", "Artist", "Album")
        assert a != None  # noqa: E711

    def test_not_equal_to_other_type(self):
        a = MediaInfo("Title", "Artist", "Album")
        assert a != "Title"
