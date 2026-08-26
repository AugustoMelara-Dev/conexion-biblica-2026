import { spawnSync } from "node:child_process"
import process from "node:process"

export function resolvePdftoppm(env = process.env) {
  if (env.PDFTOPPM_PATH) return env.PDFTOPPM_PATH
  const locator = process.platform === "win32" ? "where.exe" : "which"
  const located = spawnSync(locator, ["pdftoppm"], { encoding: "utf8" })
  const first = located.status === 0
    ? located.stdout.split(/\r?\n/).map((value) => value.trim()).find(Boolean)
    : undefined
  return first ?? (process.platform === "win32" ? "pdftoppm.exe" : "pdftoppm")
}
