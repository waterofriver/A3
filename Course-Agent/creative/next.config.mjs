import path from "node:path"
import { fileURLToPath } from "node:url"

const projectRoot = path.dirname(fileURLToPath(import.meta.url))

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Keeps an explicit production build from competing with an active dev server.
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
  output: process.env.NEXT_OUTPUT_MODE === "standalone" ? "standalone" : undefined,
  images: {
    unoptimized: true,
  },
  outputFileTracingRoot: projectRoot,
}

export default nextConfig
