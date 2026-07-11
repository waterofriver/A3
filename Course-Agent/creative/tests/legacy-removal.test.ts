import fs from "node:fs"
import path from "node:path"
import { describe, expect, it } from "vitest"

const projectRoot = path.resolve(__dirname, "..")
const repositoryRoot = path.resolve(projectRoot, "../..")

function readTypeScriptTree(target: string) {
  if (!fs.existsSync(target)) return ""
  if (fs.statSync(target).isFile()) return fs.readFileSync(target, "utf8")
  return fs
    .readdirSync(target, { recursive: true })
    .filter((name) => /\.(ts|tsx)$/.test(String(name)))
    .map((name) => fs.readFileSync(path.join(target, String(name)), "utf8"))
    .join("\n")
}

describe("legacy integrations", () => {
  it("contains no active Coze or forum implementation", () => {
    const source = ["app", "components"]
      .map((entry) => readTypeScriptTree(path.join(projectRoot, entry)))
      .join("\n")

    expect(source).not.toMatch(/Coze|coze|论坛|\/api\/blogs/)
  })

  it("removes the legacy Django project", () => {
    expect(fs.existsSync(path.join(repositoryRoot, "mywebsite"))).toBe(false)
  })

  it("removes the Coze-only root package manifest", () => {
    expect(fs.existsSync(path.join(repositoryRoot, "package.json"))).toBe(false)
    expect(fs.existsSync(path.join(repositoryRoot, "pnpm-lock.yaml"))).toBe(false)
  })
})
