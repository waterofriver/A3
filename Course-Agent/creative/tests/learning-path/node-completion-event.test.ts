import { describe, expect, it } from "vitest"

import { pathNodeEventType } from "@/lib/api/learning-events"

describe("pathNodeEventType", () => {
  it("uses the reset event when a completed node is toggled off", () => {
    expect(pathNodeEventType(false)).toBe("path_node_reset")
  })

  it("uses the completed event when an incomplete node is toggled on", () => {
    expect(pathNodeEventType(true)).toBe("path_node_completed")
  })
})
