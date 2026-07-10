import type { Page } from "@playwright/test"

const API_BASE = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8000"

export async function seedConfirmedUser(page: Page, userId: string) {
  const profile = await page.request.post(`${API_BASE}/api/chat/profile`, {
    data: {
      user_id: userId,
      chat_text: "具备基础，希望通过代码案例强化 ROS2 节点通信。",
    },
  })
  if (!profile.ok()) throw new Error(`profile seed failed: ${profile.status()}`)

  const confirmation = await page.request.post(`${API_BASE}/api/profile/confirm`, {
    data: { user_id: userId },
  })
  if (!confirmation.ok()) {
    throw new Error(`profile confirmation failed: ${confirmation.status()}`)
  }

  await page.addInitScript((id) => {
    window.localStorage.setItem("zhixue_user_id", id)
  }, userId)
}
