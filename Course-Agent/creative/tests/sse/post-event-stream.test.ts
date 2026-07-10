import { afterEach, describe, expect, it, vi } from "vitest"

import { ApiError } from "@/lib/api/client"
import { postEventStream } from "@/lib/sse/post-event-stream"
import type { GatewayEvent } from "@/lib/sse/task-reducer"

afterEach(() => vi.unstubAllGlobals())

describe("postEventStream", () => {
  it("parses an SSE event split across byte chunks", async () => {
    const gatewayEvent: GatewayEvent = {
      event: "content.delta",
      task_id: "task-1",
      seq: 1,
      trace_id: "trace-1",
      progress: 30,
      content: "流式内容",
      finish_flag: false,
      resource_ids: [],
      demo_mode: true,
    }
    const payload = `id: 1\nevent: content.delta\ndata: ${JSON.stringify(gatewayEvent)}\n\n`
    const bytes = new TextEncoder().encode(payload)
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(bytes.slice(0, 17))
        controller.enqueue(bytes.slice(17))
        controller.close()
      },
    })
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(body, {
          status: 200,
          headers: {
            "content-type": "text/event-stream",
            "x-task-id": "task-1",
          },
        }),
      ),
    )
    const received: GatewayEvent[] = []

    const taskId = await postEventStream(
      "/api/chat/profile",
      { user_id: "student-001", chat_text: "测试" },
      (parsed) => received.push(parsed),
    )

    expect(taskId).toBe("task-1")
    expect(received).toEqual([gatewayEvent])
  })

  it("maps a non-success response to ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "CONTENT_BLOCKED",
              message: "输入内容未通过安全检查。",
              retryable: false,
              details: null,
            },
            trace_id: "trace-2",
          }),
          { status: 400, headers: { "content-type": "application/json" } },
        ),
      ),
    )

    await expect(
      postEventStream("/api/chat/profile", {}, vi.fn()),
    ).rejects.toEqual(
      new ApiError(
        "CONTENT_BLOCKED",
        "输入内容未通过安全检查。",
        false,
        "trace-2",
      ),
    )
  })
})
