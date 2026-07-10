import { createParser } from "eventsource-parser"

import { API_BASE_URL, ApiError } from "@/lib/api/client"
import type { components } from "@/lib/api/generated"
import type { GatewayEvent } from "@/lib/sse/task-reducer"

type ErrorEnvelope = components["schemas"]["ErrorResponse"]

export async function postEventStream(
  path: string,
  body: unknown,
  onEvent: (event: GatewayEvent) => void,
  signal?: AbortSignal,
): Promise<string | null> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        accept: "text/event-stream",
        "content-type": "application/json",
      },
      body: JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if (signal?.aborted) throw error
    throw new ApiError(
      "NETWORK_UNAVAILABLE",
      "无法连接学习服务，请检查网络后重试。",
      true,
    )
  }

  if (!response.ok) {
    const envelope = (await response.json()) as ErrorEnvelope
    throw new ApiError(
      envelope.error.code,
      envelope.error.message,
      envelope.error.retryable,
      envelope.trace_id,
    )
  }
  if (!response.body) {
    throw new ApiError(
      "NETWORK_UNAVAILABLE",
      "学习服务未返回可读取的流。",
      true,
      response.headers.get("x-trace-id") ?? undefined,
    )
  }

  const parser = createParser({
    maxBufferSize: 1_000_000,
    onEvent: (message) => onEvent(JSON.parse(message.data) as GatewayEvent),
    onError: (error) => {
      throw error
    },
  })
  const decoder = new TextDecoder()
  const reader = response.body.getReader()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    parser.feed(decoder.decode(value, { stream: true }))
  }
  parser.feed(decoder.decode())

  return response.headers.get("x-task-id")
}
