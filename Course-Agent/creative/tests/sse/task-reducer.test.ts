import { describe, expect, it } from "vitest"

import {
  type GatewayEvent,
  initialTaskState,
  reduceTaskEvent,
} from "@/lib/sse/task-reducer"

const event = (overrides: Partial<GatewayEvent> = {}): GatewayEvent => ({
  event: "content.delta",
  task_id: "task-1",
  seq: 1,
  trace_id: "trace-1",
  progress: 20,
  content: "第一段",
  finish_flag: false,
  resource_ids: [],
  demo_mode: true,
  ...overrides,
})

describe("reduceTaskEvent", () => {
  it("ignores duplicate or older events", () => {
    const first = reduceTaskEvent(initialTaskState, event({ seq: 2 }))
    const duplicate = reduceTaskEvent(
      first,
      event({ seq: 2, content: "重复内容" }),
    )

    expect(duplicate.content).toBe("第一段")
    expect(duplicate.lastSeq).toBe(2)
  })

  it("merges incremental profile patches", () => {
    const foundation = reduceTaskEvent(
      initialTaskState,
      event({
        event: "profile.patch",
        profile_patch: { knowledge_foundation: "入门基础" },
      }),
    )
    const preference = reduceTaskEvent(
      foundation,
      event({
        event: "profile.patch",
        seq: 2,
        profile_patch: { content_preferences: ["代码案例"] },
      }),
    )

    expect(preference.profile).toEqual({
      knowledge_foundation: "入门基础",
      content_preferences: ["代码案例"],
    })
  })

  it("keeps a terminal state when a later heartbeat arrives", () => {
    const completed = reduceTaskEvent(
      initialTaskState,
      event({ event: "task.completed", seq: 5, progress: 100 }),
    )
    const heartbeat = reduceTaskEvent(
      completed,
      event({ event: "heartbeat", seq: 6, progress: 100, content: "" }),
    )

    expect(heartbeat.status).toBe("succeeded")
    expect(heartbeat.lastSeq).toBe(6)
  })
})
