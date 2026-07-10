import type { components } from "@/lib/api/generated"

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "")

type ErrorEnvelope = components["schemas"]["ErrorResponse"]
type DataEnvelope<T> = { data: T; trace_id: string }

export class ApiError extends Error {
  readonly name = "ApiError"

  constructor(
    readonly code: string,
    message: string,
    readonly retryable: boolean,
    readonly traceId?: string,
  ) {
    super(message)
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body && !headers.has("content-type")) {
    headers.set("content-type", "application/json")
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(
      "NETWORK_UNAVAILABLE",
      "无法连接学习服务，请检查网络后重试。",
      true,
    )
  }

  const body = (await response.json()) as DataEnvelope<T> | ErrorEnvelope
  if (!response.ok) {
    const envelope = body as ErrorEnvelope
    throw new ApiError(
      envelope.error.code,
      envelope.error.message,
      envelope.error.retryable,
      envelope.trace_id,
    )
  }
  return (body as DataEnvelope<T>).data
}

export { API_BASE_URL }
