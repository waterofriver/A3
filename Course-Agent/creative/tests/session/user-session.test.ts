import { beforeEach, describe, expect, it } from "vitest"

import { clearUserId, getUserId, setUserId } from "@/lib/session/user-session"

describe("user session", () => {
  beforeEach(() => localStorage.clear())

  it("stores a trimmed user id", () => {
    setUserId("  student-001  ")
    expect(getUserId()).toBe("student-001")
  })

  it("clears the user id", () => {
    setUserId("student-001")
    clearUserId()
    expect(getUserId()).toBeNull()
  })

  it("rejects an empty user id", () => {
    expect(() => setUserId("   ")).toThrow("user_id is required")
  })
})
