from pathlib import Path

# ツイート文言テンプレート
# 使えるプレースホルダー: {title}, {artist}, {album}
TWEET_TEMPLATE = "Now Playing: {title} - {artist} #nowplaying"

# アーティストが空の場合のテンプレート
TWEET_TEMPLATE_NO_ARTIST = "Now Playing: {title} #nowplaying"

# GUI の自動更新間隔（秒）
WATCH_INTERVAL_SECONDS = 5

# -------------------------------------------------------------------
# 画像アップロード（Twitter Card 用）
# None        : アップロードしない
# "catbox"    : catbox.moe を使用（永続・登録不要）
# "litterbox" : litterbox.catbox.moe を使用（一時保存・登録不要。catbox 停止時の代替）
# "imgur"     : Imgur を使用（IMGUR_CLIENT_ID が必要）
IMAGE_UPLOAD_SERVICE: str | None = "catbox"

# litterbox の保存期間: "1h" / "12h" / "24h" / "72h"
# （Twitter は投稿時に画像をキャッシュするため、一時保存でもカードは残る）
LITTERBOX_TIME = "72h"

# Imgur 使用時のみ必要
IMGUR_CLIENT_ID = ""
# -------------------------------------------------------------------
