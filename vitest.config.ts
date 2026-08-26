import path from "node:path"
import { configDefaults, defineConfig } from "vitest/config"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  test: {
    exclude: [...configDefaults.exclude, "e2e/**", ".worktrees/**"],
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
    pool: "threads",
    poolOptions: {
      threads: { singleThread: true },
    },
  },
})
