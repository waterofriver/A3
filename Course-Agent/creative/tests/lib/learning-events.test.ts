import { beforeEach, describe, expect, it, vi } from "vitest"

import { apiFetch } from "@/lib/api/client"
import {
  flushLearningEvents,
  queueLearningEvent,
} from "@/lib/api/learning-events"

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>(
    "@/lib/api/client",
  )
  return { ...actual, apiFetch: vi.fn() }
})

describe("learning event queue", () => {
  beforeEach(() => vi.mocked(apiFetch).mockReset())

  it("flushes queued events through the normal JSON API", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ accepted: 1 })
    queueLearningEvent("student-1", "机器人操作系统", {
      event_type: "resource_opened",
      resource_id: "res-1",
      metadata: {},
    })

    await flushLearningEvents("student-1", "机器人操作系统")

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/learning/events",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          user_id: "student-1",
          course_name: "机器人操作系统",
          events: [
            {
              event_type: "resource_opened",
              resource_id: "res-1",
              metadata: {},
            },
          ],
        }),
      }),
    )
  })
})
