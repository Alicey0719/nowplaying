"""Windows の再生中メディア情報を取得する (WinRT API)"""
import asyncio
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MediaInfo:
    title: str
    artist: str
    album: str
    artwork: Optional[bytes] = field(default=None, compare=False)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MediaInfo):
            return False
        return (
            self.title == other.title
            and self.artist == other.artist
            and bool(self.artwork) == bool(other.artwork)
        )

    def __str__(self) -> str:
        if self.artist:
            return f"{self.title} - {self.artist}"
        return self.title


async def _fetch_media_info() -> Optional[MediaInfo]:
    try:
        from winrt.windows.media.control import (
            GlobalSystemMediaTransportControlsSessionManager as MediaManager,
            GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
        )
    except ImportError:
        raise RuntimeError(
            "winrt パッケージが見つかりません。\n"
            "Windows の Python で: pip install -r requirements.txt"
        )

    manager = await MediaManager.request_async()
    session = manager.get_current_session()

    if session is None:
        return None

    playback = session.get_playback_info()
    if playback is None or playback.playback_status != PlaybackStatus.PLAYING:
        return None

    try:
        props = await session.try_get_media_properties_async()
    except Exception:
        return None

    if not props or not props.title:
        return None

    artwork = None
    if props.thumbnail:
        try:
            from winrt.windows.storage.streams import DataReader
            stream = await props.thumbnail.open_read_async()
            size = stream.size
            if size > 0:
                reader = DataReader(stream)
                loaded = await reader.load_async(size)
                data = bytearray(loaded)
                for i in range(loaded):
                    data[i] = reader.read_byte()
                reader.detach_stream()
                artwork = bytes(data)
        except Exception:
            pass

    # Apple Music は artist フィールドに "artist — album - type" を詰めてくることがある
    artist = props.artist or ""
    if " — " in artist:
        artist = artist.split(" — ")[0].strip()

    return MediaInfo(
        title=props.title,
        artist=artist,
        album=props.album_title or "",
        artwork=artwork,
    )


def get_media_info() -> Optional[MediaInfo]:
    """現在再生中のメディア情報を返す。再生中でない場合は None。"""
    return asyncio.run(_fetch_media_info())
