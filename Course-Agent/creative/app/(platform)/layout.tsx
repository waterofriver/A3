import { ReactNode } from "react"

import { AppShell } from "@/components/app-shell/app-shell"
import { SessionGuard } from "@/components/app-shell/session-guard"

export default function PlatformLayout({ children }: { children: ReactNode }) {
  return (
    <SessionGuard>
      <AppShell>{children}</AppShell>
    </SessionGuard>
  )
}
