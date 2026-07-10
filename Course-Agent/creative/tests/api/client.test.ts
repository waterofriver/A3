import { afterEach, describe, expect, it, vi } from "vitest"

import { ApiError, apiFetch } from "@/lib/api/client"

afterEach(() => vi.unstubAllGlobals())

describe("apiFetch", () => {
  it("returns data from a successful envelope", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ data: { status: "ok" }, trace_id: "trace-1" }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
      ),
    )

    await expect(apiFetch<{ status: string }>("/health")).resolves.toEqual({
      status: "ok",
    })
  })

  it("maps the gateway error envelope", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "TASK_NOT_FOUND",
              message: "任务不存在或已被清理。",
              retryable: false,
              details: null,
            },
            trace_id: "trace-1",
          }),
          { status: 404, headers: { "content-type": "application/json" } },
        ),
      ),
    )

    await expect(apiFetch("/api/task/missing")).rejects.toEqual(
      new ApiError(
        "TASK_NOT_FOUND",
        "任务不存在或已被清理。",
        false,
        "trace-1",
      ),
    )
  })

  it("maps a fetch failure to a retryable network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")))

    await expect(apiFetch("/api/user/info")).rejects.toMatchObject({
      code: "NETWORK_UNAVAILABLE",
      retryable: true,
    })
  })
})
