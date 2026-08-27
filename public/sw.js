const CACHE_NAME = "conexion-biblica-shell-v9"
const SHELL = [
  "/",
  "/index.html",
  "/manifest.webmanifest",
  "/banks/final-2026/manifest.json",
]

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)))
  self.skipWaiting()
})

self.addEventListener("activate", (event) => {
  event.waitUntil(Promise.all([
    self.clients.claim(),
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key.startsWith("conexion-biblica-shell-") && key !== CACHE_NAME).map((key) => caches.delete(key)))),
  ]))
})

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return
  const requestUrl = new URL(event.request.url)
  if (requestUrl.pathname === "/sw.js") return
  if (event.request.mode === "navigate" || requestUrl.pathname === "/index.html") {
    event.respondWith(
      fetch(event.request).then((response) => {
        if (response.ok) {
          const copy = response.clone()
          void caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy))
        }
        return response
      }).catch(() => caches.match(event.request).then((cached) => cached ?? caches.match("/index.html"))),
    )
    return
  }
  if (requestUrl.pathname.startsWith("/banks/")) {
    event.respondWith(
      fetch(event.request).then(async (response) => {
        if (!response.ok) return (await caches.match(event.request)) ?? response
        const copy = response.clone()
        void caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy))
        return response
      }).catch(async (loadError) => {
        const cached = await caches.match(event.request)
        if (cached) return cached
        throw loadError
      }),
    )
    return
  }
  event.respondWith(
    caches.match(event.request).then((cached) => cached ?? fetch(event.request).then((response) => {
      if (response.ok && new URL(event.request.url).origin === self.location.origin) {
        const copy = response.clone()
        void caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy))
      }
      return response
    }).catch(() => caches.match("/index.html"))),
  )
})
