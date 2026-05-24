const MIME = {
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  gif: "image/gif",
  webp: "image/webp",
}

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
}

export default {
  async fetch(request) {
    const url = new URL(request.url)

    const match = url.pathname.match(/^\/catbox_ximg\/([a-zA-Z0-9]+\.(jpe?g|png|gif|webp))$/i)
    if (!match) {
      return new Response("Not Found", { status: 404 })
    }

    const file = match[1]
    const ext = match[2].replace("jpeg", "jpg").toLowerCase()
    const imgUrl = `https://files.catbox.moe/${file}`
    const mime = MIME[ext] ?? "image/jpeg"

    const title = url.searchParams.get("title") ?? ""
    const artist = url.searchParams.get("artist") ?? ""

    // title があれば LINE MUSIC 検索へ、なければ画像へ（後方互換）
    let humanRedirect = imgUrl
    let pageTitle = "Now Playing"
    let pageDesc = ""
    if (title) {
      const q = artist ? `${title} ${artist}` : title
      pageTitle = artist ? `${title} — ${artist}` : title
      pageDesc = "LINE MUSICで聴く"
      humanRedirect = `https://music.line.me/webapp/search?query=${encodeURIComponent(q)}`
    }

    // 全リクエストに HTML を返す
    // ブラウザは <script> で即リダイレクト（meta refresh と違い X のプレビューが追いかけない）
    // クローラー/X カード validator は JS を実行しないので card タグだけ読む
    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="${esc(pageTitle)}">
  <meta name="twitter:description" content="${esc(pageDesc)}">
  <meta name="twitter:image" content="${imgUrl}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="${esc(pageTitle)}">
  <meta property="og:description" content="${esc(pageDesc)}">
  <meta property="og:url" content="${url.origin}${url.pathname}">
  <meta property="og:image" content="${imgUrl}">
  <meta property="og:image:type" content="${mime}">
</head>
<body>
<script>window.location.replace("${humanRedirect}")</script>
</body>
</html>`

    return new Response(html, {
      headers: {
        "Content-Type": "text/html;charset=utf-8",
        "Cache-Control": "public, max-age=3600",
      },
    })
  },
}
