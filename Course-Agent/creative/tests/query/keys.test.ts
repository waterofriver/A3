import { describe, expect, it } from "vitest"

import { queryKeys } from "@/lib/query/keys"

describe("queryKeys", () => {
  it("keeps user and course identity in cache keys", () => {
    expect(queryKeys.user("student-001")).toEqual(["user", "student-001"])
    expect(queryKeys.resources("student-001", "操作系统")).toEqual([
      "resources",
      "student-001",
      "操作系统",
    ])
  })
})
