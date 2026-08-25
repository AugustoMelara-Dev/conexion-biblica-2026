import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, it, vi } from "vitest"

type FetchEvent = {
  request: { method: string; mode: string; url: string }
  respondWith(response: Promise<MockResponse>): void
}

class MockResponse {
  readonly body: string
  readonly ok: boolean

  constructor(body: string, ok = true) {
    this.body = body
    this.ok = ok
  }

  clone() {
    return new MockResponse(this.body, this.ok)
  }
}

function loadServiceWorker(options: {
  cached?: MockResponse
  network?: MockResponse
}) {
  const listeners = new Map<string, (event: FetchEvent) => void>()
  const put = vi.fn(async () => undefined)
  const match = vi.fn(async () => options.cached)
  const fetchFromNetwork = vi.fn(async () => {
    if (!options.network) throw new Error("offline")
    return options.network
  })
  const serviceWorkerSource = readFileSync(
    join(process.cwd(), "public", "sw.js"),
    "utf8",
  )

  const serviceWorkerScope = {
    location: { origin: "https://conexion.test" },
    addEventListener(
      eventName: string,
      listener: (event: FetchEvent) => void,
    ) {
      listeners.set(eventName, listener)
    },
    skipWaiting: vi.fn(),
    clients: { claim: vi.fn() },
  }
  const cachesApi = {
    match,
    open: vi.fn(async () => ({ addAll: vi.fn(), put })),
    keys: vi.fn(async () => []),
    delete: vi.fn(async () => true),
  }

  new Function("self", "caches", "fetch", "URL", serviceWorkerSource)(
    serviceWorkerScope,
    cachesApi,
    fetchFromNetwork,
    URL,
  )

  return {
    async request(pathname: string) {
      let responsePromise: Promise<MockResponse> | undefined
      listeners.get("fetch")?.({
        request: {
          method: "GET",
          mode: "cors",
          url: `https://conexion.test${pathname}`,
        },
        respondWith(response) {
          responsePromise = response
        },
      })
      if (!responsePromise) throw new Error("El service worker no respondió")
      return responsePromise
    },
    fetchFromNetwork,
    put,
  }
}

describe("actualización del contenido offline", () => {
  it("consulta la red antes del caché para el manifiesto de bancos", async () => {
    const worker = loadServiceWorker({
      cached: new MockResponse("manifest-viejo"),
      network: new MockResponse("manifest-nuevo"),
    })

    const response = await worker.request("/banks/manifest.json")

    expect(response.body).toBe("manifest-nuevo")
    expect(worker.fetchFromNetwork).toHaveBeenCalledOnce()
    expect(worker.put).toHaveBeenCalledOnce()
  })

  it("consulta la red antes del caché para cada banco empaquetado", async () => {
    const worker = loadServiceWorker({
      cached: new MockResponse("banco-viejo"),
      network: new MockResponse("banco-nuevo"),
    })

    const response = await worker.request("/banks/v4_daniel.json")

    expect(response.body).toBe("banco-nuevo")
    expect(worker.fetchFromNetwork).toHaveBeenCalledOnce()
    expect(worker.put).toHaveBeenCalledOnce()
  })

  it("conserva el banco en caché si el servidor responde con error", async () => {
    const worker = loadServiceWorker({
      cached: new MockResponse("banco-disponible"),
      network: new MockResponse("error-temporal", false),
    })

    const response = await worker.request("/banks/v4_daniel.json")

    expect(response.body).toBe("banco-disponible")
    expect(worker.put).not.toHaveBeenCalled()
  })

  it("recarga una sola vez cuando una versión nueva toma el control", () => {
    const mainSource = readFileSync(join(process.cwd(), "src", "main.tsx"), "utf8")

    expect(mainSource).toContain('register("/sw.js", { updateViaCache: "none" })')
    expect(mainSource).toContain('addEventListener("controllerchange"')
    expect(mainSource).toContain("window.location.reload()")
  })
})
