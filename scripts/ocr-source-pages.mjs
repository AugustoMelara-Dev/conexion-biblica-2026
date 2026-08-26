import { createHash } from "node:crypto"
import { spawnSync } from "node:child_process"
import { mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"
import { createScheduler, createWorker } from "tesseract.js"
import { resolvePdftoppm } from "./lib/ocr-path.mjs"

const root = process.cwd()
const pdfPath = path.join(root, "MaterialConexionBiblica (1).pdf")
const cacheDir = path.join(root, "scripts", "source-cache", "final-v7")
const imageDir = path.join(root, "output", "final-v7", "ocr-images")
const modelCacheDir = path.join(root, "output", "final-v7", "tesseract-cache")
const outputPath = path.join(cacheDir, "ocr-pages.json")
const pdftoppm = resolvePdftoppm()

await mkdir(cacheDir, { recursive: true })
await mkdir(modelCacheDir, { recursive: true })
await rm(imageDir, { recursive: true, force: true })
await mkdir(imageDir, { recursive: true })

const render = spawnSync(
  pdftoppm,
  ["-f", "3", "-l", "59", "-r", "220", "-png", pdfPath, path.join(imageDir, "page")],
  { encoding: "utf8" }
)
if (render.status !== 0) {
  throw new Error(`pdftoppm falló: ${render.stderr || render.stdout}`)
}

const fileNames = (await readdir(imageDir))
  .filter((name) => /^page-\d+\.png$/.test(name))
  .filter((name) => Number(name.match(/\d+/)?.[0]) !== 26)
  .sort((left, right) => Number(left.match(/\d+/)?.[0]) - Number(right.match(/\d+/)?.[0]))

const scheduler = createScheduler()
for (let index = 0; index < 4; index += 1) {
  scheduler.addWorker(await createWorker("spa", 1, { cachePath: modelCacheDir }))
}

let completed = 0
const jobs = fileNames.map(async (fileName) => {
  const page = Number(fileName.match(/\d+/)?.[0])
  const result = await scheduler.addJob("recognize", path.join(imageDir, fileName))
  completed += 1
  process.stderr.write(`OCR ${completed}/${fileNames.length}\r`)
  return [String(page), result.data.text.replace(/\r\n/g, "\n").trim()]
})
const entries = await Promise.all(jobs)
await scheduler.terminate()
process.stderr.write("\n")

const pdfBytes = await readFile(pdfPath)
const payload = {
  schema_version: "1.0",
  source_file: path.basename(pdfPath),
  source_sha256: createHash("sha256").update(pdfBytes).digest("hex"),
  extraction: { engine: "tesseract.js", version: "7.0.0", language: "spa", dpi: 220 },
  pages: Object.fromEntries(entries),
}
await writeFile(outputPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8")
await rm(imageDir, { recursive: true, force: true })
console.log(outputPath)
