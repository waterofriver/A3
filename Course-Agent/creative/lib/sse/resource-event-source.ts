import { API_BASE_URL } from "@/lib/api/client"
import type { ResourceGatewayEvent } from "@/lib/api/resource-types"

export type ResourceConnectionState =
  | "connecting"
  | "open"
  | "error"
  | "closed"

const RESOURCE_EVENTS: ResourceGatewayEvent["event"][] = [
  "task.started",
  "agent.started",
  "task.progress",
  "content.delta",
  "media.ready",
  "resource.ready",
  "task.completed",
  "task.failed",
  "heartbeat",
]

export function subscribeToResourceTask(
  taskId: string,
  onEvent: (event: ResourceGatewayEvent) => void,
  onConnectionState: (state: ResourceConnectionState) => void,
  afterSeq = 0,
) {
  const query = afterSeq > 0 ? `?after_seq=${afterSeq}` : ""
  const eventSource = new EventSource(
    `${API_BASE_URL}/api/resource/progress/${encodeURIComponent(taskId)}${query}`,
  )
  let closed = false

  onConnectionState("connecting")
  eventSource.onopen = () => onConnectionState("open")
  eventSource.onerror = () => {
    if (!closed) onConnectionState("error")
  }

  for (const eventName of RESOURCE_EVENTS) {
    eventSource.addEventListener(eventName, (message) => {
      try {
        const event = JSON.parse(message.data) as ResourceGatewayEvent
        onEvent(event)
        if (event.event === "task.completed" || event.event === "task.failed") {
          closed = true
          eventSource.close()
          onConnectionState("closed")
        }
      } catch {
        onConnectionState("error")
      }
    })
  }

  return () => {
    closed = true
    eventSource.close()
    onConnectionState("closed")
  }
}
