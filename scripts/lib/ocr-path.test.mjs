import assert from "node:assert/strict"
import test from "node:test"

test("resuelve pdftoppm desde variable explícita o PATH de Windows", async () => {
  const modulePath = new URL("./ocr-path.mjs", import.meta.url)
  const helper = await import(modulePath).catch(() => null)
  assert.ok(helper, "falta ocr-path.mjs")
  if (!helper) return

  assert.equal(
    helper.resolvePdftoppm({ PDFTOPPM_PATH: "C:/tools/pdftoppm.exe" }),
    "C:/tools/pdftoppm.exe"
  )
  assert.match(helper.resolvePdftoppm({}), /pdftoppm(?:\.exe)?$/i)
})
