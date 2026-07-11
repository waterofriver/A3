const DEMO_MODE_EVENT = "zhixue:demo-mode"
const DEMO_MODE_SESSION_KEY = "zhixue_demo_mode_seen"

export function announceDemoMode() {
  if (typeof window === "undefined") return
  window.sessionStorage.setItem(DEMO_MODE_SESSION_KEY, "true")
  window.dispatchEvent(new CustomEvent(DEMO_MODE_EVENT))
}

export function wasDemoModeAnnounced() {
  return (
    typeof window !== "undefined" &&
    window.sessionStorage.getItem(DEMO_MODE_SESSION_KEY) === "true"
  )
}

export function subscribeToDemoMode(listener: () => void) {
  window.addEventListener(DEMO_MODE_EVENT, listener)
  return () => window.removeEventListener(DEMO_MODE_EVENT, listener)
}
