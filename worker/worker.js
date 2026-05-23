const MIME = {
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  gif: "image/gif",
  webp: "image/webp",
}

// Twitter / OGP クローラーの UA
const CRAWLERS = ["Twitterbot", "facebookexternalhit", "Slackbot", "Discordbot", "LinkedInBot"]

function isCrawler(ua) {
  return CRAWLERS.some((bot) => ua.includes(bot))
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
    const ua = request.headers.get("User-Agent") ?? ""

    // ?raw=1 は Worker 経由で画像をプロキシ（Twitter の og:image フェッチ用）
    // catbox.moe が Twitter のクローラーをブロックする場合の対策
    if (url.searchParams.get("raw") === "1") {
      const resp = await fetch(imgUrl)
      return new Response(resp.body, {
        headers: {
          "Content-Type": mime,
          "Cache-Control": "public, max-age=86400",
        },
      })
    }

    // 人間のアクセスは画像に直接リダイレクト
    if (!isCrawler(ua)) {
      return Response.redirect(imgUrl, 302)
    }

    // クローラーには Twitter Card HTML を返す
    // og:image / twitter:image は Worker プロキシ URL を指す
    const proxyImgUrl = `${url.origin}${url.pathname}?raw=1`

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content=" ">
  <meta name="twitter:image" content="${proxyImgUrl}">
  <meta property="og:type" content="website">
  <meta property="og:title" content=" ">
  <meta property="og:url" content="${url.origin}${url.pathname}">
  <meta property="og:image" content="${proxyImgUrl}">
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
