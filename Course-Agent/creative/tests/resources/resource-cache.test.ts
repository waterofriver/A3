import { describe, expect, it } from "vitest"

import {
  applyResourceEvent,
  clearActiveResourceTask,
  createResourceTaskState,
  emptyResourceTask,
  readActiveResourceTask,
  rememberActiveResourceTask,
} from "@/lib/query/resource-cache"
import type { ResourceGatewayEvent } from "@/lib/api/resource-types"

function event(
  overrides: Partial<ResourceGatewayEvent>,
): ResourceGatewayEvent {
  return {
    event: "content.delta",
    task_id: "task-1",
    seq: 1,
    trace_id: "trace-1",
    progress: 20,
    content: "",
    finish_flag: false,
    resource_ids: [],
    demo_mode: true,
    ...overrides,
  }
}

describe("applyResourceEvent", () => {
  it("buffers content independently by resource type", () => {
    const handout = applyResourceEvent(
      emptyResourceTask,
      event({ seq: 1, resource_type: "handout", content: "A" }),
    )
    const quiz = applyResourceEvent(
      handout,
      event({ seq: 2, resource_type: "quiz", content: "B" }),
    )

    expect(quiz.byType.handout.content).toBe("A")
    expect(quiz.byType.quiz.content).toBe("B")
  })

  it("ignores duplicate sequence numbers", () => {
    const first = applyResourceEvent(
      emptyResourceTask,
      event({ seq: 3, resource_type: "code", content: "first" }),
    )
    const duplicate = applyResourceEvent(
      first,
      event({ seq: 3, resource_type: "code", content: "duplicate" }),
    )

    expect(duplicate).toBe(first)
    expect(duplicate.byType.code.content).toBe("first")
  })

  it("keeps completed resources when a later resource type fails", () => {
    const completed = applyResourceEvent(
      createResourceTaskState("task-1"),
      event({
        event: "resource.ready",
        resource_type: "handout",
        resource_ids: ["handout-1"],
        progress: 55,
      }),
    )
    const partial = applyResourceEvent(
      completed,
      event({
        event: "task.failed",
        seq: 2,
        resource_type: "quiz",
        progress: 55,
        error: {
          code: "UPSTREAM_TIMEOUT",
          message: "题库生成超时",
          retryable: true,
        },
      }),
    )

    expect(partial.status).toBe("partial_success")
    expect(partial.byType.handout.status).toBe("succeeded")
    expect(partial.byType.handout.resourceIds).toEqual(["handout-1"])
    expect(partial.byType.quiz.status).toBe("failed")
  })

  it("stores only the active task pointer for refresh recovery", () => {
    localStorage.clear()
    rememberActiveResourceTask("student-1", "机器人操作系统", "task-9")

    expect(readActiveResourceTask("student-1", "机器人操作系统")).toBe(
      "task-9",
    )
    expect(createResourceTaskState("task-9").taskId).toBe("task-9")

    clearActiveResourceTask("student-1", "机器人操作系统")
    expect(readActiveResourceTask("student-1", "机器人操作系统")).toBeNull()
  })
})
