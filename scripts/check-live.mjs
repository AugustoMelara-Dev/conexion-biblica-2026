const base = "https://conexion-biblica-2026.vercel.app"
const [swResp, idxResp] = await Promise.all([
  fetch(`${base}/sw.js`, { signal: AbortSignal.timeout(20000) }),
  fetch(`${base}/`, { signal: AbortSignal.timeout(20000) }),
])
const sw = await swResp.text()
const m = sw.match(/CACHE_NAME\s*=\s*"([^"]+)"/)
console.log("sw cache:", m ? m[1] : "n/a")
console.log("x-vercel-id:", idxResp.headers.get("x-vercel-id"))
const html = await idxResp.text()
console.log("asset hashes:", (html.match(/index-[A-Za-z0-9_]+\.(js|css)/g) || []).join(", "))
