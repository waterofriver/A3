import { expect, test } from "@playwright/test"

test("new user completes profile collection", async ({ page }) => {
  const userId = `e2e-profile-${Date.now()}`

  await page.goto("/login")
  await page.getByLabel("用户 ID").fill(userId)
  await page.getByRole("button", { name: "进入学习平台" }).click()

  await expect(page).toHaveURL(/\/profile$/, { timeout: 30_000 })
  await page
    .getByPlaceholder("介绍你的专业、基础或学习目标")
    .fill("我想加强 ROS2 节点通信，喜欢代码案例。")
  await page.getByRole("button", { name: "发送" }).click()

  await expect(page.getByText("画像抽取Agent")).toBeVisible()
  await expect(page.getByText("ROS2 节点通信", { exact: false })).toBeVisible()
  await page.getByRole("button", { name: "画像确认完成" }).click()

  await expect(page).toHaveURL(/\/workspace$/)
})
