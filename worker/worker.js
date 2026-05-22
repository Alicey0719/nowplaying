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

    // 人間のアクセスは画像に直接リダイレクト
    if (!isCrawler(ua)) {
      return Response.redirect(imgUrl, 302)
    }

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content=" ">
  <meta name="twitter:image" content="${imgUrl}">
  <meta property="og:type" content="website">
  <meta property="og:title" content=" ">
  <meta property="og:url" content="${url.toString()}">
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
