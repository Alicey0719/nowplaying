const MIME = {
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  gif: "image/gif",
  webp: "image/webp",
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

    // 全リクエストに HTML を返す
    // 人間は meta refresh で catbox に即リダイレクト
    // クローラーは redirect を無視して card タグを読む
    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0;url=${imgUrl}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content=" ">
  <meta name="twitter:image" content="${imgUrl}">
  <meta property="og:type" content="website">
  <meta property="og:title" content=" ">
  <meta property="og:url" content="${url.origin}${url.pathname}">
  <meta property="og:image" content="${imgUrl}">
  <meta property="og:image:type" content="${mime}">
</head>
<body></body>
</html>`

    return new Response(html, {
      headers: {
        "Content-Type": "text/html;charset=utf-8",
        "Cache-Control": "public, max-age=3600",
      },
    })
  },
}
